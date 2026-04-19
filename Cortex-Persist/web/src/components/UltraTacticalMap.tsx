import React, { useMemo, useState, useEffect } from 'react';
import './UltraTacticalMap.css';

interface DomainNode {
  id: string;
  name: string;
  x: number;
  y: number;
  color: string;
}

const DOMAIN_NODES: DomainNode[] = [
  { id: 'ai-ml', name: 'ai_ml_substrate', x: 25, y: 25, color: '#fff' },
  { id: 'cybersec', name: 'cybersec_vectors', x: 45, y: 65, color: '#E52B2B' },
  { id: 'moskv-nexus', name: 'moskv_nexus', x: 65, y: 25, color: '#fff' },
  { id: 'sovereign-agents', name: 'sovereign_hub', x: 75, y: 55, color: '#fff' },
  { id: 'exfiltration-c5', name: 'exfiltration_c5', x: 55, y: 85, color: '#fff' },
  { id: 'legion-100', name: 'legion_swarm', x: 15, y: 75, color: '#2BE58B' },
  { id: 'sonic-nexus', name: 'sonic_intelligence', x: 35, y: 45, color: '#fff' },
];

interface ReconFinding {
  type: string;
  node_id: number;
  msg: string;
  timestamp: number;
}

interface UltraTacticalMapProps {
  activeAgents: number[];
  measuredEntropy: number;
  isStrikeActive: boolean;
  persistMode: string;
  sealedFacts: number;
  factCount: number;
  findings: ReconFinding[]; // Real-time recon findings
  legionAgents?: any[]; // Dynamic swarm agents
  onNodeClick?: (id: string) => void;
  onClose?: () => void;
}

