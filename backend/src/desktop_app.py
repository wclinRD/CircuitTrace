import sys
import os
import tempfile
import threading

# Fix macOS GUI app PATH issue (cannot find iverilog installed by Homebrew)
os.environ['PATH'] = os.environ.get('PATH', '') + ':/opt/homebrew/bin:/usr/local/bin'

# Fix PyVerilog needing write access to current directory for 'preprocess.output'
os.chdir(tempfile.gettempdir())

import webview
from hierarchy import build_hierarchy
from tracer import trace_drive, trace_load, trace_connection

SURFER_PREFERRED_PORT = 17392  # 偏好的固定 port（方便除錯）
_surfer_actual_port: int = 0   # 實際啟動後的 port（OS 自動分配時可能不同）

def _find_free_port(preferred: int) -> int:
    """嘗試使用偏好 port，若被占用則讓 OS 自動分配一個空閒 port。"""
    import socket
    # 先嘗試偏好的 port
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('127.0.0.1', preferred))
            return preferred
    except OSError:
        pass
    # 若失敗，讓 OS 自動選一個空閒 port
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]

def start_surfer_server(surfer_dir: str, preferred_port: int) -> int:
    """在背景執行緒啟動 Surfer 靜態檔案的 HTTP 伺服器，回傳實際使用的 port。"""
    import http.server
    import functools
    from urllib.parse import urlparse, parse_qs
    global _surfer_actual_port

    port = _find_free_port(preferred_port)

    class SurferRequestHandler(http.server.SimpleHTTPRequestHandler):
        """擴充 SimpleHTTPRequestHandler，新增 /api/vcd 端點供 Surfer 下載本地 VCD 檔案。"""

        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=surfer_dir, **kwargs)

        def do_GET(self):
            parsed = urlparse(self.path)
            if parsed.path == '/api/vcd':
                qs = parse_qs(parsed.query)
                vcd_path = qs.get('path', [None])[0]
                if vcd_path and os.path.exists(vcd_path):
                    try:
                        with open(vcd_path, 'rb') as f:
                            data = f.read()
                        self.send_response(200)
                        self.send_header('Content-Type', 'application/octet-stream')
                        self.send_header('Content-Length', str(len(data)))
                        self.send_header('Access-Control-Allow-Origin', '*')
                        self.end_headers()
                        self.wfile.write(data)
                    except Exception as e:
                        self.send_response(500)
                        self.end_headers()
                else:
                    self.send_response(404)
                    self.end_headers()
                return
            # 其他路徑交給 SimpleHTTPRequestHandler 處理靜態檔案
            super().do_GET()

        def log_message(self, format, *args):
            pass  # 靜音 access log，避免塞滿終端機

    class ReusableServer(http.server.HTTPServer):
        allow_reuse_address = True

    server = ReusableServer(('127.0.0.1', port), SurferRequestHandler)
    _surfer_actual_port = server.server_address[1]  # 取得實際綁定的 port
    server.serve_forever()
    return _surfer_actual_port

if getattr(sys, 'frozen', False):
    FRONTEND_DIST = os.path.join(sys._MEIPASS, "frontend-dist")
else:
    FRONTEND_DIST = os.path.join(os.path.dirname(__file__), "..", "..", "release", "frontend-dist")

