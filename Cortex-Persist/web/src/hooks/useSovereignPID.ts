import { useState, useEffect, useMemo } from 'react';
import { Protocol911State } from '../types/sovereign';

/**
 * useSovereignPID - Phase 10: Passive Observer
 * Slave hook that handles UI-only animations and agent lifecycle state,
 * while measurements and control logic are delegated to the Backend Governor.
 */
export const useSovereignPID = (isStressed: boolean, showLegionMonitor: boolean, governorStatus?: string) => {
  const [activeAgents, setActiveAgents] = useState<number[]>([]);
  
  const p911State = useMemo<Protocol911State>(() => {
    if (governorStatus === 'ROJO') return 'EMERGENCIA';
    if (governorStatus === 'STRIKE') return 'STRIKE';
    if (isStressed) return 'EMERGENCIA'; 
    if (governorStatus === 'ÁMBAR') return 'PREVENCION';
    return 'NORMAL';
  }, [isStressed, governorStatus]);

  // Adjust active agents based on stress (Visual only / Animation Substrate)
  useEffect(() => {
    if (!showLegionMonitor) return;

    const timer = setInterval(() => {
      setActiveAgents(prev => {
        const count = prev.length;
        if (isStressed && count < 50) {
          return [...prev, Math.floor(Math.random() * 100) + 1];
        } else if (!isStressed && count > 5) {
          return prev.slice(0, -1);
        }
        return prev;
      });
    }, 500);

    return () => clearInterval(timer);
  }, [isStressed, showLegionMonitor]);

  return {
    p911State,
    activeAgents,
    setActiveAgents
  };
};
