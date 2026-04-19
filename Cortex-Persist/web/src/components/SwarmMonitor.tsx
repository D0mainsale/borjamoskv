import React, { useEffect, useRef } from 'react';
import './SwarmMonitor.css';

interface Agent {
  id: string;
  role: string;
  task: string;
  exergy: number;
  progress: number;
  status: string;
  uptime: number;
}

interface SwarmMonitorProps {
  agents: Agent[];
  onClose: () => void;
}

export const SwarmMonitor: React.FC<SwarmMonitorProps> = ({ agents, onClose }) => {
  const tableRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (tableRef.current) {
      const rows = tableRef.current.querySelectorAll('.agent-row');
      rows.forEach((row, index) => {
        const agent = agents[index];
        if (agent) {
          const fill = row.querySelector('.progress-fill') as HTMLDivElement;
          if (fill) {
            fill.style.width = `${agent.progress * 100}%`;
          }
        }
      });
    }
  }, [agents]);

  return (
    <div className="swarm-monitor-overlay">
      <div className="swarm-monitor-content mica-texture">
        <div className="swarm-header">
          <div className="swarm-title">
            <span className="kernel-badge">AOS_LEGION_v6.0</span>
            <h2>ORQUESTADOR DE ENJAMBRES</h2>
          </div>
          <button className="close-btn" onClick={onClose}>✕</button>
        </div>

        <div className="swarm-stats-bar">
          <div className="stat-item">
            <span className="label">AGENTES_ACTIVOS</span>
            <span className="value">{agents.length}</span>
          </div>
          <div className="stat-item">
            <span className="label">EXERGÍA_PROMEDIO</span>
            <span className="value">
              {(agents.reduce((acc, a) => acc + a.exergy, 0) / (agents.length || 1) * 100).toFixed(1)}%
            </span>
          </div>
          <div className="stat-item">
            <span className="label">ESTADO_ENJAMBRE</span>
            <span className="value status-nominal">NOMINAL</span>
          </div>
        </div>

        <div className="agent-list-table">
          <div className="table-header">
            <span>ID_AGENTE</span>
            <span>ROL</span>
            <span>TAREA_ACTUAL</span>
            <span>PROGRESO</span>
            <span>EXERGÍA</span>
            <span>UPTIME</span>
          </div>
          <div className="table-body" ref={tableRef}>
            {agents.map(agent => (
              <div key={agent.id} className="agent-row">
                <span className="agent-id">{agent.id}</span>
                <span className={`agent-role role-${agent.role.toLowerCase()}`}>
                  {agent.role}
                </span>
                <span className="agent-task">{agent.task}</span>
                <div className="agent-progress">
                  <div className="progress-track">
                    <div 
                      className="progress-fill" 
                      data-progress={agent.progress * 100}
                    ></div>
                  </div>
                  <span className="progress-pct">{(agent.progress * 100).toFixed(0)}%</span>
                </div>
                <span className="agent-exergy">
                  {(agent.exergy * 100).toFixed(1)}%
                </span>
                <span className="agent-uptime">{agent.uptime}s</span>
              </div>
            ))}
          </div>
        </div>

        <div className="swarm-footer">
          <div className="footer-line"></div>
          <span className="footer-tag">LEGION_SUBSYSTEM_OPERATIONAL // NO_ENTROPY_DETECTED</span>
        </div>
      </div>
    </div>
  );
};
