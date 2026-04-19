import React, { useState, useEffect } from 'react';
import './AudienceIntelligence.css';

interface Receptor {
  h_sid: string;
  exergy: number;
  confidence: number;
  class: string;
}

interface AIEStats {
  total_signals: number;
  classes: Record<string, number>;
  content_pulse: Record<string, number>;
  top_receptors: Receptor[];
}

interface AudienceIntelligenceProps {
  onClose?: () => void;
}

export const AudienceIntelligence: React.FC<AudienceIntelligenceProps> = ({ onClose }) => {
  const [stats, setStats] = useState<AIEStats | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchStats = async () => {
    try {
      const res = await fetch('/api/v1/analytic/stats');
      const data = await res.json();
      setStats(data);
    } catch (err) {
      console.error("∴ AIE: Statistics synchronization failure.", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();
    const interval = setInterval(fetchStats, 10000); // 10s sync
    return () => clearInterval(interval);
  }, []);

  if (loading) return <div className="aie-container">SYNCHRONIZING SUBSTRATE...</div>;

  return (
    <div className="aie-container">
      <button className="aie-close-btn" onClick={onClose}>×</button>
      <div className="aie-header">
        <div className="aie-title">AUDIENCE INTELLIGENCE Ω-1</div>
        <div className="tag-neutral">{stats?.total_signals} SIGNALS CAPTURED</div>
      </div>

      <div className="aie-grid">
        <div className="aie-card">
          <div className="aie-card-sub">
            TOP 10 RECEPTORS BY ENGAGEMENT EXERGY
          </div>
          <table className="aie-table">
            <thead>
              <tr>
                <th>HMAC_ID</th>
                <th>EXERGY_SCORE</th>
                <th>CONFIDENCE</th>
                <th>CLASS</th>
              </tr>
            </thead>
            <tbody>
              {stats?.top_receptors.map((r) => (
                <tr key={r.h_sid} className="aie-table-row">
                  <td className="hmac-id">{r.h_sid.slice(0, 8)}...</td>
                  <td>
                    <div className="exergy-stat">
                      <span className="exergy-percent">{r.exergy}%</span>
                      <div className="exergy-bar"><div className="exergy-fill" style={{ width: `${r.exergy}%` }} /></div>
                    </div>
                  </td>
                  <td>{(r.confidence * 100).toFixed(0)}%</td>
                  <td><span className="tag-neutral">{r.class}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="aie-card">
          <div className="aie-card-sub">
            CONTENT PULSE [HVA_ACTIVATION]
          </div>
          <div className="pulse-list">
            {Object.entries(stats?.content_pulse || {}).map(([type, count]) => (
              <div key={type} className="pulse-item">
                <span className="pulse-label">/POSTS/{type.toUpperCase()}</span>
                <span className="pulse-value">{count}</span>
              </div>
            ))}
          </div>

          <div className="noise-panel">
            <div className="noise-header">
              MACHINE NOISE FILTER
            </div>
            {Object.entries(stats?.classes || {})
              .filter(([c]) => c !== 'human_likely')
              .map(([c, count]) => (
                <div key={c} className="noise-item">
                  <span>{c.toUpperCase()}</span>
                  <span>{count}</span>
                </div>
              ))}
          </div>
        </div>
      </div>
    </div>
  );
};
