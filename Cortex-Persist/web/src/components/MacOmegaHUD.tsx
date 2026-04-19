import React, { useEffect, useState, useRef, useMemo } from 'react';
import './MacOmegaHUD.css';

interface DOMNode {
  id: string;
  tag: string;
  depth: number;
  x: number;
  y: number;
  z: number;
  opacity: number;
  color: string;
}

// LCG Determinista para posiciones
const lcg = (seed: number) => (Math.imul(seed, 1664525) + 1013904223) | 0;

export const MacOmegaHUD: React.FC<{ active: boolean }> = ({ active }) => {
  const [nodes, setNodes] = useState<DOMNode[]>([]);
  const [telemetry, setTelemetry] = useState({
    exergy: 88.4,
    latency: 4,
    nodesCount: 1492,
    syncActive: true
  });
  const [scanPos, setScanPos] = useState(0);
  const frameRef = useRef(0);
  const containerRef = useRef<HTMLDivElement>(null);

  // Semilla de VSA para replicar constelaciones de Nodos 3D
  const getInitialNodes = useMemo(() => {
    let s = 999983;
    const initial: DOMNode[] = [];
    const tags = ['div', 'span', 'sect', 'art', 'btn', 'inp'];
    for (let i = 0; i < 30; i++) {
      s = lcg(s); const xr = ((s >>> 0) / 0xffffffff) * 100 - 50;
      s = lcg(s); const yr = ((s >>> 0) / 0xffffffff) * 100 - 50;
      s = lcg(s); const zr = ((s >>> 0) / 0xffffffff) * 800 - 400; // Z depth
      s = lcg(s); const isRed = ((s >>> 0) / 0xffffffff) > 0.9;
      
      initial.push({
        id: `node-${i}`,
        tag: tags[i % tags.length],
        depth: (i % 5) + 1,
        x: xr,
        y: yr,
        z: zr,
        opacity: 0,
        color: isRed ? '#E52B2B' : '#2BE58B'
      });
    }
    return initial;
  }, []);

  useEffect(() => {
    if (!active) return;
    
    // Mount initial nodes
    setNodes(getInitialNodes);

    let lastTime = performance.now();

    const animate = (time: number) => {
      const dt = time - lastTime;
      lastTime = time;

      // Dynamic Telemetry Simulation (Silicon Truth)
      if (Math.random() > 0.95) {
        setTelemetry(prev => ({
          ...prev,
          exergy: parseFloat((80 + Math.random() * 20).toFixed(1)),
          latency: Math.floor(2 + Math.random() * 6),
          nodesCount: 1400 + Math.floor(Math.random() * 200)
        }));
      }

      setScanPos(prev => (prev + dt * 0.1) % 100);

      setNodes(prev => prev.map(node => {
        let newZ = node.z + (dt * 1.5); // Move towards camera
        let newOpacity = node.opacity;
        
        // Fade in from distance, fade out near camera
        if (newZ > 300) newOpacity = Math.max(0, newOpacity - 0.05);
        else newOpacity = Math.min(1, newOpacity + 0.02);

        // Reset if passed camera
        if (newZ > 400) {
          newZ = -600;
          newOpacity = 0;
        }

        return { ...node, z: newZ, opacity: newOpacity };
      }));
      frameRef.current = requestAnimationFrame(animate);
    };

    frameRef.current = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(frameRef.current);
  }, [active, getInitialNodes]);

  const fireNotchPing = async () => {
    try {
      fetch('http://localhost:9224/api/notch_ping', { method: 'POST' }).catch(() => {});
      console.log('∴ MAC-CONTROL-Ω: PING NOTCH LED DISPARADO');
    } catch (e) {}
  };

  const hudRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!hudRef.current) return;
    hudRef.current.style.setProperty('--exergy-glow', `${telemetry.exergy / 100}`);
    hudRef.current.style.setProperty('--scan-y', `${scanPos}%`);
  }, [telemetry.exergy, scanPos]);

  if (!active) return null;

  return (
    <div 
      ref={hudRef}
      className="mac-omega-hud-container" 
    >
      <div className="hud-overlay-noise"></div>
      <div className="hud-scan-line"></div>
      <div className="ambilight-emitter top"></div>
      <div className="ambilight-emitter bottom"></div>
      <div className="ambilight-emitter left"></div>
      <div className="ambilight-emitter right"></div>
      
      <div className="hud-header">
        <div className="hud-brand">
          <div className="hud-main-label">
            <span className="hud-icon">Ω</span>
            <span>CONTROL_TOTAL_MÁQUINA</span>
          </div>
          <span className="hud-version">v9.0.0 • SINCRONIZACIÓN_HYDRA [{telemetry.syncActive ? 'ON' : 'OFF'}]</span>
        </div>
        <div className="hud-status">
          <div className="blinking-indicator"></div>
          <span>WEBSOCKET_CDP [ACTIVO]</span>
        </div>
        <div className="hud-silicon-truth">
          <span className="label">PUERTA_SILICIO:</span>
          <span className="value status-green">ABIERTA [C5]</span>
        </div>
        <button className="hud-notch-trigger" onClick={fireNotchPing}>
          [ DISPARADOR: LED_NOTCH ]
        </button>
      </div>

      {/* 3D DOM Topography Canvas */}
      <div className="hud-spatial-volume" ref={containerRef}>
        <div className="hud-watermark-omega">Ω</div>
        <div className="hud-3d-scene">
          {nodes.map(n => (
            <div 
              key={n.id} 
              className="hud-dom-node"
              style={{
                '--node-x': `${n.x}vw`,
                '--node-y': `${n.y}vh`,
                '--node-z': `${n.z}px`,
                '--node-opacity': n.opacity,
                '--node-color': n.color
              } as React.CSSProperties}
            >
              <div className="node-bracket">&lt;</div>
              <div className="node-tag">{n.tag}</div>
              <div className="node-bracket">&gt;</div>
              <div className="node-glow"></div>
            </div>
          ))}
        </div>
      </div>
      
      <div className="hud-footer">
        <div className="hud-metrics">
          <div className="metric">
            <span className="m-label">PUERTO:</span>
            <span className="m-value">9222</span>
          </div>
          <div className="metric">
            <span className="m-label">LATENCIA:</span>
            <span className="m-value">{telemetry.latency}ms</span>
          </div>
          <div className="metric">
            <span className="m-label">NODOS:</span>
            <span className="m-value">{telemetry.nodesCount.toLocaleString()}</span>
          </div>
          <div className="metric">
            <span className="m-label">EXERGÍA:</span>
            <span className="m-value color-gold">{telemetry.exergy}W</span>
          </div>
        </div>
        <div className="hud-log">
          &gt; EXTRACCIÓN Z-INDEX [C5-REAL] COMPLETADA.<br/>
          &gt; BLOQUEO PASO-A-PASO HYDRA_RTL: SINCRONIZADO.<br/>
          &gt; PUERTA DEONTOLÓGICA: KANT [ACTIVA].
        </div>
      </div>
    </div>
  );
};
