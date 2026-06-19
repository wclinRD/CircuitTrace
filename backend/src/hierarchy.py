import os
import pyslang

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

def build_hierarchy(f_path):
    files = parse_filelist(f_path)
    trees = []
    for file in files:
        if os.path.exists(file):
            tree = pyslang.syntax.SyntaxTree.fromFile(os.path.abspath(file))
            trees.append(tree)
            
    compilation = pyslang.ast.Compilation()
    for tree in trees:
        compilation.addSyntaxTree(tree)
        
    root = compilation.getRoot()
    sm = compilation.sourceManager
    
    def build_tree(inst, inst_name=None):
        children = []
        for member in inst.body:
            if isinstance(member, pyslang.ast.InstanceSymbol):
                children.append(build_tree(member, member.name))
            elif isinstance(member, pyslang.ast.InstanceArraySymbol):
                for elem in member.elements:
                    children.append(build_tree(elem, elem.name))
                    
        line = sm.getLineNumber(inst.location) if hasattr(inst, 'location') else 1
        
        return {
            "name": inst_name or inst.name,
            "module": inst.body.definition.name,
            "line": line,
            "children": children
        }
        
    hierarchy = [build_tree(top) for top in root.topInstances]
    
    # Also load source codes for all files
    sources = {}
    for file in files:
        filename = os.path.basename(file)
        if os.path.exists(file):
            with open(file, "r") as f:
                sources[filename] = f.read()
            
    return hierarchy, sources
