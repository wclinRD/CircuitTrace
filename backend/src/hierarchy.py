from pyverilog.vparser.parser import parse
from pyverilog.vparser.ast import ModuleDef, InstanceList
import os

def parse_filelist(f_path):
    base_dir = os.path.dirname(f_path)
    files = []
    with open(f_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("//"):
                files.append(os.path.join(base_dir, line))
    return files

def build_hierarchy(f_path):
    files = parse_filelist(f_path)
    ast, _ = parse(files)
    
    modules = {}
    for item in ast.description.definitions:
        if isinstance(item, ModuleDef):
            instances = []
            for child in item.items:
                if isinstance(child, InstanceList):
                    for inst in child.instances:
                        instances.append({
                            "name": inst.name,
                            "module": inst.module,
                            "line": inst.lineno
                        })
            modules[item.name] = {
                "name": item.name,
                "instances": instances,
                "line": item.lineno
            }
    
    # Find top modules
    instantiated = set()
    for mod in modules.values():
        for inst in mod["instances"]:
            instantiated.add(inst["module"])
            
    tops = [name for name in modules if name not in instantiated]
    
    def build_tree(mod_name, inst_name=None):
        if mod_name not in modules:
            return {"name": inst_name or mod_name, "module": mod_name, "children": []}
        
        mod = modules[mod_name]
        children = []
        for inst in mod["instances"]:
            children.append(build_tree(inst["module"], inst["name"]))
            
        return {
            "name": inst_name or mod_name,
            "module": mod_name,
            "line": mod["line"],
            "children": children
        }
        
    hierarchy = [build_tree(top) for top in tops]
    
    # Also load source codes for all files
    sources = {}
    for file in files:
        filename = os.path.basename(file)
        with open(file, "r") as f:
            sources[filename] = f.read()
            
    return hierarchy, sources
