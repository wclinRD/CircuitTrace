import os
import tempfile
import sys

# mimic desktop_app.py setup
os.environ['PATH'] = os.environ.get('PATH', '') + ':/opt/homebrew/bin:/usr/local/bin'
os.chdir(tempfile.gettempdir())

from hierarchy import build_hierarchy

def parse_project(file_path):
    try:
        tree, sources = build_hierarchy(file_path)
        print("SUCCESS! Hierarchy:", tree)
    except Exception as e:
        print("ERROR:", e)

parse_project('/Users/wclin/antigravity/verdi/backend/tests/fixtures/large_project/project.f')
