from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import os
from project_manager import ProjectManager
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

class SimulateRequest(BaseModel):
    file_path: str

class WaveformLoadRequest(BaseModel):
    vcd_path: str

class WaveformDataRequest(BaseModel):
    signal_name: str
    start_time: int
    end_time: int

@app.post("/api/parse")
def parse_rtl(req: ParseRequest):
    if not os.path.exists(req.file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    import traceback

    try:
        pm = ProjectManager.get_instance()
        hierarchy, sources = pm.load_project(req.file_path)
        
        # Determine source mapping for single file fallback if needed
        # In pyslang we load all.
        if not req.file_path.endswith('.f'):
            sources = {os.path.basename(req.file_path): sources.get(os.path.basename(req.file_path), "")}
            
        return {
            "success": True,
            "hierarchy": hierarchy,
            "sources": sources,
            "compile_logs": "Parsed with pyslang."
        }
    except Exception as e:
        return {
            "success": False,
            "hierarchy": [],
            "sources": {},
            "compile_logs": f"Error parsing project:\\n{traceback.format_exc()}"
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

@app.post("/api/simulate")
def api_simulate(req: SimulateRequest):
    import subprocess
    import tempfile
    
    if not os.path.exists(req.file_path):
        return {"success": False, "logs": "File not found."}
        
    files_to_compile = []
    if req.file_path.endswith('.f'):
        files_to_compile = parse_filelist(req.file_path)
    else:
        files_to_compile = [req.file_path]
        
    # We will compile to a temporary output file
    temp_vvp = os.path.join(tempfile.gettempdir(), "sim_output.vvp")
    
    logs = ""
    # 1. Run iverilog
    cmd_iverilog = ["iverilog", "-o", temp_vvp] + files_to_compile
    try:
        res_iv = subprocess.run(cmd_iverilog, capture_output=True, text=True, cwd=os.path.dirname(req.file_path))
        logs += f"$ {' '.join(cmd_iverilog)}\\n"
        logs += res_iv.stdout + res_iv.stderr
        
        if res_iv.returncode != 0:
            return {"success": False, "logs": logs + f"\\niverilog failed with exit code {res_iv.returncode}."}
            
        # 2. Run vvp
        cmd_vvp = ["vvp", temp_vvp]
        logs += f"\\n$ {' '.join(cmd_vvp)}\\n"
        res_vvp = subprocess.run(cmd_vvp, capture_output=True, text=True, cwd=os.path.dirname(req.file_path))
        logs += res_vvp.stdout + res_vvp.stderr
        
        return {"success": res_vvp.returncode == 0, "logs": logs}
        
    except Exception as e:
        import traceback
        logs += f"\\nException running simulation: {traceback.format_exc()}"
        return {"success": False, "logs": logs}

from waveform import WaveformParser

@app.post("/api/waveform/hierarchy")
def api_waveform_hierarchy(req: WaveformLoadRequest):
    try:
        parser = WaveformParser.get_instance()
        parser.load_vcd(req.vcd_path)
        tree = parser.get_hierarchy()
        
        # vcdvcd also exposes timescale, endtime
        meta = {}
        if parser.vcd_obj:
            meta['endtime'] = parser.vcd_obj.endtime
            meta['timescale'] = parser.vcd_obj.timescale
            
        return {"success": True, "hierarchy": tree, "meta": meta}
    except Exception as e:
        import traceback
        return {"success": False, "error": str(e), "traceback": traceback.format_exc()}

@app.post("/api/waveform/data")
def api_waveform_data(req: WaveformDataRequest):
    try:
        parser = WaveformParser.get_instance()
        data = parser.get_signal_data(req.signal_name, req.start_time, req.end_time)
        return {"success": True, "data": data}
    except Exception as e:
        return {"success": False, "error": str(e)}

# Mount static files
if os.path.exists(FRONTEND_DIST):
    app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIST, "assets")), name="assets")

    @app.get("/{full_path:path}")
    def serve_react(full_path: str):
        file_path = os.path.join(FRONTEND_DIST, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(FRONTEND_DIST, "index.html"))

