import React from 'react';
import { useStrategy } from '../contexts/StrategyContext';
import './LegionMonitor.css';

/**
 * LegionMonitor ◈ AOS v6.0
 * Visualización táctica del enjambre agéntico.
 * Implementa la §12 de la arquitectura soberana.
 */
import { MagneticWrapper } from './common/MagneticWrapper';

export const LegionMonitor: React.FC<{ onClose?: () => void }> = ({ onClose }) => {
  const { legion, swarmStats, p911State } = useStrategy();

  if (!legion || legion.length === 0) {
    return (
      <div className="legion-monitor-empty">
        <span className="blink">◈ BUSCANDO ENJAMBRE...</span>
      </div>
    );
  }

  return (
    <div className={`legion-monitor-container ${p911State === 'EMERGENCIA' ? 'emergency-glow' : ''}`}>
      <div className="legion-header-minimal">
        <div className="legion-branding">
          <span className="legion-symbol">∴</span> legion_swarm_v6
        </div>
        <div className="legion-metrics-pill">
          <span>elite_units: {legion.length}</span>
          <span>total_swarm: {swarmStats?.total_count || '10,000'}</span>
          <span>exergia_avg: {((swarmStats?.avg_exergy || 0.99) * 100).toFixed(1)}%</span>
        </div>
        {onClose && (
          <MagneticWrapper>
            <button className="legion-close-minimal" onClick={onClose}>close</button>
          </MagneticWrapper>
        )}
      </div>

      <div className="legion-main-viewport">
        {/* ELITE SQUADRON (High-Fidelity) */}
        <div className="legion-elite-grid">
          {legion.map((agent) => (
            <MagneticWrapper key={agent.id}>
              <div className={`legion-capsule ${agent.status === 'COMPLETED' ? 'is-complete' : ''}`}>
                <div className="capsule-header">
                  <div className="capsule-id">elite_{agent.id.toString().padStart(3, '0')}</div>
                  <div className="capsule-role">{agent.role.toLowerCase()}</div>
                </div>
                <div className="capsule-task">{agent.task.toLowerCase()}</div>
                
                <div className="mini-exergy-track">
                  <div
                    className="mini-exergy-fill"
                    style={{
                      '--exergy-width': `${agent.exergy * 100}%`,
                      '--exergy-color': getExergyColor(agent.exergy)
                    } as React.CSSProperties}
                  ></div>
                </div>

                <div className="capsule-footer-minimal">
                  <span className="pulse-slow">{agent.status.toLowerCase()}</span>
                  <span>{(agent.progress * 100).toFixed(0)}%</span>
                </div>
              </div>
            </MagneticWrapper>
          ))}
        </div>

        {/* SWARM VOID (High-Density / Virtualized) */}
        <div className="swarm-void-container">
          <div className="void-header">
            <span className="void-label">∴ virtual_swarm_void [10k_nodes]</span>
            <div className="void-stats">
              <span>load: {swarmStats?.load_factor || '0.12'}</span>
              <span>sync: {swarmStats?.sync_integrity || '99.8%'}</span>
            </div>
          </div>
          <div className="swarm-void-grid">
            {/* 10,000 points represented by a CSS noise/grid pattern and sampled particles */}
            <div className="void-noise-substrate"></div>
            {Array.from({ length: 48 }).map((_, i) => (
              <div
                key={i}
                className="void-particle"
                style={{
                  '--particle-opacity': 0.1 + Math.random() * 0.4,
                  '--particle-delay': `${Math.random() * 5}s`
                } as React.CSSProperties}
              ></div>
            ))}
          </div>
        </div>
      </div>

      <footer className="legion-footer-ether">
        <div className="status-indicator">
          <span className="dot"></span> {p911State.toLowerCase()}
        </div>
        <div className="legal-stamp">c5-real operative substrate</div>
      </footer>
    </div>
  );
};

// Utilidad de Color para Exergía
const getExergyColor = (exergy: number) => {
  if (exergy > 0.95) return '#2BE58B'; // Emerald
  if (exergy > 0.85) return '#2B3BE5'; // CORTEX Blue
  return '#E52B2B'; // Blood Red
};

export default LegionMonitor;
