import React, { useState, useEffect, useRef } from 'react';
import './HomeostasisMonitor.css';

interface HomeostasisData {
  exergia_media: number;
  entropia_sistema: number;
  indice_estabilidad: number;
  pendientes: number;
  fallidas: number;
  rendimiento_c5: number;
}

export const HomeostasisMonitor: React.FC = () => {
  const [data, setData] = useState<HomeostasisData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const exergyRef = useRef<HTMLDivElement>(null);
  const stabilityRef = useRef<SVGPathElement>(null);

  const fetchStatus = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/homeostasis/status');
      const result = await response.json();
      if (result.status === 'SUCCESS') {
        setData(result.homeostasis);
        setError(null);
      } else {
        setError('FUERA_DE_LÍNEA');
      }
    } catch (err) {
      setError('ERROR_DE_CONEXIÓN');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 5000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (data) {
      if (exergyRef.current) {
        exergyRef.current.style.setProperty('--fill-width', `${data.exergia_media * 100}%`);
      }
      if (stabilityRef.current) {
        stabilityRef.current.style.setProperty('--stroke-dash', `${data.indice_estabilidad * 100}`);
      }
    }
  }, [data]);

  if (loading && !data) return <div className="homeostasis-loading">CALIBRANDO...</div>;

  return (
    <div className={`homeostasis-root ${error ? 'offline' : ''}`}>
      <div className="homeostasis-header">
        <div className="pulse-indicator"></div>
        <span className="label">thermodynamic homeostasis</span>
        <span className="status-badge">{error ? 'disruption' : 'stable'}</span>
      </div>

      <div className="metrics-grid">
        <div className="metric-box exergy">
          <div className="metric-label">average exergy (w)</div>
          <div className="metric-value">{(data?.exergia_media || 0).toFixed(3)}</div>
          <div className="metric-bar-container">
            <div 
              ref={exergyRef}
              className="metric-bar" 
            ></div>
          </div>
        </div>

        <div className="metric-box entropy">
          <div className="metric-label">entropy (s)</div>
          <div className="metric-value">{(data?.entropia_sistema || 0).toFixed(3)}</div>
          <div className="metric-sub">
            <span className="sub-val">δp: {data?.pendientes}</span>
            <span className="sub-val">δf: {data?.fallidas}</span>
          </div>
        </div>

        <div className="metric-box stability">
          <div className="metric-label">stability (ω)</div>
          <div className="metric-value-large">
            {( (data?.indice_estabilidad || 0) * 100).toFixed(1)}%
          </div>
          <svg className="stability-ring" viewBox="0 0 36 36">
            <path
              className="ring-bg"
              d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
            />
            <path
              ref={stabilityRef}
              className="ring-fill"
              d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
            />
          </svg>
        </div>

        <div className="metric-box yield-c5">
          <div className="metric-label">c5-real yield</div>
          <div className="metric-value-glow">
            ${(data?.rendimiento_c5 || 0).toLocaleString()}
          </div>
          <div className="yield-status">
            <span className="blink-dot"></span>
            exfiltrating...
          </div>
        </div>
      </div>

      <div className="homeostasis-footer">
        <div className="timestamp">{new Date().toLocaleTimeString()} [utc]</div>
        <div className="engine-v">cortex.core_v9.0</div>
      </div>
    </div>
  );
};
