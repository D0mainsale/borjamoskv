import React, { useState, useEffect } from 'react';
import './StatusBar.css';

interface Metric {
  label: string;
  value: string;
  unit: string;
  color: string;
}

const INITIAL_METRICS: Metric[] = [
  { label: 'EXERGY', value: '98.4', unit: '%', color: '#2BE58B' },
  { label: 'RECALL@K', value: '92.1', unit: '%', color: '#2B3BE5' },
  { label: 'TOKEN YIELD', value: '67.3', unit: '%', color: '#2B3BE5' },
  { label: 'AMNESIA RISK', value: '0.00', unit: '%', color: '#2BE58B' },
  { label: 'VECTORS', value: '4821', unit: 'facts', color: '#8B2BE5' },
  { label: 'LATENCY', value: '12', unit: 'ms', color: '#2BE58B' },
];

export const StatusBar: React.FC = () => {
  const [metrics, setMetrics] = useState(INITIAL_METRICS);
  const [_tick, setTick] = useState(0);

  // Micro-fluctuation to simulate live telemetry
  useEffect(() => {
    const interval = setInterval(() => {
      setMetrics(prev => prev.map(m => {
        const base = parseFloat(m.value);
        const noise = (Math.random() - 0.5) * 0.4;
        return { ...m, value: Math.max(0, base + noise).toFixed(m.unit === 'ms' || m.unit === 'facts' ? 0 : 1) };
      }));
      setTick(t => t + 1);
    }, 2000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="status-bar">
      <div className="status-bar-brand">
        <span className="status-brand-logo">Ω</span>
        <span className="status-brand-name">CORTEX-PERSIST</span>
        <span className="status-version">v6.5</span>
      </div>

      <div className="status-metrics">
        {metrics.map((m) => (
          <div key={m.label} className="status-metric">
            <span className="metric-label">{m.label}</span>
            <span className="metric-value" style={{ color: m.color }}>
              {m.value}
              <span className="metric-unit">{m.unit}</span>
            </span>
          </div>
        ))}
      </div>

      <div className="status-bar-right">
        <span className="signal-dot"></span>
        <span className="signal-text">SIGNAL C5-REAL</span>
        <span className="status-clock">{new Date().toLocaleTimeString('en-GB')}</span>
      </div>
    </div>
  );
};
