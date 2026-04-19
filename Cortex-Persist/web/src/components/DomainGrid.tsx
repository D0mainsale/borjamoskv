import React from 'react';
import { DomainConfig, domains } from '../data/domains';

interface DomainGridProps {
  activeDomain: string | null;
  setActiveDomain: (id: string | null) => void;
  isGuardActive: boolean;
  deploymentStatus: Record<string, string>;
  mythosData: any;
  vanguardData: any;
  handleStellarStrike: () => void;
  onDeployClick: (domain: DomainConfig) => void;
  sonic: any;
}

export const DomainGrid: React.FC<DomainGridProps> = ({
  activeDomain, setActiveDomain, isGuardActive, deploymentStatus, 
  mythosData, vanguardData, handleStellarStrike, 
  onDeployClick, sonic
}) => {
  return (
    <div className={`domain-grid ${isGuardActive ? 'sovereign-mesh' : ''}`}>
      {domains.map((domain) => (
        <div
          key={domain.id}
          className={`domain-card ${activeDomain === domain.id ? 'active' : ''} ${domain.id === 'cybersec' ? 'critical' : ''}`}
          data-domain={domain.id}
          onMouseEnter={() => {
            setActiveDomain(domain.id);
            sonic.playClick('hover');
          }}
          onMouseLeave={() => setActiveDomain(null)}
        >
          <div className="hw-corner hw-tl"></div>
          <div className="hw-corner hw-tr"></div>
          <div className="hw-corner hw-bl"></div>
          <div className="hw-corner hw-br"></div>

          <div className="card-border"></div>
          <div className="card-content">
            <span className="domain-icon">
              {domain.icon}
            </span>
            <h3>
              {domain.title}
            </h3>
            <p>{domain.description}</p>

            <button
              className={`deploy-btn ${deploymentStatus[domain.id] ? 'loading' : ''}`}
              disabled={!!deploymentStatus[domain.id]}
              onClick={(e) => {
                e.stopPropagation();
                onDeployClick(domain);
              }}
            >
              {deploymentStatus[domain.id] || (
                domain.id === 'cybersec' ? 'CONSOLA_DE_ATAQUE' : 
                domain.id === 'legion-100' ? 'MONITOR_DE_LEGION' : 
                domain.id === 'moskv-nexus' ? 'FORJA_DE_NEXO' :
                domain.id === 'ai-ml' ? 'AUTO_APRENDIZAJE' :
                domain.id === 'sovereign-agents' ? 'COMUNA_AGÉNTICA' :
                domain.id === 'exfiltration-c5' ? 'UNIDAD_DE_EXFILTRACIÓN' :
                'DESPLEGAR_AGENTE'
              )}
            </button>

            {domain.id === 'cybersec' && mythosData && (
              <div className="domain-live-metrics">
                <div className="metric-tag">
                  <span className="tag-label">FASE</span>
                  <span className="tag-value">{mythosData.state_machine.current_phase}</span>
                </div>
                <div className="metric-tag">
                  <span className="tag-label">MISIÓN_ACTIVA</span>
                  <span className="tag-value pulsing-red">
                    {mythosData.state_machine.milestones.find((m: any) => m.status === 'IN_PROGRESS')?.id || 'NINGUNA'}
                  </span>
                </div>
              </div>
            )}

            <div className="scan-line"></div>
          </div>
        </div>
      ))}

      {vanguardData && (
        <div className="domain-card vanguard-monitor">
          <div className="card-content">
            <span className="domain-icon">◈</span>
            <h3>MONITOR_VANGUARDIA</h3>
            <div className="vanguard-protocol-list">
              {Object.entries(vanguardData).map(([name, entry]: [string, any]) => (
                <div key={name} className="vanguard-protocol-item">
                  <div className="protocol-info">
                    <span className="protocol-name">{name.toUpperCase()}</span>
                    <span className={`protocol-status ${entry.status.toLowerCase()}`}>
                      {entry.status}
                    </span>
                  </div>
                  {entry.status === 'SINGULARITY' && (
                    <button
                      className="stellar-strike-btn"
                      onClick={handleStellarStrike}
                    >
                      FRACTURA
                    </button>
                  )}
                </div>
              ))}
            </div>
            <div className="scan-line"></div>
          </div>
        </div>
      )}
    </div>
  );
};
