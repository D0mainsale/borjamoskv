import React from 'react';

interface StabilityMetrics {
  peak: number;
  crest: number;
  harsh: number;
}

interface StabilityPolicy {
  ceiling: number;
  threshold: number;
  ratio: number;
}

interface StabilityData {
  mode: string;
  u: number;
  rule: string;
  metrics: StabilityMetrics;
  policy: StabilityPolicy;
  ts: number;
}

interface StabilityHUDProps {
  data: StabilityData | null;
  active: boolean;
}

export const StabilityHUD: React.FC<StabilityHUDProps> = ({ data, active }) => {
  const hudRef = React.useRef<HTMLDivElement>(null);

  React.useLayoutEffect(() => {
    if (!hudRef.current || !data) return;
    hudRef.current.style.setProperty('--harsh-progress', `${data.metrics.harsh * 100}%`);
    hudRef.current.style.setProperty('--intensity-width', `${data.u * 100}%`);
  }, [data]);

  if (!active || !data) return null;

  const { mode, u, rule, metrics, policy } = data;

  const getModeLabel = (m: string) => {
    if (m === 'RED') return 'EVASION_CRITICAL';
    if (m === 'YELLOW') return 'MASTERING_PRESSURE';
    return 'NOMINAL_MASTER';
  };

  return (
    <div 
      ref={hudRef}
      className={`stability-hud shadow-portal ${active ? 'active' : ''}`} 
      data-mode={mode}
    >
      <div className="hud-scanner"></div>
      
      <header className="hud-header">
        <div className="header-top">
          <div className="system-id">GOVERNOR_v2.2_SONIC</div>
          <div className={`mode-badge ${mode.toLowerCase()}`}>{getModeLabel(mode)}</div>
        </div>
        <div className="pulsar-group">
          <div className="pulsar-dot"></div>
          <div className="rule-label">REGLA: {rule}</div>
        </div>
      </header>

      <div className="hud-grid">
        {/* Signal Layer: Audio Features */}
        <div className="hud-section metrics">
          <div className="metric-row">
            <span className="label">PICO_REAL</span>
            <span className={`value ${metrics.peak > 1.0 ? 'pulse-red' : 'gold-glow'}`}>
              {metrics.peak.toFixed(2)} dB
            </span>
          </div>
          <div className="metric-row">
            <span className="label">FACTOR_CRESTA</span>
            <span className="value">{metrics.crest.toFixed(1)}</span>
          </div>
          <div className="metric-row">
            <span className="label">ASPEREZA</span>
            <div className={`progress-bar ${metrics.harsh > 0.8 ? 'warning' : ''}`}></div>
          </div>
        </div>

        {/* Action Layer: Mastering Policy */}
        <div className="hud-section policy">
          <div className="policy-header">POLÍTICA_MASTER</div>
          <div className="policy-row">
            <span className="label">TECHO:</span>
            <span className="value">{policy.ceiling.toFixed(1)} dB</span>
          </div>
          <div className="policy-row">
            <span className="label">UMBRAL:</span>
            <span className="value">{policy.threshold.toFixed(1)} dB</span>
          </div>
          <div className="policy-row">
            <span className="label">PROPORCIÓN:</span>
            <span className="value">{policy.ratio.toFixed(1)}:1</span>
          </div>
        </div>
      </div>

      <footer className="hud-footer">
        <div className="intensity-track">
          <div className="track-fill"></div>
          <div className="intensity-label">INTENSIDAD_TOTAL: {(u * 100).toFixed(1)}%</div>
        </div>
      </footer>
    </div>
  );
};
