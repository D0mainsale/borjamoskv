import React from 'react';
import './SovereignHeader.css';
import { MagneticWrapper } from './common/MagneticWrapper';
import { useStrategy } from '../contexts/StrategyContext';
import { Zone } from '../types/sovereign';

interface SovereignHeaderProps {
  isAbueloMode?: boolean;
  onToggleAbuelo?: () => void;
  showTacticalMap: boolean;
  setShowTacticalMap: (show: boolean) => void;
  showAudienceIntelligence: boolean;
  setShowAudienceIntelligence: (show: boolean) => void;
  showTelemetry: boolean;
  setShowTelemetry: (show: boolean) => void;
  isGuardActive: boolean;
  toggleGuard: () => void;
  sovereignHandle?: string | null;
}

export const SovereignHeader: React.FC<SovereignHeaderProps> = ({ 
  isAbueloMode, onToggleAbuelo, showTacticalMap, setShowTacticalMap, 
  showAudienceIntelligence, setShowAudienceIntelligence, 
  showTelemetry, setShowTelemetry, isGuardActive, toggleGuard,
  sovereignHandle
}) => {
  const {
    persistMode, sealedFacts, factCount, exergyLevel, isStressed,
    governorMetrics, yieldData, internalAuditFeed, equilibrium, setEquilibrium,
    measuredEntropy, pidOutput, stabilityHistory, setIsStressed
  } = useStrategy();

  const headerRef = React.useRef<HTMLElement>(null);
  const zone: Zone = equilibrium < 35 ? 'CONSOLIDACIÓN' : equilibrium > 65 ? 'DIVERGENCIA' : 'EQUILIBRIO';

    React.useLayoutEffect(() => {
    if (!headerRef.current) return;

    if (governorMetrics) {
      const semantic = Math.min(governorMetrics.semantic_pressure * 100, 100);
      const thermo = Math.min(governorMetrics.thermodynamic_pressure * 100, 100);
      headerRef.current.style.setProperty('--semantic-width', `${semantic}%`);
      headerRef.current.style.setProperty('--thermo-width', `${thermo}%`);
    }

    headerRef.current.style.setProperty(
      '--spark-stroke',
      isStressed ? '#E52B2B' : '#2BE58B'
    );
  }, [governorMetrics, isStressed]);

  return (
    <header ref={headerRef} className="dashboard-header-minimal">
      <div className="header-top-line">
        <MagneticWrapper>
          <div className="header-brand-archi">
            {sovereignHandle ? `@${sovereignHandle}` : 'agents.archi'}
          </div>
        </MagneticWrapper>
        
        <div className="header-nav-pill">
          <MagneticWrapper>
            <button 
              className={`nav-item-btn ${showTacticalMap ? 'active' : ''}`}
              onClick={() => setShowTacticalMap(!showTacticalMap)}
            >
              map
            </button>
          </MagneticWrapper>
          <MagneticWrapper>
            <button 
              className={`nav-item-btn ${showAudienceIntelligence ? 'active' : ''}`}
              onClick={() => setShowAudienceIntelligence(!showAudienceIntelligence)}
            >
              intel
            </button>
          </MagneticWrapper>
          <MagneticWrapper>
            <button 
              className={`nav-item-btn ${showTelemetry ? 'active' : ''}`}
              onClick={() => setShowTelemetry(!showTelemetry)}
            >
              telemetry
            </button>
          </MagneticWrapper>
        </div>

        <div className="header-actions-minimal">
          <MagneticWrapper>
            <div className="guard-capsule">
              <span className={`guard-status-dot ${isGuardActive ? 'active' : 'warning'}`}></span>
              <button className="guard-btn-text" onClick={toggleGuard}>
                {isGuardActive ? 'protected' : 'unshielded'}
              </button>
            </div>
          </MagneticWrapper>
          <MagneticWrapper>
            <button className="abuelo-btn-minimal" onClick={onToggleAbuelo}>
              {isAbueloMode ? 'mode: h' : 'mode: a'}
            </button>
          </MagneticWrapper>
        </div>
      </div>

      <div className="header-persist-strip">
        <div className="persist-label-minimal">c5-real operative substrate</div>
        <div className="persist-stats-minimal">
          <span className="stat-unit">∴ {sealedFacts} sealed</span>
          <span className="stat-unit">∴ {factCount} facts</span>
          <span className={`persist-mode-tag ${persistMode.toLowerCase()}`}>{persistMode.toLowerCase()}</span>
        </div>
      </div>
    </header>
  );
};
