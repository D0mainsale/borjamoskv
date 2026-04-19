import React, { useEffect, useRef, useCallback, useState } from 'react';
import './VSAMonitor.css';

const GRID_SIZE = 100;
const TICK_MS = 200; // Faster for fluid collapse animation
const MUTATION_RATE = 0.08;

export const VSAMonitor: React.FC = () => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const dotsRef = useRef<Float32Array>(new Float32Array(GRID_SIZE));
  const tensorIdRef = useRef(Math.random().toString(16).slice(2, 6).toLowerCase());
  const [isCollapsing, setIsCollapsing] = useState(false);
  const [memSize, setMemSize] = useState(78643); // in KB (approx 78MB)
  const pulseRef = useRef(0);

  const draw = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const cols = 10;
    const cellW = canvas.width / cols;
    const cellH = canvas.height / cols;

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    const dots = dotsRef.current;
    for (let i = 0; i < GRID_SIZE; i++) {
      const x = (i % cols) * cellW;
      const y = Math.floor(i / cols) * cellH;
      const v = dots[i];

      // Matrix-style coloring transition
      if (isCollapsing) {
        ctx.fillStyle = v > 0.4 ? '#2B3BE5' : '#111';
      } else {
        ctx.fillStyle = v > 0.8 ? '#2B3BE5' : '#1A1A1A';
      }
      
      ctx.globalAlpha = v * 0.8 + 0.2;
      ctx.fillRect(x + 1, y + 1, cellW - 2, cellH - 2);

      if (v > 0.9) {
        ctx.shadowBlur = 8;
        ctx.shadowColor = '#2B3BE5';
        ctx.fillRect(x + 1, y + 1, cellW - 2, cellH - 2);
        ctx.shadowBlur = 0;
      }
    }

    // Overlay scan line for collapse
    if (isCollapsing) {
      ctx.strokeStyle = 'rgba(43, 229, 139, 0.5)';
      ctx.lineWidth = 2;
      const lineY = (pulseRef.current % 100) / 100 * canvas.height;
      ctx.beginPath();
      ctx.moveTo(0, lineY);
      ctx.lineTo(canvas.width, lineY);
      ctx.stroke();
    }

    ctx.globalAlpha = 1;
  }, [isCollapsing]);

  useEffect(() => {
    const dots = dotsRef.current;
    for (let i = 0; i < GRID_SIZE; i++) {
        dots[i] = Math.random();
    }
    
    const interval = setInterval(() => {
      pulseRef.current += 5;
      
      // Toggle collapse every few seconds
      if (pulseRef.current % 500 === 0) {
        setIsCollapsing(true);
        // Animate size drop
        let start = 78643;
        const target = 78;
        const duration = 1000;
        const startTime = Date.now();
        
        const step = () => {
          const now = Date.now();
          const p = Math.min(1, (now - startTime) / duration);
          setMemSize(Math.floor(start - (start - target) * p));
          if (p < 1) requestAnimationFrame(step);
          else {
            setTimeout(() => {
                setIsCollapsing(false);
                setMemSize(78643); // Reset or maintain? Keeping transient for visual impact
            }, 2000);
          }
        };
        step();
      }

      for (let i = 0; i < GRID_SIZE; i++) {
        if (Math.random() < (isCollapsing ? 0.4 : MUTATION_RATE)) {
          dots[i] = Math.random();
        }
      }
      draw();
    }, TICK_MS);

    return () => clearInterval(interval);
  }, [draw, isCollapsing]);

  return (
    <div className={`vsa-monitor ${isCollapsing ? 'collapsing' : ''}`}>
      <div className="vsa-header">
        <span className="vsa-label">vsa-sdm // memory_substrate</span>
        <span className={`vsa-status ${isCollapsing ? 'pulse-green' : ''}`}>
            {isCollapsing ? 'algebraic_collapse' : 'binding_active'}
        </span>
      </div>
      <div className="vsa-canvas-wrapper">
        <canvas
            ref={canvasRef}
            className="vsa-canvas"
            width={200}
            height={200}
        />
        {isCollapsing && <div className="collapse-overlay">78mb → 78kb</div>}
      </div>
      <div className="vsa-footer">
        <div className="vsa-tensor-id">tensor: 0xfd2a...{tensorIdRef.current}</div>
        <div className="vsa-mem-size">size: {memSize > 1024 ? (memSize/1024).toFixed(1) + ' mb' : memSize + ' kb'}</div>
      </div>
    </div>
  );
};
