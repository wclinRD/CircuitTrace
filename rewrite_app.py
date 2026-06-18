import re

with open("frontend/src/App.jsx", "r") as f:
    content = f.read()

# Replace lucide imports
content = content.replace("from 'lucide-react';", "from 'lucide-react';\nimport { ArrowLeft, ArrowRight, Terminal, ListTree, Search } from 'lucide-react';")

# Replace state definitions
state_insert = """  const [activeBottomTab, setActiveBottomTab] = useState('trace');
  const [traceResults, setTraceResults] = useState([]);
  const [historyStack, setHistoryStack] = useState([]);
  const [historyIndex, setHistoryIndex] = useState(-1);
"""
content = content.replace("  const [projectFile, setProjectFile] = useState('');", "  const [projectFile, setProjectFile] = useState('');\n" + state_insert)

# Add jumpToFileLine function
jump_func = """
  const jumpToFileLine = (file, line, saveHistory = true) => {
    if (saveHistory) {
      const newStack = historyStack.slice(0, historyIndex + 1);
      newStack.push({ file, line });
      setHistoryStack(newStack);
      setHistoryIndex(newStack.length - 1);
    }
    
    setCurrentFile(file);
    setTimeout(() => {
      if (editorRef.current && line > 0) {
        editorRef.current.revealLineInCenter(line);
        editorRef.current.setPosition({ lineNumber: line, column: 1 });
        editorRef.current.focus();
      }
    }, 100);
  };

  const goBack = () => {
    if (historyIndex > 0) {
      const prev = historyStack[historyIndex - 1];
      setHistoryIndex(historyIndex - 1);
      jumpToFileLine(prev.file, prev.line, false);
    }
  };

  const goForward = () => {
    if (historyIndex < historyStack.length - 1) {
      const next = historyStack[historyIndex + 1];
      setHistoryIndex(historyIndex + 1);
      jumpToFileLine(next.file, next.line, false);
    }
  };
"""
content = content.replace("  const addMessage = (type, text) => {", jump_func + "\n  const addMessage = (type, text) => {")

# Modify traceSignal
trace_signal_orig = """      const target = ports[0];
      if (target.file && target.line > 0) {
        setCurrentFile(target.file);
        setTimeout(() => {
          if (editorRef.current) {
            editorRef.current.revealLineInCenter(target.line);
            editorRef.current.setPosition({ lineNumber: target.line, column: 1 });
            editorRef.current.focus();
          }
        }, 100);
      }"""
trace_signal_new = """      // Update trace results table
      const newResults = ports.map(p => ({
        type: type.toUpperCase(),
        signal: signalName,
        module: p.module,
        port: p.port,
        file: p.file,
        line: p.line
      }));
      setTraceResults(newResults);
      setActiveBottomTab('trace');

      const target = ports[0];
      if (target.file && target.line > 0) {
        jumpToFileLine(target.file, target.line);
      }"""
content = content.replace(trace_signal_orig, trace_signal_new)

# Modify Editor panel
editor_orig = """        <div className="panel editor-panel">
          <Editor"""
editor_new = """        <div className="panel editor-panel">
          <div className="editor-toolbar">
            <button className="toolbar-btn" onClick={goBack} disabled={historyIndex <= 0} title="Go Back">
              <ArrowLeft size={16} />
            </button>
            <button className="toolbar-btn" onClick={goForward} disabled={historyIndex >= historyStack.length - 1} title="Go Forward">
              <ArrowRight size={16} />
            </button>
            <div className="toolbar-path">{currentFile}</div>
          </div>
          <Editor"""
content = content.replace(editor_orig, editor_new)

# Modify Bottom panel
bottom_orig = """      <div className="panel message-panel">
        <div className="panel-header">Message Console</div>
        <div className="panel-body messages">
          {messages.map((m, i) => (
            <div key={i} className={`message ${m.type}`}>
              <span className="time">[{m.time}]</span> {m.text}
            </div>
          ))}
        </div>
      </div>"""
bottom_new = """      <div className="panel message-panel">
        <div className="bottom-tabs">
          <div className={`bottom-tab ${activeBottomTab === 'console' ? 'active' : ''}`} onClick={() => setActiveBottomTab('console')}>
            <Terminal size={14} /> Message Console
          </div>
          <div className={`bottom-tab ${activeBottomTab === 'trace' ? 'active' : ''}`} onClick={() => setActiveBottomTab('trace')}>
            <ListTree size={14} /> Trace Results {traceResults.length > 0 && `(${traceResults.length})`}
          </div>
        </div>
        
        <div className="panel-body">
          {activeBottomTab === 'console' && (
            <div className="messages">
              {messages.map((m, i) => (
                <div key={i} className={`message ${m.type}`}>
                  <span className="time">[{m.time}]</span> {m.text}
                </div>
              ))}
            </div>
          )}
          
          {activeBottomTab === 'trace' && (
            <div className="trace-table-container">
              {traceResults.length === 0 ? (
                <div className="empty-state">No trace results to display.</div>
              ) : (
                <table className="trace-table">
                  <thead>
                    <tr>
                      <th>Action</th>
                      <th>Signal</th>
                      <th>Module</th>
                      <th>Port</th>
                      <th>File</th>
                      <th>Line</th>
                    </tr>
                  </thead>
                  <tbody>
                    {traceResults.map((row, idx) => (
                      <tr key={idx} onClick={() => jumpToFileLine(row.file, row.line)}>
                        <td><span className={`badge ${row.type.toLowerCase()}`}>{row.type}</span></td>
                        <td><strong>{row.signal}</strong></td>
                        <td>{row.module}</td>
                        <td>{row.port}</td>
                        <td>{row.file}</td>
                        <td>{row.line}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          )}
        </div>
      </div>"""
content = content.replace(bottom_orig, bottom_new)

# Modify Context Menu
menu_orig = """          <div className="menu-header">Signal: {contextMenu.word}</div>
          <div className="menu-item" onClick={() => { traceSignal('load', contextMenu.word); closeContextMenu(); }}>
            Trace Load Port
          </div>
          <div className="menu-item" onClick={() => { traceSignal('connection', contextMenu.word); closeContextMenu(); }}>
            Trace Connection
          </div>"""
menu_new = """          <div className="menu-header">Signal: {contextMenu.word}</div>
          <div className="menu-item" onClick={() => { traceSignal('drive', contextMenu.word); closeContextMenu(); }}>
            <Search size={14} style={{marginRight: 6, verticalAlign: 'middle'}}/> Trace Drive
          </div>
          <div className="menu-item" onClick={() => { traceSignal('load', contextMenu.word); closeContextMenu(); }}>
            <Search size={14} style={{marginRight: 6, verticalAlign: 'middle'}}/> Trace Load
          </div>
          <div className="menu-item" onClick={() => { traceSignal('connection', contextMenu.word); closeContextMenu(); }}>
            <Search size={14} style={{marginRight: 6, verticalAlign: 'middle'}}/> Trace Connection
          </div>"""
content = content.replace(menu_orig, menu_new)

with open("frontend/src/App.jsx", "w") as f:
    f.write(content)

