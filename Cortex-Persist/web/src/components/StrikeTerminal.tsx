import React, { useState, useEffect, useRef } from 'react';
import './StrikeTerminal.css';
import { sonic } from '../utils/SonicService';

interface StrikeEvent {
  type: 'STRIKE' | 'INFO' | 'SUCCESS' | 'ERROR';
  message: string;
  op_id?: number;
}

interface StrikeTerminalProps {
  factId?: number;
  target?: string;
  onClose: () => void;
}

export const StrikeTerminal: React.FC<StrikeTerminalProps> = ({ factId, target, onClose }) => {
  const [logs, setLogs] = useState<StrikeEvent[]>([]);
  const [isExecuting, setIsExecuting] = useState(false);
  const logEndRef = useRef<HTMLDivElement>(null);
  const meterRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (target && factId) {
      startStrike(target, factId);
    }
  }, [target, factId]);

  useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [logs]);

  useEffect(() => {
    if (meterRef.current) {
      meterRef.current.style.width = isExecuting ? '85%' : '0%';
    }
  }, [isExecuting]);

  const startStrike = async (strikeTarget: string, causeId: number) => {
    setIsExecuting(true);
    setLogs([{ type: 'INFO', message: `initializing strike sequence on ${strikeTarget}...` }]);
    sonic.playClick('deploy');

    try {
      const response = await fetch('/api/strike/execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ target: strikeTarget, fact_id: causeId })
      });

      if (!response.ok) throw new Error('LAUNCH_FAILURE');

      // Listen to SSE
      const eventSource = new EventSource('/api/strike/events');
      
      eventSource.onmessage = (event) => {
        const data: StrikeEvent = JSON.parse(event.data);
        setLogs(prev => [...prev, data]);
        
        if (data.type === 'SUCCESS' || data.type === 'ERROR') {
          setIsExecuting(false);
          eventSource.close();
          if (data.type === 'SUCCESS') sonic.playClick('deploy');
        }
      };

      eventSource.onerror = () => {
        setLogs(prev => [...prev, { type: 'ERROR', message: 'SSE_LINK_BROKEN: RECONNECT_PROTOCOL_INITIATED' }]);
        eventSource.close();
        setIsExecuting(false);
      };

    } catch (error) {
      setLogs(prev => [...prev, { type: 'ERROR', message: `CRITICAL_FAILURE: ${error}` }]);
      setIsExecuting(false);
      sonic.playClick('error');
    }
  };

  return (
    <div className="strike-terminal">
      <div className="strike-terminal-container">
        <div className="terminal-header">
          <div className="header-status">
            <span className={`status-dot ${isExecuting ? 'active' : ''}`}></span>
            <span className="source-label">genesis_extractor_v8.0</span>
          </div>
          <div className="header-target">target: {target || 'undefined'}</div>
          <button className="close-btn" onClick={onClose}>cancel</button>
        </div>
        
        <div className="terminal-body">
          {logs.map((log, i) => (
            <div key={i} className={`log-entry ${log.type.toLowerCase()}`}>
              <span className="timestamp">[{new Date().toLocaleTimeString().toLowerCase()}]</span>
              <span className="type">{log.type.toLowerCase()}:</span>
              <span className="message">{log.message.toLowerCase()}</span>
            </div>
          ))}
          <div ref={logEndRef} />
        </div>

        <div className="terminal-footer">
          <div className="exergy-meter">
            <div className="meter-label">exergy_flow</div>
            <div className="meter-bar">
              <div className="bar-fill" ref={meterRef}></div>
            </div>
          </div>
          <div className="auth-stamp">c5-real_qualified</div>
        </div>
      </div>
    </div>
  );
};
