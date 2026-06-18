import sys
from pyverilog.vparser.parser import parse

def main():
    if len(sys.argv) < 2:
        print("Usage: python probe_pyverilog.py <file.v>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    ast, directives = parse([file_path])
    ast.show()

if __name__ == '__main__':
    main()
