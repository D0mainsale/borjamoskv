import React, { createContext, useContext, useState, ReactNode } from 'react';
import { useSovereignPID } from '../hooks/useSovereignPID';
import { Protocol911State, PersistMode, GovernorMetrics } from '../types/sovereign';
import { useSovereignTelemetry } from '../hooks/useSovereignTelemetry';
import { useArchiForge, ArchiProduct } from '../hooks/useArchiForge';
import { useSovereignActions } from '../hooks/useSovereignActions';

interface StrategyContextType {
  // Telemetría (Núcleo)
  measuredEntropy: number;
  exergyLevel: number;
  factCount: number;
  sealedFacts: number;
  persistMode: PersistMode;
  p911State: Protocol911State;
  
  // Telemetry (Advanced)
  pidOutput: number;
  stabilityHistory: number[];
  governorMetrics: GovernorMetrics | null;
  internalAuditFeed: string[];
  yieldData: any;
  activeAgents: number[];
  setActiveAgents: (v: number[]) => void;
  legion: any[];
  swarmStats: any;
  
  // Forge
  isArchiLoading: boolean;
  archiStatus: string;
  recentProducts: ArchiProduct[];
  handleArchiDirective: (prompt: string, addNotification: any) => Promise<any>;
  
  // Actions
  strikeLog: string | null;
  isFractalStrikeActive: boolean;
  handleStrike: (params: any) => Promise<void>;
  handleFractalStrike: (onActive: (agents: number[]) => void) => Promise<void>;
  fetchBounties: () => Promise<void>;
  
  // Controls (Shared state)
  equilibrium: number;
  setEquilibrium: (v: number) => void;
  isStressed: boolean;
  setIsStressed: (v: boolean) => void;
  proximityNode: string | null;
  setProximityNode: (v: string | null) => void;
  hechosSoberanos: any[]; 
  showLegionMonitor: boolean;
  setShowLegionMonitor: (v: boolean) => void;
  vsaMetrics: any;
  crystallizeMemory: () => Promise<void>;
  
  // Identity
  claimSovereignHandle: (handle: string) => Promise<{ success: boolean; msg: string }>;
  checkHandleAvailability: (handle: string) => Promise<boolean>;
}

const StrategyContext = createContext<StrategyContextType | null>(null);

export const StrategyProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const apiHost = 'http://localhost:8000';
  
  const [equilibrium, setEquilibrium] = useState(50);
  const [isStressed, setIsStressed] = useState(false);
  const [proximityNode, setProximityNode] = useState<string | null>(null);
  const [showLegionMonitor, setShowLegionMonitor] = useState(false);

  // Unified Hooks Execution
  const {
      persistMode, sealedFacts, factCount, yieldData, governorMetrics, internalAuditFeed, hechosSoberanos, legion, swarmStats, vsaMetrics
  } = useSovereignTelemetry(apiHost);

  const { 
    p911State, activeAgents, setActiveAgents
  } = useSovereignPID(isStressed, showLegionMonitor, governorMetrics?.status);

  // Derive PID metrics from Backend Telemetry (Phase 10: Closed-Loop)
  const pidOutput = governorMetrics?.pid_output ?? 50;
  const measuredEntropy = governorMetrics ? (governorMetrics as any).medido ?? 50 : 50;
  const stabilityHistory = hechosSoberanos.slice(-50).map(h => h.exergia * 100);
  const exergyLevel = governorMetrics ? (governorMetrics as any).exergia * 100 : 99.1;

  // Sync equilibrium with Backend Governor (Debounced)
  React.useEffect(() => {
    const timer = setTimeout(() => {
      fetch(`${apiHost}/api/homeostasis/setpoint`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ setpoint: equilibrium })
      }).catch(err => console.error('◈ GOVERNOR_SYNC_ERROR:', err));
    }, 500);
    return () => clearTimeout(timer);
  }, [equilibrium, apiHost]);

  const { 
    isArchiLoading, archiStatus, recentProducts, handleArchiDirective 
  } = useArchiForge(apiHost);

  const crystallizeMemory = async () => {
    try {
      const resp = await fetch(`${apiHost}/api/vsa/crystallize`, { method: 'POST' });
      const data = await resp.json();
      console.log('◈ VSA_COLLAPSE_SUCCESS:', data);
    } catch (err) {
      console.error('◈ VSA_COLLAPSE_ERROR:', err);
    }
  };

  const claimSovereignHandle = async (handle: string) => {
    try {
      const resp = await fetch(`${apiHost}/api/identidad/registrar`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ handle, session_id: 'sovereign_user' })
      });
      return await resp.json();
    } catch (err) {
      console.error('◈ CLAIM_ERROR:', err);
      return { success: false, msg: 'Error de conexión con el núcleo' };
    }
  };

  const checkHandleAvailability = async (handle: string) => {
    try {
      const resp = await fetch(`${apiHost}/api/identidad/check?handle=${encodeURIComponent(handle)}`);
      const data = await resp.json();
      return data.available;
    } catch (err) {
      console.error('◈ CHECK_ERROR:', err);
      return false;
    }
  };

  const {
    strikeLog, isFractalStrikeActive, handleStrike, handleFractalStrike, fetchBounties
  } = useSovereignActions(apiHost);

  const value = {
    measuredEntropy,
    exergyLevel,
    factCount,
    sealedFacts,
    persistMode,
    p911State,
    pidOutput,
    stabilityHistory,
    governorMetrics,
    internalAuditFeed,
    yieldData,
    activeAgents,
    setActiveAgents,
    isArchiLoading,
    archiStatus,
    recentProducts,
    handleArchiDirective,
    strikeLog,
    isFractalStrikeActive,
    handleStrike,
    handleFractalStrike,
    fetchBounties,
    equilibrium,
    setEquilibrium,
    isStressed,
    setIsStressed,
    proximityNode,
    setProximityNode,
    showLegionMonitor,
    setShowLegionMonitor,
    hechosSoberanos,
    legion,
    swarmStats,
    vsaMetrics,
    crystallizeMemory,
    claimSovereignHandle,
    checkHandleAvailability
  };

  // Sonic Tension Synchronization
  React.useEffect(() => {
    import('../utils/SonicService').then(({ sonic }) => {
      sonic.init();
      sonic.updateDrone(30 + measuredEntropy / 2, measuredEntropy);
    });
  }, [measuredEntropy]);

  return (
    <StrategyContext.Provider value={value}>
      {children}
    </StrategyContext.Provider>
  );
};

export const useStrategy = () => {
  const context = useContext(StrategyContext);
  if (!context) throw new Error('useStrategy must be used within a StrategyProvider');
  return context;
};
