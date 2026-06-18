import sys
import os
import pyslang

def main():
    if len(sys.argv) < 2:
        print("Usage: python probe_slang.py <file.f>")
        sys.exit(1)
        
    f_path = sys.argv[1]
    base_dir = os.path.dirname(f_path)
    
    # Read .f file
    files = []
    with open(f_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("//"):
                files.append(os.path.join(base_dir, line))
                
    # Initialize pyslang compiler
    driver = pyslang.Driver()
    for file in files:
        driver.addSingleUnitSource(file)
        
    tree = driver.parseAllSources()
    compilation = driver.createCompilation()
    
    # Traverse hierarchy
    def print_inst(inst, indent=0):
        print(" " * indent + f"Instance: {inst.name} ({inst.body.definition.name})")
        
        for member in inst.body.members:
            if isinstance(member, pyslang.InstanceSymbol):
                print_inst(member, indent + 2)
            elif isinstance(member, pyslang.InstanceArraySymbol):
                for elem in member.elements:
                    print_inst(elem, indent + 2)

    root = compilation.getRoot()
    for inst in root.topInstances:
        print_inst(inst)

if __name__ == '__main__':
    main()
