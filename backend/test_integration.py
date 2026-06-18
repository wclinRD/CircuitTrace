import os
import sys
import tempfile

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))
os.environ['PATH'] = os.environ.get('PATH', '') + ':/opt/homebrew/bin:/usr/local/bin'
os.chdir(tempfile.gettempdir())

from hierarchy import build_hierarchy
from tracer import trace_drive, trace_load, trace_connection

project_file = '/Users/wclin/antigravity/verdi/backend/tests/fixtures/large_project/project.f'

print("1. Testing Parse...")
tree, sources = build_hierarchy(project_file)
print("Parse successful! Modules:", len(tree))

print("\n2. Testing Trace Drive ('op_a')...")
drive_res = trace_drive(project_file, 'top', 'op_a')
print("Drive successful! Found:", drive_res)

print("\n3. Testing Trace Load ('op_a')...")
load_res = trace_load(project_file, 'top', 'op_a')
print("Load successful! Found:", load_res)

print("\n4. Testing Trace Connection ('op_a')...")
conn_res = trace_connection(project_file, 'top', 'op_a')
print("Connection successful! Found:", conn_res)

print("\nALL TESTS PASSED AUTOMATICALLY!")
