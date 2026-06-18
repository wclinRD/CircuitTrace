import os
import re

def parse_filelist(f_path):
    base_dir = os.path.dirname(f_path)
    files = []
    if f_path.endswith('.f'):
        with open(f_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("//"):
                    files.append(os.path.join(base_dir, line))
    else:
        files.append(f_path)
    return files

def find_signal_locations(file_path, signal_name, trace_type):
    # trace_type: 'drive' or 'load'
    files = parse_filelist(file_path)
    results = []
    
    # Heuristic regex patterns for Verilog
    drive_pattern = re.compile(rf'\bassign\s+{signal_name}\s*=|'
                               rf'\boutput\s+.*?\b{signal_name}\b|'
                               rf'\b{signal_name}\s*<=|'
                               rf'\b{signal_name}\s*=')
                               
    load_pattern = re.compile(rf'=\s*[^;]*\b{signal_name}\b|'
                              rf'\binput\s+.*?\b{signal_name}\b|'
                              rf'\bif\s*\([^)]*\b{signal_name}\b[^)]*\)|'
                              rf'\bcase\s*\([^)]*\b{signal_name}\b[^)]*\)')
                              
    connection_pattern = re.compile(rf'\.\w+\s*\(\s*{signal_name}\s*\)')

    pattern = drive_pattern if trace_type == 'drive' else load_pattern
    
    for f in files:
        if not os.path.exists(f): continue
        basename = os.path.basename(f)
        module_name = basename.replace('.v', '') # Rough guess based on filename
        
        with open(f, 'r') as file_obj:
            lines = file_obj.readlines()
            for i, line in enumerate(lines):
                # Check for direct match or module instantiation connection
                if pattern.search(line) or connection_pattern.search(line):
                    results.append({
                        "module": module_name,
                        "port": signal_name,
                        "file": basename,
                        "line": i + 1,
                        "type": trace_type
                    })
                    
    # If no results found, provide a dummy result so the UI still responds
    if not results:
        results.append({
            "module": "unknown", 
            "port": signal_name, 
            "file": os.path.basename(file_path), 
            "line": 1, 
            "type": f"{trace_type} (not found)"
        })
        
    return results

def trace_drive(file_path, module_name, signal_name):
    return find_signal_locations(file_path, signal_name, 'drive')

def trace_load(file_path, module_name, signal_name):
    return find_signal_locations(file_path, signal_name, 'load')

def trace_connection(file_path, module_name, signal_name):
    drives = trace_drive(file_path, module_name, signal_name)
    loads = trace_load(file_path, module_name, signal_name)
    
    # Deduplicate
    seen = set()
    res = []
    for x in drives + loads:
        sig = f"{x['file']}:{x['line']}"
        if sig not in seen:
            seen.add(sig)
            x['type'] = 'connection'
            res.append(x)
            
    return res
