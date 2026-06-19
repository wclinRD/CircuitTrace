import os
import pyslang
from typing import Dict, Optional, Tuple, Any

class ProjectManager:
    """
    Manages the cached pyslang Compilation and syntax trees for the current project.
    Follows Harness Engineering principles by centralizing AST state management.
    """
    _instance = None

    def __init__(self):
        self.current_project_path: Optional[str] = None
        self.compilation: Optional[pyslang.ast.Compilation] = None
        self.hierarchy: list = []
        self.sources: Dict[str, str] = {}

    @classmethod
    def get_instance(cls) -> "ProjectManager":
        if cls._instance is None:
            cls._instance = ProjectManager()
        return cls._instance

    def load_project(self, f_path: str) -> Tuple[list, Dict[str, str]]:
        """
        Parses the project files, builds the compilation and hierarchy, and caches them.
        """
        # Parse filelist
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
            
        trees = []
        for file in files:
            if os.path.exists(file):
                tree = pyslang.syntax.SyntaxTree.fromFile(os.path.abspath(file))
                trees.append(tree)

        compilation = pyslang.ast.Compilation()
        for tree in trees:
            compilation.addSyntaxTree(tree)

        self.compilation = compilation
        self.current_project_path = f_path
        
        # Build hierarchy
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
            
        self.hierarchy = [build_tree(top) for top in root.topInstances]
        
        # Load sources
        self.sources = {}
        for file in files:
            filename = os.path.basename(file)
            if os.path.exists(file):
                with open(file, "r") as f:
                    self.sources[filename] = f.read()

        return self.hierarchy, self.sources
