import React, { useState, useEffect, useRef } from 'react';
import Editor from '@monaco-editor/react';
import { ChevronRight, ChevronDown, Cpu, Activity, LayoutList, FileCode, ArrowLeft, ArrowRight, Terminal, ListTree, Search, X, Waves } from 'lucide-react';
import WaveformCanvas from './WaveformCanvas';
import './App.css';

function App() {
  const urlParams = new URLSearchParams(window.location.search);
  const isStandaloneWaveform = urlParams.get('page') === 'waveform';
  const standaloneVcdPath = urlParams.get('vcd') || '';

  const [hierarchy, setHierarchy] = useState([]);
  const [sources, setSources] = useState({});
  const [currentFile, setCurrentFile] = useState('');
  const [openFiles, setOpenFiles] = useState([]);
  const [messages, setMessages] = useState([]);
  const [contextMenu, setContextMenu] = useState(null);
  const [traceContextMenu, setTraceContextMenu] = useState(null);
  const [selectedWord, setSelectedWord] = useState('');
  
  const editorRef = useRef(null);
  
  const [projectFile, setProjectFile] = useState('');

  const [activeBottomTab, setActiveBottomTab] = useState('trace');
  const [compileLogs, setCompileLogs] = useState('');
  const [simulationLogs, setSimulationLogs] = useState('');
  const [isSimulating, setIsSimulating] = useState(false);
  const [vcdFile, setVcdFile] = useState('');
  const [traceResults, setTraceResults] = useState([]);
  const [historyStack, setHistoryStack] = useState([]);
  const [historyIndex, setHistoryIndex] = useState(-1);

  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);

  const [leftWidth, setLeftWidth] = useState(250);
  const [bottomHeight, setBottomHeight] = useState(200);
  const isResizingX = useRef(false);
  const isResizingY = useRef(false);

  // 移除自動載入寫死的 project.f，改由按鈕觸發
  useEffect(() => {
    addMessage('system', 'Ready. Please load a .f file to start.');

    const handleMouseMove = (e) => {
      if (isResizingX.current) {
        let newWidth = e.clientX;
        if (newWidth < 150) newWidth = 150;
        if (newWidth > 600) newWidth = 600;
        setLeftWidth(newWidth);
      }
      if (isResizingY.current) {
        let newHeight = window.innerHeight - e.clientY;
        if (newHeight < 100) newHeight = 100;
        if (newHeight > window.innerHeight - 100) newHeight = window.innerHeight - 100;
        setBottomHeight(newHeight);
      }
    };

    const handleMouseUp = () => {
      isResizingX.current = false;
      isResizingY.current = false;
      document.body.style.cursor = 'default';
    };

    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);
    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, []);

  useEffect(() => {
    const handleTraceRequest = () => {
       if (isStandaloneWaveform || !projectFile) return;
       try {
         const reqStr = localStorage.getItem('waveform_trace_request');
         if (reqStr) {
            const req = JSON.parse(reqStr);
            // Verify timestamp isn't old, or clear it. 
            // Clearing it prevents multiple triggers, but localStorage is shared.
            if (req.signal) {
               traceSignal('drive', req.full || req.signal);
               // Open trace tab automatically
               setActiveBottomTab('trace');
            }
         }
       } catch (e) {}
    };
    window.addEventListener('storage', handleTraceRequest);
    window.addEventListener('waveform_trace_request_updated', handleTraceRequest);
    return () => {
      window.removeEventListener('storage', handleTraceRequest);
      window.removeEventListener('waveform_trace_request_updated', handleTraceRequest);
    };
  }, [isStandaloneWaveform, projectFile, traceResults]);

  const loadProject = async (filePath) => {
    addMessage('info', `Loading project from ${filePath}...`);
    setProjectFile(filePath);
    try {
      let res;
      if (window.pywebview && window.pywebview.api) {
        res = await window.pywebview.api.parse_project(filePath);
      } else {
        throw new Error("Native API not available.");
      }
      
      if (res.status === 'success' || res.success === true) {
        setHierarchy(res.hierarchy || []);
        setSources(res.sources || {});
        setCompileLogs(res.compile_logs || '');
        const firstFile = res.sources ? Object.keys(res.sources)[0] : null;
        if (firstFile) {
          setCurrentFile(firstFile);
          setOpenFiles([firstFile]);
        }
        addMessage('success', `Loaded ${filePath} successfully.`);
      } else {
        setCompileLogs(res.compile_logs || res.message || 'Unknown error');
        setActiveBottomTab('compile');
        addMessage('error', 'Failed to load project, check Compile logs.');
      }
    } catch (err) {
      addMessage('error', 'Failed to load project: ' + err.message);
    }
  };

  const handleOpenFile = async () => {
    if (window.pywebview && window.pywebview.api) {
      const filePath = await window.pywebview.api.open_file_dialog();
      if (filePath) {
        loadProject(filePath);
      }
    } else {
      // 網頁版回退 (Fallback) 讓使用者輸入路徑
      const filePath = prompt("請輸入 .f 檔案的絕對路徑：", "/Users/wclin/antigravity/verdi/backend/tests/fixtures/large_project/project.f");
      if (filePath) {
        loadProject(filePath);
      }
    }
  };

  const jumpToFileLine = (file, line, saveHistory = true) => {
    if (saveHistory) {
      const newStack = historyStack.slice(0, historyIndex + 1);
      newStack.push({ file, line });
      setHistoryStack(newStack);
      setHistoryIndex(newStack.length - 1);
    }
    
    if (!openFiles.includes(file)) {
      setOpenFiles([...openFiles, file]);
    }
    setCurrentFile(file);
    setTimeout(() => {
      if (editorRef.current && line > 0) {
        editorRef.current.revealLineInCenter(line);
        editorRef.current.setPosition({ lineNumber: line, column: 1 });
        editorRef.current.focus();
      }
    }, 100);
  };

  const goBack = () => {
    if (historyIndex > 0) {
      const prev = historyStack[historyIndex - 1];
      setHistoryIndex(historyIndex - 1);
      jumpToFileLine(prev.file, prev.line, false);
    }
  };

  const goForward = () => {
    if (historyIndex < historyStack.length - 1) {
      const next = historyStack[historyIndex + 1];
      setHistoryIndex(historyIndex + 1);
      jumpToFileLine(next.file, next.line, false);
    }
  };

  const closeFile = (e, file) => {
    e.stopPropagation();
    const newOpenFiles = openFiles.filter(f => f !== file);
    setOpenFiles(newOpenFiles);
    if (currentFile === file) {
      setCurrentFile(newOpenFiles.length > 0 ? newOpenFiles[0] : '');
    }
  };

  const addMessage = (type, text) => {
    setMessages(prev => [...prev, { type, text, time: new Date().toLocaleTimeString() }]);
  };

  const handleEditorDidMount = (editor, monaco) => {
    editorRef.current = editor;
    
    // Bind Monaco Global Shortcuts for Tracing
    editor.addCommand(monaco.KeyMod.Alt | monaco.KeyMod.Shift | monaco.KeyCode.KeyD, () => {
      const position = editor.getPosition();
      const wordInfo = editor.getModel().getWordAtPosition(position);
      if (wordInfo) traceSignal('drive', wordInfo.word);
    });
    
    editor.addCommand(monaco.KeyMod.Alt | monaco.KeyMod.Shift | monaco.KeyCode.KeyL, () => {
      const position = editor.getPosition();
      const wordInfo = editor.getModel().getWordAtPosition(position);
      if (wordInfo) traceSignal('load', wordInfo.word);
    });

    editor.addCommand(monaco.KeyMod.Alt | monaco.KeyMod.Shift | monaco.KeyCode.KeyC, () => {
      const position = editor.getPosition();
      const wordInfo = editor.getModel().getWordAtPosition(position);
      if (wordInfo) traceSignal('connection', wordInfo.word);
    });

    const triggerWaveform = () => {
      const position = editor.getPosition();
      if (!position) return;
      const wordInfo = editor.getModel().getWordAtPosition(position);
      if (wordInfo) addToWaveform(wordInfo.word);
    };
    editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.KeyW, triggerWaveform);
    editor.addCommand(monaco.KeyMod.WinCtrl | monaco.KeyCode.KeyW, triggerWaveform);

    editor.onMouseUp((e) => {
      if (e.event.detail === 2) {
        const position = e.target.position;
        if (position) {
          const wordInfo = editor.getModel().getWordAtPosition(position);
          if (wordInfo) {
            setSelectedWord(wordInfo.word);
            traceSignal('drive', wordInfo.word);
            setContextMenu(null);
          }
        }
      }
    });

    editor.onContextMenu((e) => {
      e.event.preventDefault();
      const position = e.target.position;
      if (position) {
        const wordInfo = editor.getModel().getWordAtPosition(position);
        if (wordInfo) {
          setSelectedWord(wordInfo.word);
          setContextMenu({
            x: e.event.browserEvent.clientX,
            y: e.event.browserEvent.clientY,
            word: wordInfo.word,
          });
        } else {
          setContextMenu(null);
        }
      }
    });
  };

  const closeContextMenu = () => {
    setContextMenu(null);
    setTraceContextMenu(null);
  };

  const deleteTraceGroup = (id) => {
    setTraceResults(traceResults.filter(group => group.id !== id));
  };

  const deleteAllTraces = () => {
    setTraceResults([]);
  };

  const traceSignal = async (type, signalName) => {
    addMessage('info', `Tracing ${type} for signal: ${signalName}...`);
    try {
      let res;
      if (window.pywebview && window.pywebview.api) {
        res = await window.pywebview.api.trace(type, projectFile, 'top', signalName);
      } else {
        throw new Error("Native API not available.");
      }

      if (res.status !== 'success') {
        addMessage('error', `Trace failed: ${res.message}`);
        return;
      }

      const ports = res.ports || [];
      if (ports.length === 0) {
        addMessage('warning', `No ${type} ports found.`);
        return;
      }
      
      let msg = `[${type.toUpperCase()}] ${signalName} -> `;
      ports.forEach(p => {
        msg += `${p.file}:${p.line} (${p.module}.${p.port}), `;
      });
      addMessage('success', msg);
      
      // Update trace results table (Tree structure)
      const newGroup = {
        id: Date.now(),
        type: type.toUpperCase(),
        signal: signalName,
        expanded: true,
        children: ports
      };
      setTraceResults(prev => [newGroup, ...prev]);
      setActiveBottomTab('trace');

      const target = ports[0];
      if (target.file && target.line > 0) {
        jumpToFileLine(target.file, target.line);
      }
    } catch(err) {
      addMessage('error', `Trace failed: ${err.message}`);
    }
  };

  const addToWaveform = (signalName) => {
    try {
       const existingStr = localStorage.getItem('waveform_signals');
       let signals = existingStr ? JSON.parse(existingStr) : [];
       
       // Because verilog variables are often scoped (e.g. soc_top.u_cpu.clk),
       // and double-clicking only gives the leaf name (e.g. clk), we might need to qualify it.
       // For this MVP, let's just use the clicked word. If the user clicked "clk", 
       // the backend will search for matching signals.
       // Ideally we'd find its full path via trace results, but let's start simple.
       
       if (!signals.includes(signalName)) {
         signals.push(signalName);
         localStorage.setItem('waveform_signals', JSON.stringify(signals));
         // Trigger local event since storage event only fires on other windows natively
         window.dispatchEvent(new Event('waveform_signals_updated'));
         // IPC call to sync with popped-out windows
         if (window.pywebview && window.pywebview.api) {
           window.pywebview.api.sync_waveform_signals(JSON.stringify(signals));
         }
         addMessage('success', `Added ${signalName} to Waveform`);
       }
    } catch(err) {
      console.error(err);
    }
  };

  const closeProject = () => {
    setHierarchy([]);
    setSources({});
    setOpenFiles([]);
    setCurrentFile('');
    setTraceResults([]);
    setMessages([]);
    setCompileLogs('');
    setSimulationLogs('');
    setIsSimulating(false);
    setHistoryStack([]);
    setHistoryIndex(-1);
    setSearchQuery('');
    setSearchResults([]);
    addMessage('info', 'Project closed.');
  };

  const runSimulation = async () => {
    if (!projectFile) {
      addMessage('warning', 'No project loaded to simulate.');
      return;
    }
    setIsSimulating(true);
    setSimulationLogs('Starting simulation...');
    setActiveBottomTab('simulation');
    
    try {
      let res;
      if (window.pywebview && window.pywebview.api) {
        res = await window.pywebview.api.simulate_project(projectFile);
      } else {
        // Fallback for web interface
        const req = await fetch('http://localhost:8000/api/simulate', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ file_path: projectFile })
        });
        res = await req.json();
      }
      
      if (res.success) {
        addMessage('success', 'Simulation completed successfully.');
        // Auto-set VCD path assuming dump.vcd or wave.vcd might be generated
        if (projectFile) {
           const dir = projectFile.substring(0, projectFile.lastIndexOf('/'));
           setVcdFile(`${dir}/dump.vcd`); // Try default name
        }
      } else {
        addMessage('error', 'Simulation failed.');
      }
      setSimulationLogs(res.logs);
    } catch (err) {
      addMessage('error', 'Simulation error: ' + err.message);
      setSimulationLogs('Simulation error: ' + err.message);
    } finally {
      setIsSimulating(false);
    }
  };

  const TreeNode = ({ node }) => {
    const [expanded, setExpanded] = useState(true);
    const hasChildren = node.children && node.children.length > 0;
    
    return (
      <div className="tree-node">
        <div className="tree-label" onClick={() => {
            setExpanded(!expanded);
            
            // Cross-probing: find the module or instance in sources
            let targetFile = null;
            let targetLine = -1;
            
            for (const file of Object.keys(sources)) {
              const lines = sources[file].split('\n');
              for (let i = 0; i < lines.length; i++) {
                const line = lines[i];
                if (line.includes(`module ${node.module}`) || line.includes(`${node.module} `)) {
                   if (!targetFile) {
                     targetFile = file;
                     targetLine = i + 1;
                   }
                }
                // Try to find instance name
                if (node.name !== node.module && line.includes(node.name) && line.includes(node.module)) {
                   targetFile = file;
                   targetLine = i + 1;
                }
              }
            }

            if (targetFile) {
              jumpToFileLine(targetFile, targetLine);
            }
        }}>
          <span className="icon">
            {hasChildren ? (expanded ? <ChevronDown size={14}/> : <ChevronRight size={14}/>) : <span style={{width: 14}}/>}
          </span>
          <Cpu size={14} className="node-icon"/>
          <span>{node.name} <span className="module-type">({node.module})</span></span>
        </div>
        {expanded && hasChildren && (
          <div className="tree-children">
            {node.children.map((child, i) => <TreeNode key={i} node={child} />)}
          </div>
        )}
      </div>
    );
  };

  const TraceTreeGroup = ({ group }) => {
    const [expanded, setExpanded] = useState(group.expanded);
    return (
      <>
        <tr 
          className="trace-group-row" 
          onClick={() => setExpanded(!expanded)}
          onContextMenu={(e) => {
            e.preventDefault();
            setTraceContextMenu({
              x: e.clientX,
              y: e.clientY,
              groupId: group.id
            });
          }}
        >
          <td colSpan="3">
            <span className="icon" style={{marginRight: 8, display: 'inline-flex', alignItems: 'center', verticalAlign: 'middle'}}>
              {expanded ? <ChevronDown size={14}/> : <ChevronRight size={14}/>}
            </span>
            <span className={`badge ${group.type.toLowerCase()}`} style={{marginRight: 8}}>{group.type}</span> 
            <strong>{group.signal}</strong> <span style={{color: 'var(--text-muted)'}}>({group.children.length} items)</span>
          </td>
        </tr>
        {expanded && group.children.map((child, i) => {
          const basename = child.file.split('/').pop();
          return (
            <tr key={i} className="trace-child-row" onClick={() => jumpToFileLine(child.file, child.line)}>
              <td className="trace-child-name" style={{paddingLeft: 30}}>↳ {child.port}</td>
              <td>{basename} ({child.line})</td>
              <td>{child.module}</td>
            </tr>
          );
        })}
      </>
    );
  };

  if (isStandaloneWaveform) {
    return (
      <div style={{ width: '100vw', height: '100vh', display: 'flex', flexDirection: 'column', background: '#1e1e1e', overflow: 'hidden' }}>
        <WaveformCanvas vcdPath={standaloneVcdPath} isActive={true} />
      </div>
    );
  }

  return (
    <div className="app-container" onClick={closeContextMenu}>
      <header className="app-header">
        <div className="logo"><Activity size={18} /> CircuitTrace</div>
        <div style={{display: 'flex', gap: '8px'}}>
          <button onClick={handleOpenFile} className="btn-open">
            Open .f File
          </button>
          {hierarchy.length > 0 && (
            <button onClick={closeProject} className="btn-open" style={{backgroundColor: 'var(--msg-error)', color: 'white', borderColor: 'transparent'}}>
              Close Project
            </button>
          )}
        </div>
      </header>
      
      <div className="main-content">
        <div className="panel hierarchy-panel" style={{ width: leftWidth, flexShrink: 0 }}>
          <div className="panel-header"><LayoutList size={14} /> Module Hierarchy</div>
          <div className="panel-body hierarchy-tree">
            {hierarchy.map((node, i) => <TreeNode key={i} node={node} />)}
          </div>
        </div>
        
        <div 
          className="resizer-x" 
          onMouseDown={(e) => {
            e.preventDefault();
            isResizingX.current = true;
            document.body.style.cursor = 'col-resize';
          }} 
        />

        <div className="panel editor-panel">
          <div className="editor-tabs">
            {openFiles.map(file => {
              const basename = file.split('/').pop();
              return (
                <div 
                  key={file} 
                  className={`tab ${file === currentFile ? 'active' : ''}`}
                  onClick={() => setCurrentFile(file)}
                  title={file}
                >
                  <FileCode size={14}/> {basename}
                  <X size={12} className="tab-close" onClick={(e) => closeFile(e, file)}/>
                </div>
              );
            })}
          </div>
          <div className="editor-toolbar">
            <button className="toolbar-btn" onClick={goBack} disabled={historyIndex <= 0} title="Go Back">
              <ArrowLeft size={16} />
            </button>
            <button className="toolbar-btn" onClick={goForward} disabled={historyIndex >= historyStack.length - 1} title="Go Forward">
              <ArrowRight size={16} />
            </button>
            <div className="toolbar-path">{currentFile}</div>
          </div>
          <div style={{ flex: 1, position: 'relative' }}>
            <Editor
              height="100%"
              defaultLanguage="verilog"
              theme="vs-dark"
              value={sources[currentFile] || '// Select a file'}
              path={currentFile} // Helps Monaco maintain distinct models
              onMount={handleEditorDidMount}
              options={{ readOnly: true, minimap: { enabled: false }, fontSize: 14, contextmenu: false }}
            />
          </div>
        </div>
      </div>
      
      <div 
        className="resizer-y" 
        onMouseDown={(e) => {
          e.preventDefault();
          isResizingY.current = true;
          document.body.style.cursor = 'row-resize';
        }} 
      />

      <div className="panel message-panel" style={{ height: bottomHeight, flexShrink: 0 }}>
        <div className="bottom-tabs">
          <div className={`bottom-tab ${activeBottomTab === 'console' ? 'active' : ''}`} onClick={() => setActiveBottomTab('console')}>
            <Terminal size={14} /> General
          </div>
          <div className={`bottom-tab ${activeBottomTab === 'compile' ? 'active' : ''}`} onClick={() => setActiveBottomTab('compile')}>
            <FileCode size={14} /> Compile
          </div>
          <div className={`bottom-tab ${activeBottomTab === 'simulation' ? 'active' : ''}`} onClick={() => setActiveBottomTab('simulation')}>
            <Activity size={14} /> Simulation
          </div>
          <div className={`bottom-tab ${activeBottomTab === 'waveform' ? 'active' : ''}`} onClick={() => setActiveBottomTab('waveform')}>
            <Waves size={14} /> Waveform
          </div>
          <div className={`bottom-tab ${activeBottomTab === 'trace' ? 'active' : ''}`} onClick={() => setActiveBottomTab('trace')}>
            <ListTree size={14} /> Trace Results {traceResults.length > 0 && `(${traceResults.length})`}
          </div>
          <div className={`bottom-tab ${activeBottomTab === 'search' ? 'active' : ''}`} onClick={() => setActiveBottomTab('search')}>
            <Search size={14} /> Search {searchResults.length > 0 && `(${searchResults.length})`}
          </div>
        </div>
        
        <div className="panel-body">
          {activeBottomTab === 'search' && (
            <div className="search-panel" style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
              <form onSubmit={(e) => {
                e.preventDefault();
                if (!searchQuery) return;
                const results = [];
                Object.keys(sources).forEach(file => {
                  const lines = sources[file].split('\n');
                  lines.forEach((line, index) => {
                    if (line.includes(searchQuery)) {
                      results.push({ file, line: index + 1, content: line });
                    }
                  });
                });
                setSearchResults(results);
                addMessage('info', `Found ${results.length} results for "${searchQuery}"`);
              }} style={{ padding: '8px', display: 'flex', gap: '8px', borderBottom: '1px solid var(--border)', flexShrink: 0 }}>
                <input 
                  type="text" 
                  value={searchQuery} 
                  onChange={(e) => setSearchQuery(e.target.value)} 
                  placeholder="Search in files... (Press Enter)" 
                  style={{ flex: 1, padding: '4px 8px', background: 'rgba(0,0,0,0.2)', color: 'var(--text)', border: '1px solid var(--border)', borderRadius: '4px' }}
                />
                <button type="submit" className="btn-open" style={{ padding: '4px 12px' }}>Search</button>
              </form>
              <div className="search-results" style={{ overflowY: 'auto', flex: 1 }}>
                {searchResults.length === 0 ? (
                  <div className="empty-state">No search results.</div>
                ) : (
                  <table className="trace-table">
                    <thead>
                      <tr>
                        <th style={{ width: '200px' }}>File(Line)</th>
                        <th>Content</th>
                      </tr>
                    </thead>
                    <tbody>
                      {searchResults.map((res, i) => (
                        <tr key={i} onClick={() => jumpToFileLine(res.file, res.line)} style={{ cursor: 'pointer' }} className="trace-child-row">
                          <td style={{ color: 'var(--accent)' }}>{res.file} ({res.line})</td>
                          <td style={{ fontFamily: 'monospace', whiteSpace: 'pre' }}>{res.content.trim()}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>
            </div>
          )}

          {activeBottomTab === 'console' && (
            <div className="messages">
              {messages.map((m, i) => (
                <div key={i} className={`message ${m.type}`}>
                  <span className="time">[{m.time}]</span> {m.text}
                </div>
              ))}
            </div>
          )}

          {activeBottomTab === 'compile' && (
            <div className="compile-logs" style={{ padding: '8px', overflowY: 'auto', height: '100%', backgroundColor: '#1e1e1e', color: '#d4d4d4', fontFamily: 'monospace', whiteSpace: 'pre-wrap', fontSize: '12px', userSelect: 'text' }}>
              {compileLogs ? compileLogs : 'No compile logs available.'}
            </div>
          )}

          {activeBottomTab === 'simulation' && (
            <div className="simulation-panel" style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
              <div className="simulation-toolbar" style={{ padding: '8px', borderBottom: '1px solid var(--border)', display: 'flex', gap: '8px', alignItems: 'center' }}>
                <button onClick={runSimulation} disabled={!projectFile || isSimulating} className="btn-open" style={{ backgroundColor: isSimulating ? 'var(--bg-lighter)' : 'var(--accent)' }}>
                  {isSimulating ? 'Running...' : 'Run Simulation'}
                </button>
              </div>
              <div className="simulation-logs" style={{ flex: 1, padding: '8px', overflowY: 'auto', backgroundColor: '#1e1e1e', color: '#00ff00', fontFamily: 'monospace', whiteSpace: 'pre-wrap', fontSize: '12px', userSelect: 'text' }}>
                {simulationLogs ? simulationLogs : 'Click Run Simulation to start.'}
              </div>
            </div>
          )}

          <div 
            className="waveform-container" 
            style={{ 
              display: activeBottomTab === 'waveform' ? 'flex' : 'none', 
              flexDirection: 'column', 
              height: '100%' 
            }}
          >
            <div style={{ padding: '8px', borderBottom: '1px solid #3c3c3c', display: 'flex', gap: '8px' }}>
              <input 
                type="text" 
                value={vcdFile} 
                readOnly 
                placeholder="No VCD file loaded" 
                style={{ flex: 1, background: '#1e1e1e', color: '#d4d4d4', border: '1px solid #3c3c3c', padding: '4px 8px' }}
              />
              <button 
                onClick={() => {
                  const sigs = localStorage.getItem('waveform_signals') || '[]';
                  window.pywebview?.api?.open_waveform_window(vcdFile, sigs);
                }} 
                disabled={!vcdFile} 
                className="btn-open" 
                style={{ padding: '4px 12px' }}
              >
                Pop-out Window
              </button>
            </div>
            <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0 }}>
              <WaveformCanvas vcdPath={vcdFile} isActive={activeBottomTab === 'waveform'} />
            </div>
          </div>
          
          {activeBottomTab === 'trace' && (
            <div className="trace-table-container">
              {traceResults.length === 0 ? (
                <div className="empty-state">No trace results to display.</div>
              ) : (
                <table className="trace-table">
                  <thead>
                    <tr>
                      <th>Signals / Drivers / Loads</th>
                      <th>File(Line)</th>
                      <th>Scope</th>
                    </tr>
                  </thead>
                  <tbody>
                    {traceResults.map((group) => (
                      <TraceTreeGroup key={group.id} group={group} />
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          )}
        </div>
      </div>

      {contextMenu && (
        <div 
          className="context-menu"
          style={{ top: contextMenu.y, left: contextMenu.x }}
          onClick={(e) => e.stopPropagation()}
        >
          <div className="menu-header">Signal: {contextMenu.word}</div>
          <div className="menu-item" onClick={() => { traceSignal('drive', contextMenu.word); closeContextMenu(); }}>
            <Search size={14} style={{marginRight: 6, verticalAlign: 'middle'}}/> Driver (Alt+Shift+D)
          </div>
          <div className="menu-item" onClick={() => { traceSignal('load', contextMenu.word); closeContextMenu(); }}>
            <Search size={14} style={{marginRight: 6, verticalAlign: 'middle'}}/> Load (Alt+Shift+L)
          </div>
          <div className="menu-item" onClick={() => { traceSignal('connection', contextMenu.word); closeContextMenu(); }}>
            <Search size={14} style={{marginRight: 6, verticalAlign: 'middle'}}/> Connectivity (Alt+Shift+C)
          </div>
          <div className="menu-item" onClick={() => { addToWaveform(contextMenu.word); closeContextMenu(); }}>
            <Waves size={14} style={{marginRight: 6, verticalAlign: 'middle'}}/> Add to Waveform (Ctrl+W)
          </div>
        </div>
      )}

      {traceContextMenu && (
        <div className="context-menu" style={{ top: traceContextMenu.y, left: traceContextMenu.x }} onClick={e => e.stopPropagation()}>
          <div className="menu-item" onClick={() => { deleteAllTraces(); closeContextMenu(); }}>
            <span style={{color: 'var(--msg-error)'}}>Delete All</span>
          </div>
          <div className="menu-item" onClick={() => { deleteTraceGroup(traceContextMenu.groupId); closeContextMenu(); }}>
            <span style={{color: 'var(--msg-error)'}}>Delete Selected</span>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
