import React, { useState, useEffect } from 'react';
import './SemanticMemoryPanel.css';

interface Strike {
  id: string;
  platform: string;
  program_name: string;
  status: string;
  exergy: number;
  max_bounty: string;
}

interface MemoryEntry {
  id: string;
  pointer: string;
  preview: string;
  entities: number;
  retention: number;
  status: string;
}

export const SemanticMemoryPanel: React.FC = () => {
  const [selected, setSelected] = useState<string | null>(null);
  const [entries, setEntries] = useState<MemoryEntry[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchStrikes = async () => {
      try {
        const res = await fetch('/api/strikes?limit=10');
        const data: Strike[] = await res.json();
        
        // Map strikes into semantic memory entries
        const mapped: MemoryEntry[] = data.map((s, i) => ({
          id: String(s.id || i),
          pointer: `cortex://strike/${s.platform}/${String(s.id || i).slice(0, 8)}`,
          preview: `${s.program_name} — ${s.platform}`.toLowerCase(),
          entities: Math.floor(s.exergy * 10),
          retention: s.exergy >= 0.8 ? 100 : Math.round(s.exergy * 100),
          status: s.status?.toLowerCase() || 'indexed',
        }));
        setEntries(mapped.length > 0 ? mapped : FALLBACK);
      } catch {
        setEntries(FALLBACK);
      } finally {
        setLoading(false);
      }
    };

    fetchStrikes();
    const interval = setInterval(fetchStrikes, 15000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="memory-panel">
      <div className="memory-panel-header">
        <span className="memory-panel-title">exergy-rag store</span>
        <span className="memory-panel-count">{loading ? '...' : `${entries.length} facts`}</span>
      </div>

      <div className="memory-panel-body">
        {entries.map(entry => (
          <div
            key={entry.id}
            className={`memory-entry ${selected === entry.id ? 'selected' : ''}`}
            onClick={() => setSelected(selected === entry.id ? null : entry.id)}
          >
            <div className="memory-entry-header">
              <span className="memory-pointer">{entry.pointer.slice(-18)}</span>
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
                  <span>pointer</span>
                  <code>{entry.pointer}</code>
                </div>
                <div className="memory-detail-row">
                  <span>entities</span>
                  <code>{entry.entities} extracted</code>
                </div>
                <div className="memory-detail-row">
                  <span>status</span>
                  <code className={entry.status === 'submitted' ? 'pulse-green' : ''}>{entry.status}</code>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      <div className="memory-panel-footer">
        <div className="memory-stat">
          <span>bridge</span>
          <span style={{ color: '#2BE58B' }}>active</span>
        </div>
        <div className="memory-stat">
          <span>store</span>
          <span style={{ color: '#2B3BE5' }}>sqlite-vec</span>
        </div>
      </div>
    </div>
  );
};

// Fallback when API is unreachable
const FALLBACK: MemoryEntry[] = [
  { id: '1', pointer: 'cortex://memory/fact/a8f2c1e9', preview: 'sovereign exergy-rag pipeline...', entities: 12, retention: 100, status: 'indexed' },
  { id: '2', pointer: 'cortex://memory/fact/b3d7f80a', preview: 'token compression middleware v2...', entities: 8, retention: 100, status: 'indexed' },
  { id: '3', pointer: 'cortex://memory/fact/c1f909d2', preview: 'xrag single-token loss limits...', entities: 5, retention: 98, status: 'indexed' },
];
