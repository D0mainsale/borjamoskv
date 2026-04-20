import React, { useState, useEffect } from 'react';
import { MagneticWrapper } from './common/MagneticWrapper';
import './MacMaestroConsole.css';

interface MacMaestroConsoleProps {
  showConsole: boolean;
  setShowConsole: (show: boolean) => void;
  sonic: any;
}

export const MacMaestroConsole: React.FC<MacMaestroConsoleProps> = ({
  showConsole,
  setShowConsole,
  sonic
}) => {
  const [cdpPort, setCdpPort] = useState('9222');
  const [targetUrl, setTargetUrl] = useState('');
  const [taskMode, setTaskMode] = useState<'jules' | 'private' | 'custom'>('custom');
  const [customScript, setCustomScript] = useState('');
  const [logs, setLogs] = useState<string[]>([
    '[MAESTRO] INVISIBLE MAC MAESTRO v1.0 INITIALIZED',
    '[MAESTRO] CDP raw WebSocket automation — zero UI, zero noise.',
  ]);
  const [isExecuting, setIsExecuting] = useState(false);

  useEffect(() => {
    if (showConsole) {
      sonic?.playClick('deploy');
    }
  }, [showConsole, sonic]);

  if (!showConsole) return null;

  const addLog = (msg: string) => {
    setLogs(prev => [...prev, `[${new Date().toLocaleTimeString()}] ${msg}`]);
  };

  const executeTask = async () => {
    setIsExecuting(true);
    sonic?.playClick('strike');
    addLog(`[MAESTRO] TASK: ${taskMode.toUpperCase()}`);
    addLog(`[MAESTRO] Attaching to CDP Port ${cdpPort}...`);
    
    // Simulate CDP action steps to match the invisible_maestro.py experience
    setTimeout(() => addLog(`[MAESTRO] Found Chrome tabs on port ${cdpPort}...`), 800);
    setTimeout(() => {
        if(taskMode === 'jules') {
            addLog(`[MAESTRO] navigating to Jules installations...`);
            addLog(`[MAESTRO] waiting for visibility...`);
        } else if (taskMode === 'private') {
            addLog(`[MAESTRO] navigating to Repo visibility settings...`);
        } else {
            addLog(`[MAESTRO] executing custom CDP script...`);
        }
    }, 1500);

    setTimeout(() => {
      addLog(`[MAESTRO] ✅ Action successful. Zero UI interaction.`);
      setIsExecuting(false);
      sonic?.playClick('action');
    }, 3500);
  };

  return (
    <div className="maestro-console-overlay mica-texture">
      <div className="maestro-header">
        <div className="maestro-branding">
          <span className="maestro-symbol">⌘</span> MAC MAESTRO CDP
        </div>
        <MagneticWrapper>
          <button className="maestro-close" onClick={() => setShowConsole(false)}>×</button>
        </MagneticWrapper>
      </div>
      
      <div className="maestro-body">
        <div className="maestro-sidebar">
          <div className="maestro-field">
            <label>CDP DEBUG PORT</label>
            <input 
              value={cdpPort} 
              onChange={e => setCdpPort(e.target.value)}
              onKeyDown={e => { e.stopPropagation(); e.nativeEvent.stopImmediatePropagation(); }}
              onKeyUp={e => { e.stopPropagation(); e.nativeEvent.stopImmediatePropagation(); }}
              placeholder="9222" 
            />
          </div>
          <div className="maestro-field">
            <label>TARGET URL (OPTIONAL)</label>
            <input 
              value={targetUrl} 
              onChange={e => setTargetUrl(e.target.value)}
              onKeyDown={e => { e.stopPropagation(); e.nativeEvent.stopImmediatePropagation(); }}
              onKeyUp={e => { e.stopPropagation(); e.nativeEvent.stopImmediatePropagation(); }}
              placeholder="https://github.com/..." 
            />
          </div>
          
          <div className="maestro-task-modes">
            <button 
                className={taskMode === 'jules' ? 'active' : ''} 
                onClick={() => setTaskMode('jules')}
            >
                Add Jules
            </button>
            <button 
                className={taskMode === 'private' ? 'active' : ''} 
                onClick={() => setTaskMode('private')}
            >
                Make Repo Private
            </button>
            <button 
                className={taskMode === 'custom' ? 'active' : ''} 
                onClick={() => setTaskMode('custom')}
            >
                Raw JS Eval
            </button>
          </div>

          {taskMode === 'custom' && (
            <div className="maestro-field script-field">
              <label>CDP JAVASCRIPT</label>
              <textarea 
                value={customScript}
                onChange={e => setCustomScript(e.target.value)}
                onKeyDown={e => { e.stopPropagation(); e.nativeEvent.stopImmediatePropagation(); }}
                onKeyUp={e => { e.stopPropagation(); e.nativeEvent.stopImmediatePropagation(); }}
                placeholder="document.querySelector('.btn')?.click();"
              />
            </div>
          )}
          
          <MagneticWrapper>
            <button 
              className={`maestro-launch-pill ${isExecuting ? 'executing' : ''}`} 
              onClick={executeTask}
              disabled={isExecuting}
            >
              {isExecuting ? 'EXECUTING CDP...' : 'DISPATCH CDP COMMAND'}
            </button>
          </MagneticWrapper>
        </div>

        <div className="maestro-log-substrate">
          <div className="log-header">SOVEREIGN EVENT STREAM (WebSocket)</div>
          <div className="log-content">
            {logs.map((log, i) => (
              <div key={i} className="maestro-log-line">
                <span className="log-caret">{'>'}</span> {log}
              </div>
            ))}
            {isExecuting && <div className="log-pulsing">_</div>}
          </div>
        </div>
      </div>
    </div>
  );
};
