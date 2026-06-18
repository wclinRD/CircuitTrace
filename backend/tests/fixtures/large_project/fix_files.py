import os
import glob

base_dir = "/Users/wclin/antigravity/verdi/backend/tests/fixtures/large_project"

for filepath in glob.glob(os.path.join(base_dir, "*.v")):
    with open(filepath, "r") as f:
        content = f.read()
    
    # Remove literal backslash-n strings that were accidentally written
    content = content.replace("\\n", "\n")
    
    with open(filepath, "w") as f:
        f.write(content)
        
print("Fixed literal newlines in .v files.")
