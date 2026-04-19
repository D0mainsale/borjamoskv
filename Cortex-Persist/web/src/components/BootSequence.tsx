import React, { useState, useEffect } from 'react';
import './BootSequence.css';

const BOOT_LOGS = [
  "kernel: AOS v6.0.0-aurora initializing...",
  "kernel: Binding Sovereign Fabric to Direct-Silicon... OK",
  "aos: Starting CORTEX_SUBSYSTEM Ω-MANDATE...",
  "aos: Verified C5-REAL cryptographic signatures.",
  "dban: Linking to Decentralized Billion Agent Network [DBAN]...",
  "ouroboros: Mapping Capital-Extractor volumes... SUCCESS",
  "vsa: Initializing D=10000 Semantic Tensor Space.",
  "vsa: Restoring Contextual Exery Index from sqlite-vec.",
  "shield: Loading Aegis-Omega Aesthetics Protocol...",
  "sys: AOS SYSTEMS NOMINAL. NOISE PURGED.",
  "sys: BYPASSING RHEATORIC WAIT LOCK.",
  "execute: MICA_NOIR_MODE=v6.0 start-kernel"
];

export const BootSequence: React.FC<{ onComplete: () => void }> = ({ onComplete }) => {
  const [logs, setLogs] = useState<string[]>([]);
  const [glitchOut, setGlitchOut] = useState(false);

  useEffect(() => {
    let currentIndex = 0;
    
    // Simulate rapid boot sequence
    const interval = setInterval(() => {
      if (currentIndex < BOOT_LOGS.length) {
        setLogs(prev => [...prev, BOOT_LOGS[currentIndex]]);
        currentIndex++;
      } else {
        clearInterval(interval);
        
        // Trigger glitch transition out
        setTimeout(() => {
          setGlitchOut(true);
          
          // Actually remove component after glitch anim finishes
          setTimeout(() => {
            onComplete();
          }, 400); 
        }, 600);
      }
    }, 120); // 120ms per line

    return () => clearInterval(interval);
  }, [onComplete]);

  return (
    <div className={`boot-container ${glitchOut ? 'glitch-out' : ''}`}>
      <div className="boot-terminal">
        {logs.map((log, i) => (
          <div key={i} className="boot-line">
            <span className="boot-timestamp">[{String((i * 0.12).toFixed(3)).padStart(6, '0')}]</span>
            <span className="boot-text">{log}</span>
          </div>
        ))}
        {!glitchOut && <div className="boot-cursor">_</div>}
      </div>
    </div>
  );
};
