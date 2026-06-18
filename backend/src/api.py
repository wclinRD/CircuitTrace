from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import os
from hierarchy import build_hierarchy, parse_filelist
from tracer import trace_drive, trace_load, trace_connection

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

import sys

if getattr(sys, 'frozen', False):
    FRONTEND_DIST = os.path.join(sys._MEIPASS, "frontend-dist")
else:
    FRONTEND_DIST = os.path.join(os.path.dirname(__file__), "..", "..", "release", "frontend-dist")

# We will mount static files at the end to avoid intercepting API routes.

class ParseRequest(BaseModel):
    file_path: str

class TraceRequest(BaseModel):
    file_path: str
    module_name: str
    signal_name: str

@app.post("/api/parse")
def parse_rtl(req: ParseRequest):
    if not os.path.exists(req.file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    import io
    import sys
    from contextlib import redirect_stdout, redirect_stderr
    import traceback

    output_buffer = io.StringIO()
    
    if req.file_path.endswith('.f'):
        try:
            with redirect_stdout(output_buffer), redirect_stderr(output_buffer):
                hierarchy, sources = build_hierarchy(req.file_path)
            
            return {
                "success": True,
                "hierarchy": hierarchy,
                "sources": sources,
                "compile_logs": output_buffer.getvalue()
            }
        except Exception as e:
            error_msg = f"Error parsing project:\\n{traceback.format_exc()}"
            output_buffer.write("\\n" + error_msg)
            return {
                "success": False,
                "hierarchy": [],
                "sources": {},
                "compile_logs": output_buffer.getvalue()
            }
    else:
        # Fallback for single .v file
        try:
            with redirect_stdout(output_buffer), redirect_stderr(output_buffer):
                hierarchy, sources = build_hierarchy(req.file_path)
            return {
                "success": True,
                "hierarchy": hierarchy,
                "sources": {os.path.basename(req.file_path): sources[os.path.basename(req.file_path)]},
                "compile_logs": output_buffer.getvalue()
            }
        except Exception as e:
            error_msg = f"Error parsing file:\\n{traceback.format_exc()}"
            output_buffer.write("\\n" + error_msg)
            return {
                "success": False,
                "hierarchy": [],
                "sources": {},
                "compile_logs": output_buffer.getvalue()
            }

@app.post("/api/trace/drive")
def api_trace_drive(req: TraceRequest):
    drivers = trace_drive(req.file_path, req.module_name, req.signal_name)
    return {"drive_ports": drivers}

@app.post("/api/trace/load")
def api_trace_load(req: TraceRequest):
    loads = trace_load(req.file_path, req.module_name, req.signal_name)
    return {"load_ports": loads}

@app.post("/api/trace/connection")
def api_trace_connection(req: TraceRequest):
    connections = trace_connection(req.file_path, req.module_name, req.signal_name)
    return {"connection_ports": connections}

# Mount static files
if os.path.exists(FRONTEND_DIST):
    app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIST, "assets")), name="assets")

    @app.get("/{full_path:path}")
    def serve_react(full_path: str):
        file_path = os.path.join(FRONTEND_DIST, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(FRONTEND_DIST, "index.html"))

