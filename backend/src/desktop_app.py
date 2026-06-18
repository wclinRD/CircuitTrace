import sys
import os
import tempfile

# Fix macOS GUI app PATH issue (cannot find iverilog installed by Homebrew)
os.environ['PATH'] = os.environ.get('PATH', '') + ':/opt/homebrew/bin:/usr/local/bin'

# Fix PyVerilog needing write access to current directory for 'preprocess.output'
os.chdir(tempfile.gettempdir())

import webview
from hierarchy import build_hierarchy
from tracer import trace_drive, trace_load, trace_connection

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
        try:
            tree, sources = build_hierarchy(file_path)
            return {"status": "success", "hierarchy": tree, "sources": sources}
        except Exception as e:
            return {"status": "error", "message": str(e)}

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

if __name__ == '__main__':
    js_api = DesktopApi()
    
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
    # Built-in HTTP server might be needed for assets routing
    # But usually file:// protocol handles relative paths fine if base: './' is set
    webview.start()
