import React, { useEffect, useState } from 'react';
import './CausalityNexus.css';

interface FactLineage {
  id: number;
  id_padre: number | null;
  dominio: string;
  contenido: string;
  exergia: number;
  created_at: string;
  nivel: number;
}

interface CausalityNexusProps {
  factId: number;
  onClose: () => void;
  onStrike?: (factId: number, target: string) => void;
}

const CausalityNexus: React.FC<CausalityNexusProps> = ({ factId, onClose, onStrike }) => {
  const [lineage, setLineage] = useState<FactLineage[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchLineage = async () => {
      try {
        const response = await fetch(`http://localhost:8000/api/fact/lineage?id=${factId}`);
        const data = await response.json();
        if (data.status === 'SUCCESS') {
          setLineage(data.lineage);
        }
      } catch (error) {
        console.error('Error fetching lineage:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchLineage();
  }, [factId]);

  return (
    <div className="causality-nexus-overlay" onClick={onClose}>
      <div className="causality-nexus-container" onClick={(e) => e.stopPropagation()}>
        <div className="nexus-header">
          <div className="nexus-title-group">
            <h2 className="nexus-title">causality nexus</h2>
            <p className="nexus-subtitle">truth tree substrate</p>
          </div>
          <div className="nexus-info">
            <span className="nexus-id">id: fact_{factId}</span>
          </div>
          <button className="nexus-close-btn" onClick={onClose}>close</button>
        </div>

        <div className="nexus-content">
          {loading ? (
            <div className="nexus-loading">∴ reconstructing causality...</div>
          ) : lineage.length === 0 ? (
            <div className="nexus-empty">no ancestors detected</div>
          ) : (
            <div className="nexus-tree">
              {lineage.map((item, index) => (
                <div key={item.id} className="nexus-node-wrapper" data-node-index={index}>
                  {index < lineage.length - 1 && (
                    <div className="nexus-line-laser" />
                  )}
                  <div className={`nexus-node ${index === 0 ? 'root' : ''}`}>
                    <div className="node-meta">
                      <div className="flow-meter">
                        <div className="flow-fill" data-progress={item.exergia}></div>
                      </div>
                      <span className="node-domain">{item.dominio}</span>
                      <span className="node-exergy">{(item.exergia * 100).toFixed(1)}% exg</span>
                    </div>
                    <p className="node-content">{item.contenido}</p>
                    <div className="node-timestamp">{new Date(item.created_at).toLocaleString().toLowerCase()}</div>
                    <div className="node-level">depth: {item.nivel}</div>
                    
                    {onStrike && (
                      <button 
                        className="nexus-strike-btn"
                        onClick={() => onStrike(item.id, item.dominio)}
                      >
                        execute strike
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
        
        <div className="nexus-footer">
          <div className="nexus-status-bar">
            <span className="status-label">lineage_depth:</span>
            <span className="status-value">{lineage.length}</span>
            <span className="status-label">protocol:</span>
            <span className="status-value">cronos-ω/v7</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CausalityNexus;
