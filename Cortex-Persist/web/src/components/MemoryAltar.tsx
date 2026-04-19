import React, { useState, useEffect, useRef } from 'react';
import { useStrategy } from '../contexts/StrategyContext';
import { sonic } from '../utils/SonicService';
import CausalityNexus from './CausalityNexus';
import { StrikeTerminal } from './StrikeTerminal';
import './MemoryAltar.css';

interface MemoryAltarProps {
  onClose: () => void;
}

export const MemoryAltar: React.FC<MemoryAltarProps> = ({ onClose }) => {
  const { hechosSoberanos, factCount, sealedFacts } = useStrategy();
  const [lineageFactId, setLineageFactId] = useState<number | null>(null);
  const [activeStrike, setActiveStrike] = useState<{ id: number; target: string } | null>(null);
  const listRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (listRef.current) {
      const cards = listRef.current.querySelectorAll('.fact-card');
      cards.forEach((card, index) => {
        const fact = hechosSoberanos[index];
        if (fact) {
          const fill = card.querySelector('.exergy-fill') as HTMLDivElement;
          if (fill) {
            fill.style.width = `${fact.exergia * 100}%`;
          }
        }
      });
    }
  }, [hechosSoberanos]);

  const handleCrystallize = async (id: number) => {
    sonic.playClick('deploy');
    try {
      const response = await fetch('http://localhost:8000/api/fact/crystallize', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id })
      });
      if (response.ok) {
        console.log(`◈ ALTAR: Fact ${id} crystallized.`);
      }
    } catch (err) {
      console.error("C5_CRYSTALLIZE_FAIL:", err);
    }
  };

  const handleAnnihilate = async (id: number) => {
    sonic.playClick('error');
    const el = document.querySelector(`[data-fact-id="${id}"]`);
    if (el) el.classList.add('annihilating');
    
    try {
      const response = await fetch('http://localhost:8000/api/fact/annihilate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id })
      });
      if (response.ok) {
        console.log(`◈ ALTAR: Fact ${id} annihilated.`);
      }
    } catch (err) {
      console.error("C5_ANNIHILATE_FAIL:", err);
      if (el) el.classList.remove('annihilating');
    }
  };

  const handleOpenLineage = (id: number) => {
    sonic.playClick('hover');
    setLineageFactId(id);
  };

  const handleStrikeTrigger = (id: number, target: string) => {
    setActiveStrike({ id, target });
  };

  return (
    <div className="memory-altar-overlay" onClick={onClose}>
      <div className="memory-altar-container" onClick={e => e.stopPropagation()}>
        <div className="memory-altar-header">
          <div className="altar-title-group">
            <h2 className="altar-title">memory altar</h2>
            <p className="altar-subtitle">c5-real operative substrate</p>
          </div>
          <div className="altar-stats">
            <div className="altar-stat">
              <span className="stat-label">total_facts</span>
              <span className="stat-value">{factCount}</span>
            </div>
            <div className="altar-stat">
              <span className="stat-label">crystallized</span>
              <span className="stat-value">{sealedFacts}</span>
            </div>
            <button className="close-altar-btn" onClick={onClose}>close</button>
          </div>
        </div>

        <div className="memory-list" ref={listRef}>
          {hechosSoberanos.map((fact) => (
            <div 
              key={fact.id} 
              data-fact-id={fact.id}
              className={`fact-card ${fact.cristalizado ? 'crystallized' : ''}`}
            >
              <div className="fact-meta">
                <span className="fact-domain">{fact.dominio}</span>
                <span className="fact-exergy">E: {(fact.exergia * 100).toFixed(1)}%</span>
              </div>
              <div className="fact-content">{fact.contenido}</div>
              <div className="fact-actions">
                <button 
                  className="btn-action"
                  onClick={() => handleOpenLineage(fact.id)}
                >
                  lineage
                </button>
                {!fact.cristalizado && (
                  <button 
                    className="btn-action highlight"
                    onClick={() => handleCrystallize(fact.id)}
                  >
                    crystallize
                  </button>
                )}
                <button 
                  className="btn-action danger"
                  onClick={() => handleAnnihilate(fact.id)}
                >
                  annihilate
                </button>
              </div>
              <div className="fact-exergy-bar">
                <div 
                  className="exergy-fill" 
                ></div>
              </div>
            </div>
          ))}
          {hechosSoberanos.length === 0 && (
            <div className="empty-altar">
              ∴ empty substrate: no persistent facts acquired.
            </div>
          )}
        </div>
      </div>

      {lineageFactId !== null && (
        <CausalityNexus 
          factId={lineageFactId} 
          onClose={() => setLineageFactId(null)} 
          onStrike={handleStrikeTrigger}
        />
      )}

      {activeStrike && (
        <StrikeTerminal 
          factId={activeStrike.id} 
          target={activeStrike.target}
          onClose={() => setActiveStrike(null)}
        />
      )}
    </div>
  );
};