export const UltraTacticalMap: React.FC<UltraTacticalMapProps> = ({
  activeAgents,
  measuredEntropy,
  isStrikeActive,
  persistMode,
  sealedFacts,
  factCount,
  findings: newFindings,
  legionAgents = [],
  onNodeClick,
  onClose
}) => {
  const mapRef = React.useRef<HTMLDivElement>(null);
  const [activeFindings, setActiveFindings] = useState<(ReconFinding & { id: string, opacity: number })[]>([]);

  React.useLayoutEffect(() => {
    if (!mapRef.current) return;
    const glitchFilter = measuredEntropy > 0.4 
      ? `blur(${measuredEntropy * 1}px) hue-rotate(${measuredEntropy * 20}deg)` 
      : 'none';
    mapRef.current.style.setProperty('--glitch-filter', glitchFilter);
  }, [measuredEntropy]);

  // Veracity Glow radius based on sealed facts (limit to 40% of map)
  const veracityRadius = Math.min(10 + (sealedFacts * 0.5), 40);

  // Manage findings with TTL
  useEffect(() => {
    if (newFindings && newFindings.length > 0) {
      const formatted = newFindings.map(f => ({
        ...f,
        id: `${f.type}-${f.timestamp}-${Math.random()}`,
        opacity: 1
      }));
      setActiveFindings(prev => [...prev, ...formatted].slice(-10)); // Keep last 10
    }
  }, [newFindings]);

  // Fade out findings
  useEffect(() => {
    const timer = setInterval(() => {
      setActiveFindings(prev => 
        prev
          .map(f => ({ ...f, opacity: f.opacity - 0.05 }))
          .filter(f => f.opacity > 0)
      );
    }, 200);
    return () => clearInterval(timer);
  }, []);
  
  // Synergy Network
  const connections = useMemo(() => {
    return [
      [DOMAIN_NODES[0], DOMAIN_NODES[2]],
      [DOMAIN_NODES[2], DOMAIN_NODES[3]],
      [DOMAIN_NODES[1], DOMAIN_NODES[3]],
      [DOMAIN_NODES[3], DOMAIN_NODES[4]],
      [DOMAIN_NODES[5], DOMAIN_NODES[6]],
      [DOMAIN_NODES[6], DOMAIN_NODES[0]],
    ];
  }, []);

  const agentSentries = useMemo(() => {
    // If we have real legion data, use it. Otherwise fallback to generic activeAgents logic.
    if (legionAgents && legionAgents.length > 0) {
      return legionAgents.map((agent, i) => {
        const idNum = parseInt(agent.id.replace('LEGION-', '')) || i;
        const targetNode = DOMAIN_NODES[idNum % DOMAIN_NODES.length];
        const offset = (Math.sin(idNum + Date.now() / 1500) * 1.5) + 1;
        return {
          id: agent.id,
          x: targetNode.x + (Math.cos(idNum) * 4 * offset),
          y: targetNode.y + (Math.sin(idNum) * 4 * offset),
          role: agent.role.toLowerCase()
        };
      });
    }

    return activeAgents.slice(0, 50).map((id) => {
      const targetNode = DOMAIN_NODES[id % DOMAIN_NODES.length];
      const offset = (Math.sin(id + Date.now() / 1500) * 1.5) + 1;
      return {
        id,
        x: targetNode.x + (Math.cos(id) * 4 * offset),
        y: targetNode.y + (Math.sin(id) * 4 * offset),
        role: 'generic'
      };
    });
  }, [legionAgents, activeAgents]);


  return (
    <div 
      ref={mapRef}
      className={`ultra-tactical-map ${isStrikeActive ? 'strike-interference' : ''}`} 
    >
      <div className="map-header-minimal">
        <div className="map-branding">
          <span className="map-symbol">∴</span> tactical_atlas_v6
        </div>
        <button className="map-close-minimal" onClick={onClose}>close</button>
      </div>
      
      <div className="map-grid-overlay"></div>
      <div className="map-ambience"></div>
      
      <svg viewBox="0 0 100 100" className="map-svg-canvas">
        <defs>
          <radialGradient id="veracityGlow" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="#00F0FF" stopOpacity={0.15} />
            <stop offset="100%" stopColor="#00F0FF" stopOpacity={0} />
          </radialGradient>
        </defs>

        {/* Sovereign Veracity Layer */}
        <circle 
          cx={65} cy={25} r={veracityRadius} 
          fill="url(#veracityGlow)" 
          className="veracity-field"
        />

        {/* Connection Lines */}
        <g className="synergy-network">
          {connections.map(([a, b], i) => (
            <line 
              key={i} 
              x1={a.x} y1={a.y} x2={b.x} y2={b.y} 
              className={`flow-line ${isStrikeActive ? 'unstable' : ''}`}
            />
          ))}
        </g>

        {/* Event Markers (Active Recon) */}
        <g className="recon-events">
          {activeFindings.map((f) => {
            const node = DOMAIN_NODES[f.node_id % DOMAIN_NODES.length];
            return (
              <g 
                key={f.id} 
                className="finding-marker" 
                data-opacity={Math.round(f.opacity * 10) / 10}
              >
                <circle cx={node.x} cy={node.y} r="0.5" fill="var(--laser-green)" className="ping" />
                <circle cx={node.x} cy={node.y} r="3" stroke="var(--laser-green)" fill="none" className="ripple" />
                <text x={node.x + 2} y={node.y - 2} className="finding-text">
                  [{f.type}] {f.msg.split(' ').pop()}
                </text>
              </g>
            );
          })}
        </g>

        {/* Nodes */}
        <g className="domain-nodes">
          {DOMAIN_NODES.map((node) => {
            const isAuthoritative = node.id === 'moskv-nexus';
            return (
              <g 
                key={node.id} 
                className={`node-group ${node.id} ${isAuthoritative ? 'authoritative' : ''}`}
                onClick={() => onNodeClick?.(node.id)}
                data-node-id={node.id}
              >
                {/* Persistence Aura ripple */}
                {sealedFacts > 0 && (
                  <circle 
                    cx={node.x} cy={node.y} r={2}
                    className="persistence-aura"
                  />
                )}
                <circle 
                  cx={node.x} cy={node.y} r="1.8" 
                  className="node-core"
                />
                <circle 
                  cx={node.x} cy={node.y} r="3" 
                  className="node-pulse"
                />
                <text x={node.x + 3} y={node.y + 1} className="node-label">
                  {node.name}
                </text>
              </g>
            );
          })}
        </g>

        {/* Agent Sentries */}
        <g className="agent-sentries">
          {agentSentries.map((agent) => (
            <circle 
              key={agent.id}
              cx={agent.x} cy={agent.y} r="0.6"
              className={`sentry-dot role-${agent.role}`}
            />
          ))}
        </g>
      </svg>

      <div className="map-hud-ether">
        <div className="hud-group">
          <span className="hud-unit">grid_ops // sector_04</span>
          <span className="hud-unit laser-green">active_intel // [live]</span>
        </div>
        <div className="hud-group text-right">
          <span className="hud-unit">sealed: {sealedFacts}</span>
          <span className="hud-unit gold">total: {factCount}</span>
        </div>
      </div>
    </div>
  );
};