class DesktopApi:
    def open_file_dialog(self):
        if webview.windows:
            window = webview.windows[0]
            result = window.create_file_dialog(webview.OPEN_DIALOG, allow_multiple=False)
            if result:
                return result[0]
        return None

    def parse_project(self, file_path):
        import io
        import sys
        from contextlib import redirect_stdout, redirect_stderr
        import traceback

        output_buffer = io.StringIO()
        try:
            with redirect_stdout(output_buffer), redirect_stderr(output_buffer):
                tree, sources = build_hierarchy(file_path)
            return {
                "status": "success", 
                "success": True,
                "hierarchy": tree, 
                "sources": sources,
                "compile_logs": output_buffer.getvalue()
            }
        except Exception as e:
            error_msg = f"Error parsing:\\n{traceback.format_exc()}"
            output_buffer.write("\\n" + error_msg)
            return {
                "status": "error", 
                "success": False,
                "hierarchy": [],
                "sources": {},
                "compile_logs": output_buffer.getvalue()
            }

    def simulate_project(self, file_path):
        import subprocess
        import tempfile
        from hierarchy import parse_filelist
        
        if not os.path.exists(file_path):
            return {"success": False, "logs": "File not found."}
            
        files_to_compile = []
        if file_path.endswith('.f'):
            files_to_compile = parse_filelist(file_path)
        else:
            files_to_compile = [file_path]
            
        temp_vvp = os.path.join(tempfile.gettempdir(), "sim_output.vvp")
        
        logs = ""
        cmd_iverilog = ["iverilog", "-o", temp_vvp] + files_to_compile
        try:
            res_iv = subprocess.run(cmd_iverilog, capture_output=True, text=True, cwd=os.path.dirname(file_path))
            logs += f"$ {' '.join(cmd_iverilog)}\\n"
            logs += res_iv.stdout + res_iv.stderr
            
            if res_iv.returncode != 0:
                return {"success": False, "logs": logs + f"\\niverilog failed with exit code {res_iv.returncode}."}
                
            cmd_vvp = ["vvp", temp_vvp]
            logs += f"\\n$ {' '.join(cmd_vvp)}\\n"
            res_vvp = subprocess.run(cmd_vvp, capture_output=True, text=True, cwd=os.path.dirname(file_path))
            logs += res_vvp.stdout + res_vvp.stderr
            
            return {"success": res_vvp.returncode == 0, "logs": logs}
            
        except Exception as e:
            import traceback
            logs += f"\\nException running simulation: {traceback.format_exc()}"
            return {"success": False, "logs": logs}

    def trace(self, type_, file_path, module_name, signal_name):
        try:
            if type_ == "drive":
                res = trace_drive(file_path, module_name, signal_name)
            elif type_ == "load":
                res = trace_load(file_path, module_name, signal_name)
            elif type_ == "connection":
                res = trace_connection(file_path, module_name, signal_name)
            else:
                return {"status": "error", "message": "Unknown trace type"}
            return {"status": "success", "ports": res}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def load_waveform(self, vcd_path):
        from waveform import WaveformParser
        try:
            parser = WaveformParser.get_instance()
            parser.load_vcd(vcd_path)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_waveform_hierarchy(self):
        from waveform import WaveformParser
        try:
            parser = WaveformParser.get_instance()
            tree = parser.get_hierarchy()
            meta = {}
            if parser.vcd_obj:
                meta['endtime'] = parser.vcd_obj.endtime
                meta['timescale'] = parser.vcd_obj.timescale
            return {"success": True, "hierarchy": tree, "meta": meta}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_waveform_data(self, signal_name, start_time, end_time):
        from waveform import WaveformParser
        try:
            parser = WaveformParser.get_instance()
            data = parser.get_signal_data(signal_name, start_time, end_time)
            return {"success": True, "data": data}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def open_waveform_window(self, vcd_path, signals_json="[]"):
        import urllib.parse
        html_path = os.path.join(FRONTEND_DIST, "index.html")
        encoded_signals = urllib.parse.quote(signals_json)
        # 將 surfer_port 一起傳入 URL，新視窗不需要等待 pywebviewready
        url = (f'file://{html_path}'
               f'?page=waveform'
               f'&vcd={vcd_path}'
               f'&surfer_port={_surfer_actual_port}'
               f'&signals={encoded_signals}')
        webview.create_window(
            f'CircuitTrace Waveform - {os.path.basename(vcd_path)}', 
            url,
            width=1200, 
            height=700,
            js_api=self
        )
        return {"success": True}

    def sync_waveform_signals(self, signals_json):
        for w in webview.windows:
            try:
                # We use evaluate_js to dispatch an event in every window
                w.evaluate_js(f"window.dispatchEvent(new CustomEvent('waveform_signals_sync', {{detail: {signals_json}}}));")
            except:
                pass
        return {"success": True}

    def read_surfer_wasm(self):
        """回傳 Surfer HTTP 伺服器的實際 port，前端用來建立 iframe URL。"""
        return {"success": True, "port": _surfer_actual_port}

    def read_vcd_file(self, vcd_path):
        import base64
        if not os.path.exists(vcd_path):
            return {"success": False, "error": "VCD file not found"}
        with open(vcd_path, 'rb') as f:
            return {"success": True, "data": base64.b64encode(f.read()).decode('ascii')}

if __name__ == '__main__':
    js_api = DesktopApi()
    
    # 啟動 Surfer 靜態檔案 HTTP 伺服器（自動解決 port 衝突）
    surfer_dir = os.path.join(FRONTEND_DIST, "surfer")
    if os.path.isdir(surfer_dir):
        t = threading.Thread(
            target=start_surfer_server,
            args=(surfer_dir, SURFER_PREFERRED_PORT),
            daemon=True
        )
        t.start()
        # 等待 server 確實綁定（最多 2 秒）
        import time
        for _ in range(20):
            if _surfer_actual_port != 0:
                break
            time.sleep(0.1)
    
    html_path = os.path.join(FRONTEND_DIST, "index.html")
    # Provide the path to the static file. webview can serve it directly.
    webview.create_window(
        'CircuitTrace', 
        f'file://{html_path}',
        width=1200, 
        height=800,
        min_size=(800, 600),
        js_api=js_api
    )
    # 主應用用 file:// 載入，Surfer iframe 用 localhost HTTP 伺服器
    webview.start(http_server=False)
