import os
import pyslang
import re
from project_manager import ProjectManager

def find_target_instance(module_name):
    pm = ProjectManager.get_instance()
    if not pm.compilation:
        return None
    
    root = pm.compilation.getRoot()
    target_inst = None
    
    def find_mod(inst):
        nonlocal target_inst
        if inst.body.definition.name == module_name:
            target_inst = inst
            return
        for member in inst.body:
            if isinstance(member, pyslang.ast.InstanceSymbol):
                find_mod(member)
            elif isinstance(member, pyslang.ast.InstanceArraySymbol):
                for elem in member.elements:
                    find_mod(elem)
                    
    for top in root.topInstances:
        find_mod(top)
        if target_inst:
            break
            
    return target_inst

def trace_signal(file_path, module_name, signal_name, trace_type):
    pm = ProjectManager.get_instance()
    if pm.current_project_path != file_path:
        pm.load_project(file_path)
        
    root = pm.compilation.getRoot()
    
    if '.' in signal_name:
        parts = signal_name.split('.')
        leaf_signal = parts[-1]
        inst_path = '.'.join(parts[:-1])
        sym = root.lookupName(inst_path)
        inst = sym if sym else (root.topInstances[0] if root.topInstances else root)
        ast_signal_name = leaf_signal
    else:
        inst = find_target_instance(module_name)
        if not inst:
            inst = root.topInstances[0] if root.topInstances else root
        ast_signal_name = signal_name
        
    results = []
    
    if not inst:
        results.append({
            "module": module_name, 
            "port": signal_name, 
            "file": os.path.basename(file_path), 
            "line": 1, 
            "type": f"{trace_type} (module not found)"
        })
        return results
        
    sm = pm.compilation.sourceManager
    seen = set()
    
    def add_result(node):
        loc = node.sourceRange.start if hasattr(node, 'sourceRange') else None
        if not loc:
            loc = node.location if hasattr(node, 'location') else None
            
        line = sm.getLineNumber(loc) if loc else 1
        filename = sm.getFileName(loc) if loc else os.path.basename(file_path)
        
        sig = f"{filename}:{line}"
        if sig not in seen:
            seen.add(sig)
            results.append({
                "module": getattr(inst, 'name', module_name),
                "port": signal_name,
                "file": os.path.basename(filename),
                "line": line,
                "type": trace_type
            })

    def visitor(node):
        kind_str = str(getattr(node, 'kind', ''))
        
        if 'Assign' in kind_str and hasattr(node, 'left') and hasattr(node, 'right'):
            sym = node.left.getSymbolReference()
            is_lhs = sym and sym.name == ast_signal_name
            
            if trace_type == 'drive' and is_lhs:
                add_result(node)
            elif trace_type == 'load':
                if not is_lhs:
                    if hasattr(node.right, 'syntax') and ast_signal_name in str(node.right.syntax):
                        add_result(node)
                        
        elif trace_type == 'load' and ('Statement' in kind_str or 'Expression' in kind_str):
            if hasattr(node, 'syntax') and node.syntax:
                if re.search(rf'\b{ast_signal_name}\b', str(node.syntax)):
                    add_result(node)
                    
        elif 'Port' in kind_str:
            if hasattr(node, 'name') and node.name == ast_signal_name:
                add_result(node)
                
    inst.visit(visitor)
    
    if not results:
        results.append({
            "module": module_name, 
            "port": signal_name, 
            "file": os.path.basename(file_path), 
            "line": 1, 
            "type": f"{trace_type} (not found)"
        })
        
    return results

def trace_drive(file_path, module_name, signal_name):
    return trace_signal(file_path, module_name, signal_name, 'drive')

def trace_load(file_path, module_name, signal_name):
    return trace_signal(file_path, module_name, signal_name, 'load')

def trace_connection(file_path, module_name, signal_name):
    drives = trace_drive(file_path, module_name, signal_name)
    loads = trace_load(file_path, module_name, signal_name)
    
    seen = set()
    res = []
    for x in drives + loads:
        if "not found" in x['type']: continue
        sig = f"{x['file']}:{x['line']}"
        if sig not in seen:
            seen.add(sig)
            x['type'] = 'connection'
            res.append(x)
            
    if not res:
        res.append({
            "module": module_name, 
            "port": signal_name, 
            "file": os.path.basename(file_path), 
            "line": 1, 
            "type": "connection (not found)"
        })
    return res
