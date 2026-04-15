import React, { useState } from 'react';
import './SemanticMemoryPanel.css';

interface MemoryEntry {
  id: string;
  pointer: string;
  preview: string;
  entities: number;
  retention: number;
  timestamp: string;
}

const MOCK_ENTRIES: MemoryEntry[] = [
  { id: '1', pointer: 'cortex://memory/fact/a8f2c1e9', preview: 'Sovereign Exergy-RAG pipeline...', entities: 12, retention: 100, timestamp: '00:47:13' },
  { id: '2', pointer: 'cortex://memory/fact/b3d7f80a', preview: 'Token compression middleware v2...', entities: 8, retention: 100, timestamp: '00:44:08' },
  { id: '3', pointer: 'cortex://memory/fact/c1f909d2', preview: 'xRAG single-token loss limits...', entities: 5, retention: 98.2, timestamp: '00:41:32' },
  { id: '4', pointer: 'cortex://memory/fact/d4a2ee71', preview: 'CORTEX Falsation Engine axioms...', entities: 15, retention: 100, timestamp: '00:38:01' },
];

export const SemanticMemoryPanel: React.FC = () => {
  const [selected, setSelected] = useState<string | null>(null);

  return (
    <div className="memory-panel">
      <div className="memory-panel-header">
        <span className="memory-panel-title">EXERGY-RAG STORE</span>
        <span className="memory-panel-count">{MOCK_ENTRIES.length} facts</span>
      </div>

      <div className="memory-panel-body">
        {MOCK_ENTRIES.map(entry => (
          <div
            key={entry.id}
            className={`memory-entry ${selected === entry.id ? 'selected' : ''}`}
            onClick={() => setSelected(selected === entry.id ? null : entry.id)}
          >
            <div className="memory-entry-header">
              <span className="memory-pointer">{entry.pointer.slice(-12)}</span>
              <span
                className="memory-retention"
                style={{ color: entry.retention === 100 ? '#2BE58B' : '#E5A82B' }}
              >
                {entry.retention}%
              </span>
            </div>
            <p className="memory-preview">{entry.preview}</p>
            {selected === entry.id && (
              <div className="memory-detail">
                <div className="memory-detail-row">
                  <span>POINTER</span>
                  <code>{entry.pointer}</code>
                </div>
                <div className="memory-detail-row">
                  <span>ENTITIES</span>
                  <code>{entry.entities} extracted</code>
                </div>
                <div className="memory-detail-row">
                  <span>RETENTION</span>
                  <code style={{ color: entry.retention === 100 ? '#2BE58B' : '#E5A82B' }}>{entry.retention}%</code>
                </div>
                <div className="memory-detail-row">
                  <span>INDEXED</span>
                  <code>{entry.timestamp}</code>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      <div className="memory-panel-footer">
        <div className="memory-stat">
          <span>BRIDGE</span>
          <span style={{ color: '#2BE58B' }}>ACTIVE</span>
        </div>
        <div className="memory-stat">
          <span>STORE</span>
          <span style={{ color: '#2B3BE5' }}>sqlite-vec</span>
        </div>
      </div>
    </div>
  );
};
