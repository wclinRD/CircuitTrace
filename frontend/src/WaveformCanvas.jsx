import React, { useRef, useEffect, useState, useCallback } from 'react';
import GetSignalsDialog from './GetSignalsDialog';

// Port 由 Python 動態決定，避免衝突
const DEFAULT_SURFER_PORT = 17392;

const WaveformCanvas = ({ vcdPath, isActive }) => {
  const iframeRef = useRef(null);
  const surferPortRef = useRef(DEFAULT_SURFER_PORT); // 用 ref 避免 closure stale 問題
  const [hierarchyData, setHierarchyData] = useState(null);
  const [addedSignals, setAddedSignals] = useState([]);
  const [showGetSignals, setShowGetSignals] = useState(false);
  const [surferReady, setSurferReady] = useState(false);
  const [surferPort, setSurferPort] = useState(DEFAULT_SURFER_PORT);
  const [surferUrl, setSurferUrl] = useState(null);

  const waitForPyWebview = () => new Promise(resolve => {
    if (window.pywebview) { resolve(); return; }
    // Polling fallback: pywebviewready 可能在 listener 挂上前就已觸發
    const poll = setInterval(() => {
      if (window.pywebview) {
        clearInterval(poll);
        resolve();
      }
    }, 50);
    window.addEventListener('pywebviewready', () => {
      clearInterval(poll);
      resolve();
    }, { once: true });
    // 5 秒超時保護，防止永遠沒有 pywebview 的情況
    setTimeout(() => { clearInterval(poll); resolve(); }, 5000);
  });

  // 初始化：優先從 URL query param 讀取 surfer_port（pop-out 視窗用），
  // 如果沒有再向 Python 詢問
  useEffect(() => {
    let cancelled = false;
    const initPort = async () => {
      // 先嘗試從 URL query string 取得 port（pop-out 視窗會帶這個 param）
      const urlParams = new URLSearchParams(window.location.search);
      const portFromUrl = parseInt(urlParams.get('surfer_port') || '0', 10);
      if (portFromUrl > 0) {
        surferPortRef.current = portFromUrl;
        setSurferPort(portFromUrl);
        setSurferUrl(`http://127.0.0.1:${portFromUrl}/index.html`);
        return; // 不需要再問 Python
      }

      // 主視窗：向 Python API 詢問實際使用的 port
      try {
        await waitForPyWebview();
        const result = await window.pywebview.api.read_surfer_wasm();
        if (!cancelled && result && result.port) {
          const port = result.port;
          surferPortRef.current = port;
          setSurferPort(port);
          setSurferUrl(`http://127.0.0.1:${port}/index.html`);
        }
      } catch (e) {
        // Fallback：pywebview 不存在（瀏覽器開發模式）
        if (!cancelled) {
          setSurferUrl(`http://127.0.0.1:${DEFAULT_SURFER_PORT}/index.html`);
        }
      }
    };
    initPort();
    return () => { cancelled = true; };
  }, []);

  // 送訊息給 Surfer iframe（用 * 作為 targetOrigin，因為 sandbox 限制）
  const sendToSurfer = useCallback((msg) => {
    if (iframeRef.current && iframeRef.current.contentWindow) {
      // 用 '*' 確保能穿透 sandbox，integration.js 在 iframe 內部接收
      iframeRef.current.contentWindow.postMessage(msg, '*');
    }
  }, []);

  const loadVcd = useCallback((path) => {
    if (!path) return;
    const port = surferPortRef.current;
    const vcdUrl = `http://127.0.0.1:${port}/api/vcd?path=${encodeURIComponent(path)}`;
    sendToSurfer({ command: 'LoadUrl', url: vcdUrl });
  }, [sendToSurfer]);

  const loadHierarchy = useCallback(async () => {
    if (!vcdPath) return;
    try {
      await waitForPyWebview();
      let res = await window.pywebview.api.load_waveform(vcdPath);
      if (res.success) {
        res = await window.pywebview.api.get_waveform_hierarchy();
      }
      if (res.success) setHierarchyData(res.hierarchy);
    } catch (err) {
      console.error('Failed to load waveform hierarchy', err);
    }
  }, [vcdPath]);

  // Surfer iframe 載入完成時的處理
  const handleIframeLoad = useCallback(() => {
    setSurferReady(true);
    if (vcdPath) {
      // 稍等讓 Surfer egui 完成初始化再送 LoadUrl
      setTimeout(() => loadVcd(vcdPath), 1000);
    }
    loadHierarchy();
  }, [vcdPath, loadVcd, loadHierarchy]);

  // ────────────────────────────────────────────────
  // 波形 → 程式碼方向：監聽 Surfer iframe 的 SignalClicked 訊息
  // integration.js 的 surfer_notify_host 呼叫 window.parent.postMessage(data, "*")
  // ────────────────────────────────────────────────
  useEffect(() => {
    const handleMessage = (e) => {
      // 接受來自 Surfer iframe 的訊息（127.0.0.1:PORT）
      const port = surferPortRef.current;
      const expectedOrigin = `http://127.0.0.1:${port}`;
      // 若 origin 不是我們的 surfer server，忽略（防止其他訊息干擾）
      if (e.origin !== expectedOrigin) return;

      const data = e.data;
      if (!data || typeof data !== 'object') return;

      if (data.command === 'SignalClicked') {
        // 取最後一段 (去掉 scope 前綴)
        const signalName = (data.signal || '').split('.').pop();
        localStorage.setItem('waveform_trace_request', JSON.stringify({
          signal: signalName,
          full: data.signal,
          timestamp: Date.now()
        }));
        window.dispatchEvent(new Event('waveform_trace_request_updated'));
      }
    };
    window.addEventListener('message', handleMessage);
    return () => window.removeEventListener('message', handleMessage);
  }, []); // 不依賴 surferPort state，改用 ref 避免 re-register

  // 當 vcdPath 改變時重新載入
  useEffect(() => {
    if (surferReady && vcdPath) {
      loadVcd(vcdPath);
      loadHierarchy();
    }
  }, [vcdPath, surferReady, loadVcd, loadHierarchy]);

  // ────────────────────────────────────────────────
  // 程式碼 → 波形方向：監聽 waveform_signals_sync 事件 (Ctrl+W 觸發)
  // vars 格式必須是字串陣列，integration.js 會轉成 { name: v }
  // ────────────────────────────────────────────────
  useEffect(() => {
    const handleSyncEvent = (e) => {
      if (!e.detail || !Array.isArray(e.detail)) return;
      // 確保 vars 是字串陣列（可能傳進來的是物件）
      const signals = e.detail.map(s => typeof s === 'string' ? s : (s.name || s.signal || String(s)));
      setAddedSignals(signals);
      localStorage.setItem('waveform_signals', JSON.stringify(signals));
      if (surferReady) {
        sendToSurfer({ command: 'AddVariables', vars: signals });
      }
    };

    const syncFromStorage = () => {
      try {
        const stored = localStorage.getItem('waveform_signals');
        if (stored) {
          const signals = JSON.parse(stored);
          setAddedSignals(signals);
          if (surferReady) sendToSurfer({ command: 'AddVariables', vars: signals });
        }
      } catch (e) {}
    };

    window.addEventListener('waveform_signals_sync', handleSyncEvent);
    window.addEventListener('storage', syncFromStorage);
    return () => {
      window.removeEventListener('waveform_signals_sync', handleSyncEvent);
      window.removeEventListener('storage', syncFromStorage);
    };
  }, [surferReady, sendToSurfer]);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', flex: 1, minHeight: 0, width: '100%', overflow: 'hidden', background: '#1e1e1e' }}>
      <div style={{ display: 'flex', background: '#252526', padding: '4px', gap: '8px', alignItems: 'center', flexShrink: 0 }}>
        <button
          onClick={() => setShowGetSignals(true)}
          style={{ padding: '2px 8px', background: '#007acc', color: 'white', border: 'none', cursor: 'pointer', borderRadius: '3px' }}
        >
          + Get Signals
        </button>
        <span style={{ color: '#ccc', marginLeft: 'auto', fontSize: '12px' }}>
          Powered by Surfer Wasm Engine
        </span>
      </div>

      <div style={{ flex: 1, position: 'relative', minHeight: 0 }}>
        {!surferUrl && (
          <div style={{ color: '#aaa', textAlign: 'center', paddingTop: '40px', fontSize: '14px' }}>
            正在啟動 Surfer 波形引擎...
          </div>
        )}
        {surferUrl && (
          <iframe
            ref={iframeRef}
            src={surferUrl}
            onLoad={handleIframeLoad}
            style={{
              position: 'absolute',
              top: 0,
              left: 0,
              width: '100%',
              height: '100%',
              border: 'none',
              display: 'block',
            }}
            title="Surfer Waveform Viewer"
            // 移除 sandbox 限制，讓 postMessage 和 script 正常運作
            // allow-same-origin 已經允許，allow-scripts 是必要的
            // 若移除 sandbox 整個 iframe 就沒有限制，更相容
          />
        )}
      </div>

      <GetSignalsDialog
        isOpen={showGetSignals}
        onClose={() => setShowGetSignals(false)}
        hierarchyData={hierarchyData}
        onAddSignals={(newSignals) => {
          // newSignals 是字串陣列
          const merged = Array.from(new Set([...addedSignals, ...newSignals]));
          setAddedSignals(merged);
          localStorage.setItem('waveform_added_signals', JSON.stringify(merged));
          window.dispatchEvent(new Event('storage'));
          if (surferReady) {
            sendToSurfer({ command: 'AddVariables', vars: newSignals });
          }
        }}
      />
    </div>
  );
};

export default WaveformCanvas;
