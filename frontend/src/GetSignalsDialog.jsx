import React, { useState } from 'react';

const GetSignalsDialog = ({ isOpen, onClose, hierarchyData, onAddSignals }) => {
  const [selectedScopePath, setSelectedScopePath] = useState(null);
  const [selectedSignals, setSelectedSignals] = useState(new Set());

  if (!isOpen) return null;

  // Helper to get node at path
  const getNodeAtPath = (pathList) => {
    let current = hierarchyData;
    for (let i = 0; i < pathList.length; i++) {
      if (current[pathList[i]] && current[pathList[i]].children) {
        current = current[pathList[i]].children;
      } else {
        return null;
      }
    }
    return current;
  };

  const currentScopeNode = selectedScopePath ? getNodeAtPath(selectedScopePath) : hierarchyData;

  const currentSignals = [];
  if (currentScopeNode) {
    for (const [key, val] of Object.entries(currentScopeNode)) {
      if (val.type === 'signal') {
        currentSignals.push({ name: key, ...val });
      }
    }
  }

  const handleToggleSignal = (full_name) => {
    const nextSet = new Set(selectedSignals);
    if (nextSet.has(full_name)) {
      nextSet.delete(full_name);
    } else {
      nextSet.add(full_name);
    }
    setSelectedSignals(nextSet);
  };

  const handleApply = () => {
    if (selectedSignals.size > 0) {
      onAddSignals(Array.from(selectedSignals));
      setSelectedSignals(new Set());
    }
    onClose();
  };

  // Tree Node component
  const ScopeTree = ({ node, path, name }) => {
    const isExpanded = true; // For simplicity, keep expanded or handle state if needed
    const isSelected = selectedScopePath && selectedScopePath.join('.') === path.join('.');

    return (
      <div style={{ marginLeft: path.length > 1 ? '10px' : '0' }}>
        <div 
          onClick={() => setSelectedScopePath(path)}
          style={{ 
            cursor: 'pointer', 
            padding: '2px 4px',
            background: isSelected ? '#007acc' : 'transparent',
            color: isSelected ? '#fff' : '#ccc',
            display: 'flex',
            alignItems: 'center'
          }}
        >
          <span style={{ marginRight: '4px' }}>📁</span>
          {name}
        </div>
        {isExpanded && node.children && (
          <div style={{ paddingLeft: '10px' }}>
            {Object.entries(node.children).filter(([k, v]) => v.type === 'module').map(([childName, childNode]) => (
              <ScopeTree 
                key={childName} 
                node={childNode} 
                path={[...path, childName]} 
                name={childName} 
              />
            ))}
          </div>
        )}
      </div>
    );
  };

  return (
    <div style={{
      position: 'absolute', top: '10%', left: '10%', width: '80%', height: '80%',
      background: '#252526', border: '1px solid #454545', boxShadow: '0 4px 8px rgba(0,0,0,0.5)',
      display: 'flex', flexDirection: 'column', zIndex: 1000
    }}>
      {/* Header */}
      <div style={{ background: '#333', padding: '8px', color: '#fff', display: 'flex', justifyContent: 'space-between' }}>
        <span>Get Signals</span>
        <button onClick={onClose} style={{ background: 'transparent', color: '#fff', border: 'none', cursor: 'pointer' }}>✖</button>
      </div>

      {/* Body */}
      <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
        {/* Left Pane: Hierarchy */}
        <div style={{ width: '30%', borderRight: '1px solid #454545', overflow: 'auto', padding: '8px' }}>
          {hierarchyData && Object.entries(hierarchyData).map(([rootName, rootNode]) => (
            <ScopeTree key={rootName} node={rootNode} path={[rootName]} name={rootName} />
          ))}
        </div>

        {/* Middle Pane: Signals */}
        <div style={{ width: '40%', borderRight: '1px solid #454545', overflow: 'auto', padding: '8px' }}>
          <table style={{ width: '100%', color: '#ccc', textAlign: 'left', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ background: '#333' }}>
                <th style={{ padding: '4px' }}>Signal</th>
                <th style={{ padding: '4px' }}>Bits</th>
              </tr>
            </thead>
            <tbody>
              {currentSignals.map(sig => {
                const isSelected = selectedSignals.has(sig.full_name);
                return (
                  <tr 
                    key={sig.full_name} 
                    onClick={() => handleToggleSignal(sig.full_name)}
                    onDoubleClick={() => {
                        onAddSignals([sig.full_name]);
                        onClose();
                    }}
                    style={{ 
                      background: isSelected ? '#094771' : 'transparent', 
                      cursor: 'pointer',
                      borderBottom: '1px solid #333'
                    }}
                  >
                    <td style={{ padding: '4px' }}>{sig.name}</td>
                    <td style={{ padding: '4px' }}>{sig.size}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        {/* Right Pane: Selected Signals Preview (Optional, keeping simple for now) */}
        <div style={{ width: '30%', overflow: 'auto', padding: '8px', color: '#ccc' }}>
           <h4 style={{ margin: '0 0 8px 0', color: '#fff' }}>Selected ({selectedSignals.size})</h4>
           <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
             {Array.from(selectedSignals).map(fn => (
               <li key={fn} style={{ padding: '2px 0' }}>{fn}</li>
             ))}
           </ul>
        </div>
      </div>

      {/* Footer */}
      <div style={{ padding: '8px', background: '#333', textAlign: 'right' }}>
        <button onClick={onClose} style={{ marginRight: '8px', padding: '4px 16px' }}>Cancel</button>
        <button onClick={handleApply} style={{ padding: '4px 16px', background: '#007acc', color: 'white', border: 'none' }}>Apply & Close</button>
      </div>
    </div>
  );
};

export default GetSignalsDialog;
