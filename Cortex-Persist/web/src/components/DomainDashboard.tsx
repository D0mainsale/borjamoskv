import React, { useState, useEffect, useRef } from 'react';
import './DomainDashboard.css';

// Sub-componentes
import { MoskvChat } from './MoskvChat/MoskvChat';
import { UltraTacticalMap } from './UltraTacticalMap';
import { AudienceIntelligence } from './AudienceIntelligence';
import { WebGLSubstrate } from './WebGLSubstrate';
import { SovereignHeader } from './SovereignHeader';
import { ForgePanel } from './ForgePanel';
import { DomainGrid } from './DomainGrid';
import { StrikeConsole } from './StrikeConsole';
import { MemoryAltar } from './MemoryAltar';
import { HomeostasisMonitor } from './HomeostasisMonitor';
import { LegionMonitor } from './LegionMonitor';
import { VSAMonitor } from './VSAMonitor';

// Lógica y Datos
import { useStrategy } from '../contexts/StrategyContext';
import { DomainConfig } from '../data/domains';
import { sonic } from '../utils/SonicService';

interface DomainDashboardProps {
  onDeploy?: (domain: any) => void;
  isAbueloMode?: boolean;
  sovereignHandle?: string | null;
}


export const DomainDashboard: React.FC<DomainDashboardProps> = ({ onDeploy, isAbueloMode }) => {
  const {
    isArchiLoading, archiStatus, recentProducts, handleArchiDirective,
    pidOutput, measuredEntropy, p911State, activeAgents, setActiveAgents,
    persistMode, sealedFacts, factCount, strikeLog,
    isFractalStrikeActive, handleStrike, handleFractalStrike, fetchBounties,
    proximityNode, legion, vsaMetrics, crystallizeMemory
  } = useStrategy();

  const [notifications, setNotifications] = useState<any[]>([]);
  const addNotification = (msg: string, type: 'success' | 'error' = 'success') => {
    const id = Math.random().toString(36).substr(2, 9);
    setNotifications(prev => [...prev, { id, msg, type }]);
    setTimeout(() => setNotifications(prev => prev.filter(n => n.id !== id)), 5000);
  };

  const [showLegionMonitor, setShowLegionMonitor] = useState(false);
  const [activeDomain, setActiveDomain] = useState<string | null>(null);
  const [isGuardActive, setIsGuardActive] = useState<boolean>(true);
  const [showStrikeConsole, setShowStrikeConsole] = useState(false);
  const [showTacticalMap, setShowTacticalMap] = useState(false);
  const [showAudienceIntelligence, setShowAudienceIntelligence] = useState(false);
  const [showMoskvChat, setShowMoskvChat] = useState(false);
  const [showMemoryAltar, setShowMemoryAltar] = useState(false);
  const [showTelemetry, setShowTelemetry] = useState(false);
  const [strikeParams, setStrikeParams] = useState({ domain: '', apiUrl: '', token: '' });
  const [isInitialized, setIsInitialized] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  const initSignal = () => {
    sonic.init();
    setIsInitialized(true);
    sonic.playClick('deploy');
  };

  const handleOuroborosExtraction = async () => {
    addNotification('INICIANDO EXFILTRACIÓN C5-REAL...', 'success');
    sonic.playClick('strike');
    try {
      const response = await fetch('http://localhost:8000/api/ouroboros/extract', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mode: 'live', handle: 'borjamoskv' }) 
      });
      const result = await response.json();
      if (result.status === 'SUCCESS') {
        addNotification(`EXTRACCIÓN EXITOSA: ${result.message}`, 'success');
      } else {
        addNotification(`FALLO EN EXFILTRACIÓN: ${result.message}`, 'error');
      }
    } catch (err) {
      addNotification('ERROR DE CONEXIÓN CON OUROBOROS', 'error');
    }
  };

  useEffect(() => {
    if (isInitialized) sonic.updateDrone(30 + measuredEntropy / 2, measuredEntropy);
  }, [measuredEntropy, isInitialized]);

  // Progreso de Scroll (Láser de Profundidad)
  useEffect(() => {
    const handleScroll = () => {
      const scrollHeight = document.documentElement.scrollHeight - window.innerHeight;
      const progress = (window.scrollY / scrollHeight) * 100;
      if (containerRef.current) {
        containerRef.current.style.setProperty('--scroll-height', `${progress}%`);
      }
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  // Interacción Física (Tecla E) - Nexos del Espacio
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.code === 'KeyE' && proximityNode) {
        sonic.playClick('deploy');
        if (proximityNode === 'strike') setShowStrikeConsole(true);
        else if (proximityNode === 'intelligence') setShowTelemetry(true);
        else if (proximityNode === 'sovereign-agents') setShowMoskvChat(true);
        else if (proximityNode === 'domain') setShowTacticalMap(true);
        else if (proximityNode === 'memory-altar') setShowMemoryAltar(true);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [proximityNode]);

  const onDeployClick = (domain: DomainConfig) => {
    if (domain.id === 'cybersec') setShowStrikeConsole(true);
    else if (domain.id === 'legion-100') { setShowLegionMonitor(true); handleFractalStrike(setActiveAgents); }
    else if (domain.id === 'moskv-nexus') setShowTelemetry(true);
    else if (domain.id === 'solidity-fuzzing') setShowStrikeConsole(true);
    else if (domain.id === 'sovereign-agents') setShowMoskvChat(true);
    else if (domain.id === 'exfiltration-c5') { handleOuroborosExtraction(); fetchBounties(); }
    else if (domain.id === 's0p-governor') setShowLegionMonitor(!showLegionMonitor);
    else if (domain.id === 'memory-altar') setShowMemoryAltar(true);
    onDeploy?.(domain);
  };

  if (!isInitialized) {
    return (
      <div className="system-init-overlay" onClick={initSignal}>
        {p911State === 'EMERGENCIA' && (
          <div className="emergency-active-overlay mica-texture">
            <div className="emergency-content">
              <span className="emergency-warning">ALERTA_MÁXIMA: PROTOCOLO_EMERGENCIA_ACTIVO</span>
              <div className="emergency-pulse"></div>
            </div>
          </div>
        )}
        {p911State === 'STRIKE' && (
          <div className="strike-active-overlay mica-texture">
            <div className="strike-content">
              <span className="strike-warning">EXTRACCIÓN_ACTIVA: MODO_STRIKE_SOBERANO</span>
              <div className="strike-pulse"></div>
              <div className="telemetry-item">
                <span className="label">RATIO_VSA</span>
                <span className="value cyan">{vsaMetrics.ratio}</span>
              </div>
              <button 
                className="crystallize-btn"
                onClick={crystallizeMemory}
                title="Ω-COLLAPSE: Crystallize Memory Facts"
              >
                CRISTALIZAR
              </button>
            </div>
          </div>
        )}
        <div className="vsa-section">
          <VSAMonitor />
        </div>
        <div className="secondary-controls">
        <div className="init-core">
          <div className="init-logo">∴</div>
          <div className="init-label">acquiring sovereign signal...</div>
          <div className="init-sub">pulse to activate c5-real protocol</div>
        </div>
      </div>
      </div>
    );
  }

  return (
    <div 
      ref={containerRef} 
      className={`domain-dashboard-container ${p911State === 'STRIKE' ? 'strike-active' : ''} ${p911State === 'EMERGENCIA' ? 'emergency-active' : ''}`}
      data-abuelo={isAbueloMode}
    >
      <WebGLSubstrate 
        entropy={isArchiLoading ? 0.95 : (measuredEntropy / 100)} 
        equilibrium={isArchiLoading ? 0.1 : (pidOutput / 100)}
        accentColor={p911State === 'STRIKE' || p911State === 'EMERGENCIA' ? '#E52B2B' : '#2BE58B'}
      />
      
      {showTelemetry && (
        <div className="telemetry-nexo-layer">
          <HomeostasisMonitor />
        </div>
      )}
      
      <div className="noise-grain"></div>
      <div className="scanlines"></div>
      <div className="scroll-progress-line"></div>
      
      <SovereignHeader 
        isAbueloMode={isAbueloMode}
        onToggleAbuelo={() => {}}
        isGuardActive={isGuardActive}
        toggleGuard={() => setIsGuardActive(!isGuardActive)}
        showTacticalMap={showTacticalMap}
        setShowTacticalMap={setShowTacticalMap}
        showAudienceIntelligence={showAudienceIntelligence}
        setShowAudienceIntelligence={setShowAudienceIntelligence}
        showTelemetry={showTelemetry}
        setShowTelemetry={setShowTelemetry}
      />

      <ForgePanel 
        recentProducts={recentProducts}
        isArchiLoading={isArchiLoading}
        archiStatus={archiStatus}
        handleArchiDirective={(p) => handleArchiDirective(p, addNotification)}
      />

      <DomainGrid 
        activeDomain={activeDomain}
        setActiveDomain={setActiveDomain}
        isGuardActive={isGuardActive}
        deploymentStatus={{}}
        mythosData={null}
        vanguardData={null}
        handleStellarStrike={() => {}}
        onDeployClick={onDeployClick}
        sonic={sonic}
      />

      <StrikeConsole 
        showStrikeConsole={showStrikeConsole}
        setShowStrikeConsole={setShowStrikeConsole}
        strikeParams={strikeParams}
        setStrikeParams={setStrikeParams}
        handleStrike={() => handleStrike(strikeParams)}
        displayedLog={strikeLog || ''}
        debugMode={false}
      />

      <div className="sovereign-toast-layer">
        {notifications.map(n => (
          <div key={n.id} className={`sovereign-toast ${n.type}`}>
            <span className="message">{n.msg.toLowerCase()}</span>
          </div>
        ))}
      </div>

      {showMoskvChat && <MoskvChat onClose={() => setShowMoskvChat(false)} />}
      
      {showTacticalMap && (
        <UltraTacticalMap 
          activeAgents={activeAgents}
          measuredEntropy={measuredEntropy}
          isStrikeActive={isFractalStrikeActive}
          persistMode={persistMode}
          sealedFacts={sealedFacts}
          factCount={factCount}
          findings={[]} 
          legionAgents={legion}
          onClose={() => setShowTacticalMap(false)} 
        />
      )}
      
      {showAudienceIntelligence && <AudienceIntelligence onClose={() => setShowAudienceIntelligence(false)} />}
      
      {showMemoryAltar && <MemoryAltar onClose={() => setShowMemoryAltar(false)} />}
      
      {showLegionMonitor && (
        <div className="telemetry-nexo-layer">
          <LegionMonitor 
            onClose={() => setShowLegionMonitor(false)} 
          />
        </div>
      )}
    </div>
  );
};

export default DomainDashboard;
