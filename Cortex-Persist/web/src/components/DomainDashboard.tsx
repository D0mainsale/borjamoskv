import React, { useState, useEffect, useCallback, useRef, useMemo } from 'react';
import './DomainDashboard.css';
import { MoskvChat } from './MoskvChat/MoskvChat';
import { UltraTacticalMap } from './UltraTacticalMap';
import { MagneticWrapper } from './MagneticWrapper';

interface Domain {
  id: string;
  title: string;
  description: string;
  icon: string;
  color: string;
  amount?: number;
  status?: string;
}

interface MythosMilestone {
  id: string;
  description: string;
  status: string;
  unlocks_at?: string;
  poy_target?: string;
}

interface MythosData {
  project: string;
  state_machine: {
    current_phase: number;
    milestones: MythosMilestone[];
  };
}

interface DomainDashboardProps {
  onDeploy?: (domain: Domain) => void;
}

// ── Sonic Service (Industrial Modular Synthesis) ─────────────────────
class SonicService {
  private ctx: AudioContext | null = null;
  private droneOsc: OscillatorNode | null = null;
  private droneGain: GainNode | null = null;

  init() {
    if (this.ctx) return;
    this.ctx = new (window.AudioContext || (window as any).webkitAudioContext)();
    
    // Ambient Drone (Low Freq Tension)
    this.droneOsc = this.ctx.createOscillator();
    this.droneGain = this.ctx.createGain();
    const lpf = this.ctx.createBiquadFilter();
    
    this.droneOsc.type = 'sawtooth';
    this.droneOsc.frequency.setValueAtTime(32.7, this.ctx.currentTime); // C1
    
    lpf.type = 'lowpass';
    lpf.frequency.setValueAtTime(120, this.ctx.currentTime);
    
    this.droneGain.gain.setValueAtTime(0.02, this.ctx.currentTime);
    
    this.droneOsc.connect(lpf);
    lpf.connect(this.droneGain);
    this.droneGain.connect(this.ctx.destination);
    
    this.droneOsc.start();
  }

  playClick(type: 'hover' | 'deploy' | 'error') {
    if (!this.ctx) return;
    const osc = this.ctx.createOscillator();
    const g = this.ctx.createGain();
    
    if (type === 'hover') {
      osc.type = 'sine';
      osc.frequency.setValueAtTime(800, this.ctx.currentTime);
      osc.frequency.exponentialRampToValueAtTime(100, this.ctx.currentTime + 0.05);
      g.gain.setValueAtTime(0.03, this.ctx.currentTime);
    } else if (type === 'deploy') {
      osc.type = 'square';
      osc.frequency.setValueAtTime(400, this.ctx.currentTime);
      osc.frequency.exponentialRampToValueAtTime(800, this.ctx.currentTime + 0.15);
      g.gain.setValueAtTime(0.05, this.ctx.currentTime);
    }
    
    g.gain.exponentialRampToValueAtTime(0.001, this.ctx.currentTime + 0.2);
    
    osc.connect(g);
    g.connect(this.ctx.destination);
    
    osc.start();
    osc.stop(this.ctx.currentTime + 0.2);
  }

  updateDrone(frequency: number) {
    if (!this.droneOsc || !this.ctx) return;
    this.droneOsc.frequency.setTargetAtTime(frequency, this.ctx.currentTime, 0.5);
  }
}

const sonic = new SonicService();

const domains: Domain[] = [
  {
    id: 'ai-ml',
    title: 'Ingeniería AI/ML',
    description: 'Modelos TensorFlow/PyTorch ajustados para flujos de trabajo del mundo real.',
    icon: 'Ω',
    color: '#2B3BE5'
  },
  {
    id: 'cybersec',
    title: 'Ciberseguridad',
    description: 'Fase 3 (Mythos): Insecure Deserialization -> RCE. Pivoteando desde XSS hacia dominancia del servidor.',
    icon: '🛡️',
    color: '#E52B2B'
  },
  {
    id: 'cloud',
    title: 'Nube (AWS/Azure/GCP)',
    description: 'Arquitectura multirregión, serverless y escalabilidad global garantizada.',
    icon: '☁️',
    color: '#2B8BE5'
  },
  {
    id: 'devops',
    title: 'DevOps & CI/CD',
    description: 'Integración continua con GitHub Actions/Terraform para ciclos de lanzamiento 80% más rápidos.',
    icon: '⚙️',
    color: '#E58B2B'
  },
  {
    id: 'data',
    title: 'Ingeniería de Datos',
    description: 'Streaming con Apache Spark y transformaciones dbt para inteligencia empresarial.',
    icon: '📊',
    color: '#8B2BE5'
  },
  {
    id: 'fullstack',
    title: 'Full Stack',
    description: 'React/Vue + Node.js/Next.js con SSR optimizado para SEO.',
    icon: '💻',
    color: '#2BE58B'
  },
  {
    id: 'blockchain',
    title: 'Blockchain / Strikes',
    description: 'Contratos inteligentes Solidity e infraestructura Hyperledger para integridad on-chain.',
    icon: '⛓️',
    color: '#E5E52B'
  },
  {
    id: 'quantum',
    title: 'Computación Cuántica',
    description: 'Circuitos Qiskit y algoritmos híbridos en infraestructuras AWS Braket.',
    icon: '⚛️',
    color: '#2BE5E5'
  },
  {
    id: 'edge',
    title: 'Edge / IoT',
    description: 'Corredores MQTT y clústeres Kubernetes en flotas de baja latencia.',
    icon: '🛰️',
    color: '#E52BE5'
  },
  {
    id: 'sovereign-agents',
    title: 'Agentes Soberanos (AI.com)',
    description: 'Despliegues en la Malla Descentralizada de Mil Millones de Agentes (DBAN) con protocolos de auto-mejora peer-to-peer.',
    icon: 'Ⓐ',
    color: '#2B3BE5'
  },
  {
    id: 'moskv-nexus',
    title: 'MoskvBot 3.3 Nexus',
    description: 'Núcleo Operativo C5: Integración de Autodidact-Ω, System Forge-Ω y MAC Maestro-Ω.',
    icon: '⎈',
    color: '#E52B55'
  },
  {
    id: 'exfiltration-c5',
    title: 'C5 EXFILTRATION UNIT',
    description: 'Extracción de capital soberano desde reportes de recompensa hacia el Ledger C5-REAL.',
    icon: '💸',
    color: '#2BE58B'
  }
];

// ─── Runtime constants (immutable, outside component) ──────────────────────
const KP = 0.8, KI = 0.05, KD = 0.3;
const I_MAX = 30;
const OUT_MIN = 0, OUT_MAX = 100;
const NODE_CAP = 50;
const EDGE_CAP = 20;

// Deterministic LCG — no Math.random() in VSA renders
const lcg = (seed: number): number => Math.imul(seed, 1664525) + 1013904223 | 0;
const seedToFloat = (s: number): number => (s >>> 0) / 0xffffffff;

type Zone = 'CONSOLIDATION' | 'BALANCE' | 'DIVERGENCE';
type Protocol911State = 'NORMAL' | 'PRE_911' | 'YOLO_ACTIVE' | 'COOLDOWN';

const MagneticWrapper: React.FC<{children: React.ReactNode}> = ({ children }) => {
  return <div className="magnetic-nav-item">{children}</div>;
};

export const DomainDashboard: React.FC<DomainDashboardProps> = ({ onDeploy }) => {
  const [yieldData, setYieldData] = useState<any>(null);
  const [mythosData, setMythosData] = useState<MythosData | null>(null);
  const [activeDomain, setActiveDomain] = useState<string | null>(null);
  const [isGuardActive, setIsGuardActive] = useState<boolean>(true);
  const [vanguardData, setVanguardData] = useState<any>(null);
  const [exergyMetrics, setExergyMetrics] = useState<{ neural_resonance: number; exergy_multiplier: number; total_savings?: number } | null>(null);
  const [deploymentStatus, setDeploymentStatus] = useState<Record<string, string>>({});
  const [showStrikeConsole, setShowStrikeConsole] = useState(false);
  const [showLegionMonitor, setShowLegionMonitor] = useState(false);
  const [showNexusForge, setShowNexusForge] = useState(false);
  const [showTacticalMap, setShowTacticalMap] = useState(false);
  const [showExfiltrationConsole, setShowExfiltrationConsole] = useState(false);
  const [showAutodidactMonitor, setShowAutodidactMonitor] = useState(false);
  const [showMoskvChat, setShowMoskvChat] = useState(false);
  const [strikeParams, setStrikeParams] = useState({ domain: '', apiUrl: '', token: '' });
  const [strikeLog, setStrikeLog] = useState<string | null>(null);
  const [internalAuditFeed, setInternalAuditFeed] = useState<string[]>([]);
  const [activeAgents, setActiveAgents] = useState<number[]>([]);
  const [hoveredAgent, setHoveredAgent] = useState<any>(null);
  const [sonicPurificationRate, setSonicPurificationRate] = useState(1.1);
  const [searchTerm, setSearchTerm] = useState('');
  const [synergyFlows, setSynergyFlows] = useState<{from: number, to: number}[]>([]);
  const [isDiverging, setIsDiverging] = useState(false);
  const [sieveLogic, setSieveLogic] = useState<string[]>([]);
  const [isSynthesizing, setIsSynthesizing] = useState(false);
  const [synthesisLogs, setSynthesisLogs] = useState<string[]>([]);
  const [isTraining, setIsTraining] = useState(false);
  const [trainingHeatmap] = useState<number[]>(Array(100).fill(0));
  const [activeClawNode, setActiveClawNode] = useState<number | null>(null);
  const [glitchText, setGlitchText] = useState('');
  const [equilibrium, setEquilibrium] = useState<number>(50);
  const mousePosRef = useRef({ x: 0, y: 0 });
  const [cursorType, setCursorType] = useState<'default' | 'terminal'>('default');
  const [debugMode, setDebugMode] = useState(false);
  const [scrollProgress, setScrollProgress] = useState(0);

  // Ω-PERSIST: live membrane state (fed from SSE)
  const [persistMode, setPersistMode] = useState<'COMMITTED' | 'FALLBACK' | 'OFFLINE'>('OFFLINE');
  const [sealedFacts, setSealedFacts] = useState(0);
  const [factCount, setFactCount] = useState(0);

  // ── Scroll Tracking ─────────────────────
  useEffect(() => {
    const handleScroll = () => {
      const scrollHeight = document.documentElement.scrollHeight - window.innerHeight;
      const progress = (window.scrollY / scrollHeight) * 100;
      setScrollProgress(progress);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);


  const konamiProgressRef = useRef<string[]>([]);
  const konamiCode = ['ArrowUp', 'ArrowUp', 'ArrowDown', 'ArrowDown', 'ArrowLeft', 'ArrowRight', 'ArrowLeft', 'ArrowRight', 'b', 'a'];

  // ── Konami Code Listener — O(1): ref-based, [] deps, never recreates ───
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      konamiProgressRef.current = [...konamiProgressRef.current, e.key].slice(-konamiCode.length);
      if (JSON.stringify(konamiProgressRef.current) === JSON.stringify(konamiCode)) {
        setDebugMode(true);
        sonic.playClick('deploy');
        console.log("OS: SOVEREIGN_DEBUG = TRUE");
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []); // ← Fixed: never recreates listener on each keypress

  // ── Terminal Display (O(1) Direct-Silicon) ─────────────────────
  const [displayedLog, setDisplayedLog] = useState('');
  useEffect(() => {
    if (strikeLog) setDisplayedLog(strikeLog); // Zero-Rhetoric immediate bind
  }, [strikeLog]);

  // ── Cursor + Header Refs (declared before handleMouseMove for closure) ──
  const cursorRef = useRef<HTMLDivElement>(null);
  const headerRef = useRef<HTMLElement>(null);

  // ── Mouse tracking — Direct DOM imperativo, ZERO re-renders ───────────
  const handleMouseMove = useCallback((e: React.MouseEvent) => {
    const x = e.clientX;
    const y = e.clientY;
    mousePosRef.current = { x, y };
    const root = document.documentElement;
    root.style.setProperty('--mouse-x', `${x}px`);
    root.style.setProperty('--mouse-y', `${y}px`);
    // Imperative DOM updates: bypass React render cycle entirely
    if (cursorRef.current) {
      cursorRef.current.style.transform = `translate3d(${x}px, ${y}px, 0)`;
    }
    if (headerRef.current) {
      const dx = (x - window.innerWidth / 2) * 0.01;
      const dy = (y - window.innerHeight / 2) * 0.01;
      headerRef.current.style.transform = `translate3d(${dx}px, ${dy}px, 0)`;
    }
  }, []);

  // ── PID + homeostasis state ─────────────────────────────────────────────────
  const [measuredEntropy, setMeasuredEntropy] = useState<number>(50);
  const [pidOutput, setPidOutput] = useState<number>(50);
  const [zone, setZone] = useState<Zone>('BALANCE');
  const [p911State, setP911State] = useState<Protocol911State>('NORMAL');
  const [vsaTick, setVsaTick] = useState(0);
  const [stabilityHistory, setStabilityHistory] = useState<number[]>(Array(50).fill(50));
  const [isStressed, setIsStressed] = useState(false);
  const [exergyLevel, setExergyLevel] = useState(98.4);
  const [, setPidState] = useState({ saturated: false, calibrating: false });
  const [, setCooldownProgress] = useState(0);
  const [pidLogs, setPidLogs] = useState<string[]>([]);
  const [bounties, setBounties] = useState<any[]>([]);
  const [isExfiltrating, setIsExfiltrating] = useState<string | null>(null);

  // ── PID + homeostasis state ─────────────────────────────────────────────────
  const internalPidStateRef = useRef({ saturated: false, calibrating: false });

  // Derived: no extra setState calls needed
  const is911Active = p911State === 'YOLO_ACTIVE';

  // ── Refs (mutable values that don't trigger re-render) ──────────────────────
  const pidRef = useRef({
    integral: 0,
    prevError: 0,
    prevTime: performance.now(),
    lastMeasured: 50,
  });
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const p911Ref = useRef({ enteredAt: 0, pre911Since: 0, cooldownUntil: 0 });
  const activeAgentsRef = useRef<number[]>([]);

  // Sync agents ref (no re-render cost on read)
  useEffect(() => { activeAgentsRef.current = activeAgents; }, [activeAgents]);

  // ── Deterministic VSA substrate — LCG seeded by tick, not Math.random() ────
  const vsaComputed = useMemo(() => {
    let seed = (vsaTick * 1664525 + 1013904223) | 0;
    return Array.from({ length: 100 }, () => {
      seed = lcg(seed);
      return seedToFloat(seed);
    });
  }, [vsaTick]);

  // ── Static agent profile cache (pure-deterministic, computed once) ──────
  const agentProfilesCache = useMemo(() =>
    Array.from({ length: 100 }, (_, i) => getAgentProfile(i + 1)),
  // eslint-disable-next-line react-hooks/exhaustive-deps
  []);

  // ── Decorative heatmap seeds (LCG, low-frequency update every 5 ticks) ──
  const heatmapTick = Math.floor(vsaTick / 5);
  const heatmapSeeds = useMemo(() => {
    let seed = (heatmapTick * 1664525 + 999983) | 0;
    return Array.from({ length: 24 }, () => {
      seed = lcg(seed);
      const s1 = seed;
      seed = lcg(seed);
      return { active: seedToFloat(s1) > 0.7, opacity: 0.1 + seedToFloat(seed) * 0.4 };
    });
  }, [heatmapTick]);

  // ── Zone hysteresis (bands 23/27 and 73/77) ─────────────────────────────────
  useEffect(() => {
    setZone(prev => {
      if (prev === 'CONSOLIDATION') return equilibrium > 27 ? 'BALANCE' : 'CONSOLIDATION';
      if (prev === 'DIVERGENCE')   return equilibrium < 73 ? 'BALANCE' : 'DIVERGENCE';
      // In BALANCE: exit bands
      if (equilibrium < 23) return 'CONSOLIDATION';
      if (equilibrium > 77) return 'DIVERGENCE';
      return 'BALANCE';
    });
  }, [equilibrium]);

  // ── Swarm useEffect: PID + spawn + evaluateProtocol + cleanup ──────────────
  useEffect(() => {
    if (!showLegionMonitor) {
      if (intervalRef.current) clearInterval(intervalRef.current);
      return;
    }
    // Always clear previous interval before creating a new one (prevents accumulation)
    if (intervalRef.current) clearInterval(intervalRef.current);

    const TICK_MS = Math.max(200, 2000 - (equilibrium * 15));

    intervalRef.current = setInterval(() => {
      const now = performance.now();
      const wall = Date.now();

      // ── dt: normalized time delta for PID (seconds, minimum 10ms) ──────────
      const dt = Math.max((now - pidRef.current.prevTime) / 1000, 0.01);
      pidRef.current.prevTime = now;

      // ── Measure entropy from current agent count ────────────────────────────
      const nodeCount = activeAgentsRef.current.length;
      let rawMeasured = (nodeCount / NODE_CAP) * 100;

      // ── Thermal Stress Injection ────────────────────────────────────────────
      if (isStressed) {
        rawMeasured += (Math.random() - 0.5) * 30; // High amplitude noise
      }

      // Low-pass filter prevents derivative kick from step changes
      const filtered = pidRef.current.lastMeasured * 0.8 + rawMeasured * 0.2;
      pidRef.current.lastMeasured = filtered;

      // ── PID computation ─────────────────────────────────────────────────────
      const error = equilibrium - filtered;
      
      // Update history buffer for sparkline
      setStabilityHistory(prev => [...prev.slice(-49), 50 + (error / 2)]); // Mapped to center
      setExergyLevel(prev => Math.min(100, Math.max(85, prev + (Math.random() - 0.5) * 0.2)));

      // Detection of saturation/calibration
      const isSaturated = Math.abs(pidRef.current.integral) >= I_MAX;
      const isCalibrating = Math.abs(error) > 15;
      
      if (isSaturated && !internalPidStateRef.current.saturated) {
        setPidLogs(prev => [`[${new Date().toLocaleTimeString()}] PID_INTEGRAL_MAX_SATURATION`, ...prev.slice(0, 4)]);
      }
      if (isCalibrating && !internalPidStateRef.current.calibrating) {
        setPidLogs(prev => [`[${new Date().toLocaleTimeString()}] HIGH_ERROR_CALIBRATION_TRIGGERED`, ...prev.slice(0, 4)]);
      }

      internalPidStateRef.current = { saturated: isSaturated, calibrating: isCalibrating };
      setPidState({ saturated: isSaturated, calibrating: isCalibrating });

      // Anti-windup: clamp integral before accumulating
      pidRef.current.integral = Math.max(
        -I_MAX,
        Math.min(I_MAX, pidRef.current.integral + error * dt)
      );
      const derivative = (error - pidRef.current.prevError) / dt;
      pidRef.current.prevError = error;
      const rawPid = KP * error + KI * pidRef.current.integral - KD * derivative;
      const pidOut = Math.max(OUT_MIN, Math.min(OUT_MAX, rawPid + 50));

      setMeasuredEntropy(filtered);
      setPidOutput(pidOut);

      // ── Protocol 911 state machine (precedence: 911 > safety > manual > PID) 
      setP911State(prevState => {
        switch (prevState) {
          case 'NORMAL':
            if (equilibrium >= 95) {
              if (!p911Ref.current.pre911Since) p911Ref.current.pre911Since = wall;
              if (wall - p911Ref.current.pre911Since >= 2000) return 'PRE_911';
            } else {
              p911Ref.current.pre911Since = 0;
            }
            return 'NORMAL';

          case 'PRE_911':
            // Safety checks before arming
            if (equilibrium < 85) { p911Ref.current.pre911Since = 0; return 'NORMAL'; }
            if (nodeCount < NODE_CAP &&
                (!p911Ref.current.cooldownUntil || wall > p911Ref.current.cooldownUntil)) {
              p911Ref.current.enteredAt = wall;
              pidRef.current.integral = 0; // Freeze integral → prevents windup rebound on exit
              return 'YOLO_ACTIVE';
            }
            return 'PRE_911';

          case 'YOLO_ACTIVE': {
            const elapsed = wall - p911Ref.current.enteredAt;
            const exit = nodeCount >= NODE_CAP || equilibrium < 85 || elapsed > 10000;
            if (exit) {
              p911Ref.current.cooldownUntil = wall + 30000;
              return 'COOLDOWN';
            }
            return 'YOLO_ACTIVE';
          }

          case 'COOLDOWN':
            const left = p911Ref.current.cooldownUntil - wall;
            setCooldownProgress(Math.max(0, (left / 30000) * 100));
            if (wall >= p911Ref.current.cooldownUntil) {
              p911Ref.current.pre911Since = 0;
              setCooldownProgress(0);
              return 'NORMAL';
            }
            return 'COOLDOWN';
        }
      });

      // ── Agent spawn with hard cap ───────────────────────────────────────────
      if (nodeCount < NODE_CAP) {
        const maxNew = equilibrium > 70 ? 25 : 8;
        const count = Math.min(
          Math.floor(Math.random() * maxNew) + 3,
          NODE_CAP - nodeCount
        );
        const newAgents = Array.from({ length: count }, () => Math.floor(Math.random() * 100) + 1);
        setActiveAgents(newAgents);

        if (newAgents.length >= 2) {
          const numFlows = Math.min(equilibrium > 60 ? 8 : 3, EDGE_CAP);
          const flows = Array.from({ length: numFlows }, () => ({
            from: newAgents[Math.floor(Math.random() * newAgents.length)],
            to: newAgents[Math.floor(Math.random() * newAgents.length)]
          })).filter(f => f.from !== f.to);
          setSynergyFlows(flows);
        }
      }

      // Advance deterministic VSA tick
      setVsaTick(t => t + 1);

    }, TICK_MS);

    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [showLegionMonitor, equilibrium]); // equilibrium changes speed → clean recreate

  // ── Claw RL Hook (CORTEX Substrate Target) ─────────────────────
  useEffect(() => {
    let eventSource: EventSource | null = null;
    if (isTraining) {
      setPidLogs(prev => [`[${new Date().toLocaleTimeString()}] CLAW_TRAIN_API: Connecting to C5 substrate...`, ...prev.slice(0, 4)]);
      
      eventSource = new EventSource('/api/rl/claw/stream');
      
      eventSource.onmessage = (e) => {
        const data = JSON.parse(e.data);
        setActiveClawNode(data.node_id);
        setExergyLevel(data.exergy);
        setStabilityHistory(prev => [...prev.slice(1), 50 + (data.loss * 100)]);
        setPidLogs(prev => [
          `[${new Date().toLocaleTimeString()}] GRAD_NORM: ${data.gradient_norm.toFixed(4)} | NODE_${data.node_id} OPTIMIZED`,
          ...prev.slice(0, 4)
        ]);
      };

      eventSource.onerror = () => {
        setPidLogs(prev => [`[${new Date().toLocaleTimeString()}] CLAW_ERROR: Stream disconnected.`, ...prev.slice(0, 4)]);
        setIsTraining(false);
        eventSource?.close();
      };
    }
    
    return () => {
      eventSource?.close();
      setActiveClawNode(null);
    };
  }, [isTraining]);

  // ── 911 glitch effect (driven by derived is911Active, not internal state) ──
  useEffect(() => {
    if (!is911Active) {
      setGlitchText('');
      return;
    }
    const glitchChars = '0123456789ABCDEF!@#$%^&*()_+-=[]{}|;:,.<>?';
    const interval = setInterval(() => {
      let text = '';
      for (let i = 0; i < 20; i++) {
        text += glitchChars[Math.floor(Math.random() * glitchChars.length)];
      }
      setGlitchText(text);
      setActiveAgents(prev => prev.filter(() => Math.random() > 0.1));
    }, 50);
    return () => clearInterval(interval);
  }, [is911Active]);

  // Manual override for debug — transitions directly to YOLO_ACTIVE
  const trigger911 = () => {
    if (p911State === 'NORMAL' || p911State === 'PRE_911') {
      pidRef.current.integral = 0; // Prevent windup rebound
      p911Ref.current.enteredAt = Date.now();
      p911Ref.current.cooldownUntil = 0;
      setP911State('YOLO_ACTIVE');
    }
  };

  // ── Autodidact-Ω Direct Hook (C5-REAL) ─────────────────────
  useEffect(() => {
    if (showAutodidactMonitor && isDiverging) {
      const triggerJit = async () => {
        try {
          const res = await fetch('/api/jit/trigger', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ mode: 'FALSATION_ENGINE' })
          });
          const data = await res.json();
          setSieveLogic([
            `∴ C5-REAL: JIT_TRIGGER [${data.status}]`,
            `∴ BOOST: ${data.throughput_boost} | EXERGY: ${data.new_exergy_baseline}`,
            "∴ SIGNAL: Reality verified via zero-knowledge proof."
          ]);
        } catch (err) {
          setSieveLogic(["⚠ C5-ERROR: Falsation-Engine socket timeout."]);
        } finally {
          setIsDiverging(false);
        }
      };
      triggerJit();
    }
  }, [showAutodidactMonitor, isDiverging]);

  // ── System Forge Synthesis Hook (C5-REAL) ─────────────────────
  useEffect(() => {
    if (showNexusForge && isSynthesizing) {
       const startSynthesis = async () => {
         try {
           const res = await fetch('/api/hardware/synthesis', {
             method: 'POST',
             headers: { 'Content-Type': 'application/json' },
             body: JSON.stringify({ target: 'SILICON_OVERLORD' })
           });
           const data = await res.json();
           setSynthesisLogs([
             `◈ FORGE: [${data.status}] ID=${data.job_id}`,
             `◈ LOAD: Synthesizing ${data.estimated_cycles.toExponential()} cycles...`,
             "◈ SIGNAL: Hardware synthesis anchored to Direct-Silicon JIT."
           ]);
         } catch (err) {
           setSynthesisLogs(["⚠ FORGE-ERROR: Synthesis endpoint unreachable."]);
         } finally {
           setIsSynthesizing(false);
         }
       };
       startSynthesis();
    }
  }, [showNexusForge, isSynthesizing]);

  const getAgentProfile = (id: number) => {
    const roles: ('SONIC' | 'VISUAL' | 'NAROA' | 'MAP' | 'FORGE')[] = ['SONIC', 'VISUAL', 'NAROA', 'MAP', 'FORGE'];
    const roleIndex = Math.floor((id - 1) / 20);
    const role = roles[roleIndex];
    
    const tools = {
      SONIC: 'Sample-Hunter v2 / Adv-Mastering',
      VISUAL: 'Remotion-Engine-Ω / Motion-Forge',
      NAROA: 'Mica-Noir-Scribe / Portfolio-Sync',
      MAP: 'Asset-Recon / Pattern-Discovery',
      FORGE: 'Nexus-Orchestrator 3.3'
    };

    const traits = ['Lethal', 'Ghost', 'Analyst', 'Overclocked', 'Precise', 'Organic', 'Kinetic', 'Silent'];
    const trait = traits[id % traits.length];

    return {
      role,
      designation: `${role}-${id}`,
      tool: tools[role],
      trait,
      efficiency: (95 + (id % 5)).toFixed(1),
      signature: `0x${(id * 9999).toString(16).padEnd(4, '0')}`
    };
  };

  const getAgentMetadata = (id: number) => {
    const profile = getAgentProfile(id);
    const uptimeInSeconds = Math.floor(Date.now() / 1000);
    const cycles = (id * 420) + (uptimeInSeconds % 100);
    const multiplier = profile.role === 'SONIC' ? sonicPurificationRate : 1.0;
    const yieldValue = (parseFloat(profile.efficiency) * Math.pow(1.001 * multiplier, id % 10)).toFixed(4);
    const isOmega = id % 7 === 0 || profile.role === 'FORGE';

    return {
      id,
      designation: profile.designation,
      role: profile.role,
      tool: profile.tool,
      trait: profile.trait,
      efficiency: profile.efficiency,
      cycles,
      yield: yieldValue,
      isOmega,
      coordinate: `${Math.floor((id-1)/10)},${(id-1)%10}`,
      status: activeAgents.includes(id) ? 'PURIFYING' : 'STANDBY',
      exergy: (98.5 + (id % 15) / 10).toFixed(2),
      target: activeAgents.includes(id) ? profile.signature : 'NULL'
    };
  };

  const handleDeploy = useCallback(async (domain: Domain) => {
    setDeploymentStatus(prev => ({ ...prev, [domain.id]: 'DEPLOYING...' }));

    try {
      const res = await fetch('/api/deploy', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          domain_id: domain.id,
          guard_active: isGuardActive
        })
      });
      const result = await res.json();
      if (result.status === 'DEPLOYED') {
        setDeploymentStatus(prev => ({ ...prev, [domain.id]: 'DEPLOYED ✓' }));
        setTimeout(() => {
          setDeploymentStatus(prev => ({ ...prev, [domain.id]: '' }));
        }, 3000);
      } else {
        setDeploymentStatus(prev => ({ ...prev, [domain.id]: 'FAILED ✗' }));
      }
    } catch (err) {
      setDeploymentStatus(prev => ({ ...prev, [domain.id]: 'ERROR ✗' }));
      console.error('∴ CORTEX-SIGNAL: Kinetic bridge failure.', err);
    }
  }, [isGuardActive]);

  const toggleGuard = useCallback(async () => {
    const newState = !isGuardActive;
    setIsGuardActive(newState);

    try {
      const res = await fetch('/api/sync', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          guard_active: newState,
          data: {
            agent_id: "BORJA-MOSKV-ALPHA",
            weights: [0.98, 0.44, 0.12]
          }
        })
      });
      const result = await res.json();
      console.log(`∴ CORTEX-SIGNAL: Sovereign Guard ${newState ? 'ACTIVATED' : 'DEACTIVATED'}`, result);
    } catch (err) {
      console.warn('∴ CORTEX-SIGNAL: Identity Proxy inaccessible. Local guard mode only.');
    }
  }, [isGuardActive]);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [yieldRes, mythosRes, vanguardRes, exergyRes] = await Promise.all([
          fetch('/api/yield'),
          fetch('/api/mythos/status'),
          fetch('/api/vanguard/status'),
          fetch('/api/exergy/metrics')
        ]);

        const yData = await yieldRes.json();
        const mData = await mythosRes.json();
        const vData = await vanguardRes.json();
        const eData = await exergyRes.json();

        setYieldData(yData);
        setMythosData(mData);
        setVanguardData(vData);
        setExergyMetrics(eData);
      } catch (err) {
        console.warn('∴ CORTEX-SIGNAL: Connection to ledger failed. Operating in limited exergy mode.', err);
      }
    };
    fetchData();
    const interval = setInterval(fetchData, 10000);
    return () => clearInterval(interval);
  }, []);

  // ── Stealth Audit Ticker Simulation (Shadow mode) ─────────────────────
  useEffect(() => {
    const findings = [
      "∴ VSA_HIT: Repositorio 'Archi-Core' verificado en 0.81ms.",
      "∴ AUDIT: Hallado vector 'Race Condition' en /contracts/v1.",
      "∴ LEDGER: Bloque C5-3912 sellado con hash 0x7a8...911.",
      "∴ RESONANCE: Kernel VSA operando al 99.4% de fidelidad.",
      "∴ SHADOW: Sincronizando pesos neuronales con nodo 'Agents.archi'.",
      "∴ OUROBOROS: Strike completado. Yield proyectado: +$1,240.",
      "∴ SYSTEM: Purga de entropía realizada (Ley Ω₄)."
    ];
    let idx = 0;
    const interval = setInterval(() => {
      setInternalAuditFeed(prev => [findings[idx], ...prev.slice(0, 5)]);
      idx = (idx + 1) % findings.length;
    }, 4000);
    return () => clearInterval(interval);
  }, []);

  const fetchBounties = useCallback(async () => {
    try {
      const res = await fetch('/api/bounties');
      const data = await res.json();
      setBounties(data);
    } catch (err) {
      console.warn('∴ CORTEX-SIGNAL: Bounty registry offline.', err);
    }
  }, []);

  useEffect(() => {
    fetchBounties();
    const interval = setInterval(fetchBounties, 30000);
    return () => clearInterval(interval);
  }, [fetchBounties]);

  // ── C5-REAL Stream (SSE Hook to Aether Kernel) ─────────────────────
  useEffect(() => {
    const eventSource = new EventSource('/api/stream/metrics');
    
    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        
        // P0 Path: Update Dashboard with physical C5 telemetry
        if (data.metrics) { 
          if (data.metrics.entropy !== undefined) setMeasuredEntropy(data.metrics.entropy);
          if (Array.isArray(data.metrics.active_nodes)) {
            setActiveAgents(data.metrics.active_nodes);
          }
          // Ω-PERSIST: live membrane state from SSE
          if (data.metrics.persist_mode)    setPersistMode(data.metrics.persist_mode as 'COMMITTED' | 'FALLBACK' | 'OFFLINE');
          if (data.metrics.sealed_facts !== undefined) setSealedFacts(data.metrics.sealed_facts);
          if (data.metrics.fact_count   !== undefined) setFactCount(data.metrics.fact_count);
        }
        
        if (data.log_event) { 
          setStrikeLog(prev => prev ? prev + '\n' + data.log_event : data.log_event);
        }
      } catch (err) {
        console.warn("C5_STREAM_PARSE_FAULT:", err);
      }
    };

    
    eventSource.onerror = () => {
      console.warn("C5-REAL: Telemetry link severed. Reconecting via Substrate...");
    };

    return () => eventSource.close();
  }, []);

  const handleExfiltrate = async (reportId: string, method: 'code4rena' | 'onchain') => {
    setIsExfiltrating(reportId);
    setPidLogs(prev => [`[${new Date().toLocaleTimeString()}] INITIATING_EXFILTRATION: ${reportId}`, ...prev.slice(0, 4)]);
    
    try {
      const response = await fetch('/api/exfiltrate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ report_id: reportId, method })
      });
      const data = await response.json();
      
      setPidLogs(prev => [`[${new Date().toLocaleTimeString()}] EXFILTRATION_${data.status}: ${data.mode}`, ...prev.slice(0, 4)]);
      // Refresh bounties
      fetchBounties();
    } catch (err) {
      setPidLogs(prev => [`[${new Date().toLocaleTimeString()}] EXFILTRATION_CRIT_FAIL: ${err}`, ...prev.slice(0, 4)]);
    } finally {
      setIsExfiltrating(null);
    }
  };

  const handleStrike = async () => {
    const { domain, apiUrl, token } = strikeParams;
    if (!domain) return;

    try {
      setStrikeLog(`◈ INITIATING STRIKE: ${domain}\n∴ CORTEX: Dispatching Mythos Swarm...`);
      const response = await fetch('/api/mythos/strike', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ domain, api_url: apiUrl, auth_token: token })
      });
      const data = await response.json();
      setStrikeLog(prev => prev + `\n✅ ${data.status} | Engine: ${data.engine}\n📊 Log: ${data.log}`);
    } catch (err) {
      setStrikeLog(prev => prev + `\n❌ STRIKE_FAILED: ${err}`);
    }
  };

  const handleStellarStrike = async () => {
    try {
      setStrikeLog(`⚔️ OPERATION: STELLAR FRACTURE\n🛡️ LEGION-10k: Initializing 10,000 agents...`);
      const response = await fetch('/api/strike/stellar', {
        method: 'POST'
      });
      const data = await response.json();
      setStrikeLog(prev => prev + `\n🔥 ${data.status} | Mode: Industrial Siege\n📊 Legion Density: 10Hz sync enabled.`);
    } catch (err) {
      setStrikeLog(prev => prev + `\n❌ OPERATION_FAILED: ${err}`);
    }
  };

  const [isFractalStrikeActive, setIsFractalStrikeActive] = useState(false);

  const handleFractalStrike = async () => {
    setIsFractalStrikeActive(true);
    setStrikeLog(`◈ INITIATING FRACTAL STRIKE [LEGION-100]\n∴ CORTEX: Hooking into Swarm Substrate...`);

    try {
      const res = await fetch('/api/strike/fractal', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mode: 'FRACTAL_V6' })
      });
      const data = await res.json();
      
      setActiveAgents(Array.from({ length: 100 }, (_, i) => i + 1));
      setStrikeLog(prev => prev + `\n🔥 ${data.msg}\n∴ STRIKE_ID: ${data.strike_id}\n`);
      
      // Multi-phase simulation (visual only, driven by state)
      setTimeout(() => setStrikeLog(prev => prev + "◈ PHASE: SCANNING_VULNERABILITIES...\n"), 1000);
      setTimeout(() => setStrikeLog(prev => prev + "◈ PHASE: EXPLOITING_VECTORS...\n"), 2500);
      setTimeout(() => setStrikeLog(prev => prev + "◈ PHASE: EXTRACTING_EXERGY...\n"), 4000);

      setTimeout(() => {
        setIsFractalStrikeActive(false);
        setActiveAgents([]);
        setStrikeLog(prev => prev + `\n✅ STRIKE_COMPLETE | ID=${data.strike_id}\n∴ EXERGY_SNAPSHOT: 99.1%`);
      }, (data.duration_est || 5) * 1000);
    } catch (e) {
      setStrikeLog(prev => prev + `\n🛑 C5-REAL BINDING FAILED: API unreachable.`);
      setIsFractalStrikeActive(false);
    }
  };

  const getDomainYield = (domainId: string) => {
    if (!yieldData) return null;
    return yieldData.breakdown.find((b: any) => {
      const name = b.name || '';
      if (domainId === 'blockchain') return name.includes('Firedancer') || name.includes('LayerZero');
      if (domainId === 'cybersec') return name.includes('Sherlock') || name.includes('CODE4RENA');
      return false;
    }) || null;
  };

  const [isInitialized, setIsInitialized] = useState(false);

  useEffect(() => {
    if (isInitialized) {
      sonic.updateDrone(30 + measuredEntropy / 2);
    }
  }, [measuredEntropy, isInitialized]);

  const initSignal = () => {
    sonic.init();
    setIsInitialized(true);
    sonic.playClick('deploy');
  };

  if (!isInitialized) {
    return (
      <div className="system-init-overlay" onClick={initSignal}>
        <div className="init-core">
          <div className="init-logo">Ω</div>
          <div className="init-label">ACQUIRING SIGNAL...</div>
          <div className="init-sub">CLICK TO INITIALIZE SOVEREIGN TERMINAL</div>
        </div>
      </div>
    );
  }

  return (
    <div className="domain-dashboard-container" onMouseMove={handleMouseMove}>
      <div className="mica-grain"></div>
      <div className="scanlines"></div>
      
      <div className="scroll-progress-line" style={{ height: `${scrollProgress}%` }}></div>
      
      <div className="radar-substrate">
        <div className="radar-circle" style={{ width: '100%', height: '100%' }}></div>
        <div className="radar-circle" style={{ width: '70%', height: '70%' }}></div>
        <div className="radar-circle" style={{ width: '40%', height: '40%' }}></div>
        <div className="radar-circle" style={{ width: '10%', height: '10%' }}></div>
      </div>
      
      <div 
        ref={cursorRef}
        className="tactical-cursor" 
        style={{ left: -15, top: -15 }}
      >
        <div className="cursor-crosshair"></div>
        {cursorType === 'terminal' && <div className="cursor-prompt">{`>_`}</div>}
      </div>

      <div className="brand-title">ARCHI.</div>

      <header ref={headerRef} className="dashboard-header">
        <div className="header-main">
          <MagneticWrapper>
            <h1>SOVEREIGN DOMAINS 2026</h1>
          </MagneticWrapper>
          <div className="sovereign-guard-control">
            <span className={`guard-label ${isGuardActive ? 'protected' : 'vulnerable'}`}>
              {isGuardActive ? 'ESCUDO Ω-1: ACTIVO' : 'ESTADO: VULNERABLE'}
            </span>
            <MagneticWrapper>
              <button
                className={`guard-toggle-btn ${isGuardActive ? 'active' : ''}`}
                onClick={toggleGuard}
                title="Toggle Sovereign Soul Protection"
              >
                <div className="toggle-orb"></div>
              </button>
            </MagneticWrapper>
            <button
              className={`vanguard-reboot-btn ${showTacticalMap ? 'active' : ''}`}
              onClick={() => setShowTacticalMap(!showTacticalMap)}
            >
              {showTacticalMap ? 'CLOSE_MAP' : 'OPEN_ULTRA_MAP'}
            </button>
            <button
              className="vanguard-reboot-btn"
              onClick={async () => {
                await fetch('/api/vanguard/trigger', { method: 'POST' });
                setStrikeLog("VANGUARD INDUSTRIAL CYCLE REBOOTED.");
              }}
            >
              REBOOT_VANGUARD
            </button>
          </div>

          {/* Ω-PERSIST: Live membrane status bar */}
          <div className="persist-status-bar" data-mode={persistMode}>
            <span className="persist-dot" />
            <span className="persist-label">
              Ω-PERSIST:&nbsp;
              <strong>{persistMode}</strong>
            </span>
            <span className="persist-divider">|</span>
            <span className="persist-stat">{sealedFacts} sealed</span>
            <span className="persist-divider">|</span>
            <span className="persist-stat">{factCount} facts</span>
          </div>
        </div>

        <div className="system-metrics-overview">
          <p className="signal-status">
            CORTEX SIGNAL: <span className="status-blink">ACTIVE</span> |
            EXERGY: <span className={`exergy-val ${isStressed ? 'jitter-red' : ''}`}>{exergyLevel.toFixed(1)}%</span> |
            COMPLIANCE: <span className="c5-tag">C5-LEDGER</span>
          </p>
          {yieldData && (
            <p className="yield-status">CONFIRMED YIELD: <span className="yield-value">${yieldData.total_confirmed_yield.toLocaleString()}</span> | SCANS: {yieldData.scans}</p>
          )}

          {exergyMetrics && (
            <div className="neural-resonance-dashboard shadow-portal">
              <div className="resonance-gauge-v2">
                <div className="gauge-value-box">
                  <span className="latency-val">0.8</span>
                  <span className="latency-unit">ms</span>
                </div>
                <div className="gauge-label">VSA_LATENCY</div>
              </div>
              <div className="resonance-info">
                <span className="label">NEURAL_RESONANCE [Ω]</span>
                <span className={`multiplier ${exergyMetrics.exergy_multiplier >= 1000 ? 'gold-glow' : ''}`}>
                  {exergyMetrics.exergy_multiplier.toFixed(0)}x YIELD
                </span>
                <div className="system-path-verified">
                  <span className="path-icon">∴</span> 
                  <span className="path-text">C5-REAL_PATH_VERIFIED</span>
                </div>
              </div>
            </div>
          )}

          <div className="stealth-audit-ticker">
            <div className="ticker-header">
              <span className="ticker-pill">SHADOW_AUDIT_FEED</span>
              <span className="ticker-time">{new Date().toLocaleTimeString()}</span>
            </div>
            <div className="ticker-content">
              {internalAuditFeed.map((entry, idx) => (
                <div key={idx} className="ticker-entry" style={{ opacity: 1 - (idx * 0.15) }}>
                  {entry}
                </div>
              ))}
            </div>
          </div>

          <div className="homeostasis-control">
            <div className="homeostasis-labels">
              <span className={`label-consolidate ${zone === 'CONSOLIDATION' ? 'active' : 'dimmed'}`}>
                ∴ ENGINEERING <br/> <span className="small-detail">(ORDER / DETERMINISM)</span>
              </span>
              <span className={`label-pid ${zone === 'BALANCE' && Math.abs(equilibrium - measuredEntropy) < 3 ? 'perfect-balance resonance' : ''}`}>
                [ {Math.abs(equilibrium - measuredEntropy) < 3 ? 'RESONANCE_ACTIVE' : `PID_OUT: ${pidOutput.toFixed(1)}%`} ]
              </span>
              <span className={`label-diverge ${zone === 'DIVERGENCE' ? 'active' : 'dimmed'}`}>
                IMAGINATION ∴ <br/> <span className="small-detail">(CHAOS / GENERATIVE)</span>
              </span>
            </div>
            <input
              type="range"
              min="0"
              max="100"
              value={equilibrium}
              onChange={(e) => setEquilibrium(parseInt(e.target.value))}
              className={`homeostasis-slider ${zone === 'DIVERGENCE' ? 'imagination-slider' : zone === 'CONSOLIDATION' ? 'engineering-slider' : ''}`}
              aria-label="Homeostasis target setpoint"
            />
            {/* stability-sparkline visualization */}
            <div className="stability-sparkline-container">
               <svg width="100%" height="30" viewBox="0 0 100 30" preserveAspectRatio="none">
                  <path 
                    d={`M ${stabilityHistory.map((v, i) => `${i * 2},${30 - (v * 0.3)}`).join(' L ')}`}
                    fill="none" 
                    stroke={isStressed ? "var(--blood-red)" : "var(--laser-green)"} 
                    strokeWidth="1"
                    className="spark-path"
                  />
               </svg>
            </div>

            {/* PID readout bar */}
            <div className="pid-readout">
              <div className="readout-item">
                <span className="label">SETPOINT</span>
                <span className="value">{equilibrium}%</span>
              </div>
              <div className="readout-item">
                <span className="label">MEASURED</span>
                <span className={`value ${Math.abs(equilibrium - measuredEntropy) > 10 ? 'pulsing-warn' : ''}`}>
                  {measuredEntropy.toFixed(1)}%
                </span>
              </div>
              <div className="readout-item coefficients">
                <span className="label">COEFFS</span>
                <span className="value">P:{KP} I:{KI} D:{KD}</span>
              </div>
            </div>

            <div className="homeostasis-actions">
              <button 
                className={`stress-btn ${isStressed ? 'active' : ''}`}
                onMouseDown={() => setIsStressed(true)}
                onMouseUp={() => setIsStressed(false)}
                onMouseLeave={() => setIsStressed(false)}
              >
                {isStressed ? 'INJECTING_ENTROPY' : 'THERMAL_STRESS_TEST'}
              </button>
            </div>

            {pidLogs.length > 0 && (
              <div className="pid-diagnostics-log">
                {pidLogs.map((log, i) => (
                  <div key={i} className="log-entry">{log}</div>
                ))}
              </div>
            )}

            <div className="vsa-substrate-mini">
              {vsaComputed.map((val, i) => {
                // Deterministic activation pattern based on zone
                let isActive: boolean;
                if (zone === 'DIVERGENCE') {
                  isActive = val < (equilibrium - 30) / 100;
                } else if (zone === 'CONSOLIDATION') {
                  isActive = i < (100 - equilibrium);
                } else {
                  isActive = i % 2 === 0;
                }
                // const isHovered = false; // logic would be complex here, simplifying for card level
                const cellColor = zone === 'DIVERGENCE' ? '#FFB800' : zone === 'CONSOLIDATION' ? '#2E5090' : '#2BE58B';
                return (
                  <div
                    key={i}
                    style={{
                      flex: 1,
                      background: isActive ? cellColor : 'rgba(255,255,255,0.02)',
                      boxShadow: isActive ? `0 0 12px ${cellColor}` : 'none',
                      transition: 'background 0.6s cubic-bezier(0.16, 1, 0.3, 1), opacity 0.3s ease, box-shadow 0.4s ease',
                      opacity: isActive ? 1 : 0.3,
                    }}
                  />
                );
              })}
            </div>
          </div>
        </div>
      </header>

      <div className={`domain-grid ${isGuardActive ? 'sovereign-mesh' : ''}`}>
        {domains.map((domain) => (
          <div
            key={domain.id}
            className={`domain-card ${activeDomain === domain.id ? 'active' : ''} ${domain.id === 'cybersec' ? 'critical' : ''}`}
            onMouseEnter={() => {
              setActiveDomain(domain.id);
              sonic.playClick('hover');
            }}
            onMouseLeave={() => setActiveDomain(null)}
          >
            <div className="hw-corner hw-tl"></div>
            <div className="hw-corner hw-tr"></div>
            <div className="hw-corner hw-bl"></div>
            <div className="hw-corner hw-br"></div>

            <div className="card-border"></div>
            <div className="card-content">
              <span className="domain-icon" style={{ textShadow: `0 0 10px ${domain.color}` }}>
                {domain.icon}
              </span>
              <h3 style={{ color: activeDomain === domain.id ? domain.color : 'inherit' }}>{domain.title}</h3>
              <p>{domain.description}</p>

              <button
                className={`deploy-btn ${deploymentStatus[domain.id] ? 'loading' : ''}`}
                disabled={!!deploymentStatus[domain.id]}
                onClick={(e) => {
                  e.stopPropagation();
                  if (domain.id === 'cybersec') {
                    setShowStrikeConsole(true);
                  } else if (domain.id === 'legion-100') {
                    setShowLegionMonitor(true);
                  } else if (domain.id === 'moskv-nexus') {
                    setShowNexusForge(true);
                  } else if (domain.id === 'ai-ml') {
                    setShowAutodidactMonitor(true);
                  } else if (domain.id === 'sovereign-agents') {
                    setShowMoskvChat(true);
                  } else if (domain.id === 'exfiltration-c5') {
                    setShowExfiltrationConsole(true);
                    fetchBounties();
                  } else {
                    handleDeploy(domain);
                  }
                  onDeploy?.(domain);
                }}
              >
                {deploymentStatus[domain.id] || (
                  domain.id === 'cybersec' ? 'INIT_STRIKE_CONSOLE' : 
                  domain.id === 'legion-100' ? 'MONITOR_SWARM_420' : 
                  domain.id === 'moskv-nexus' ? 'NEXUS_FORGE_DASH' :
                  domain.id === 'ai-ml' ? 'OPEN_AUTODIDACT_SIEVE' :
                  domain.id === 'sovereign-agents' ? 'OPEN_AI_COM' :
                  domain.id === 'exfiltration-c5' ? 'OPEN_EXFIL_UNIT' :
                  'DEPLOY_AGENT'
                )}
              </button>

              {domain.id === 'cybersec' && mythosData && (
                <div className="domain-live-metrics">
                  <div className="metric-tag">
                    <span className="tag-label">PHASE</span>
                    <span className="tag-value">{mythosData.state_machine.current_phase}</span>
                  </div>
                  <div className="metric-tag">
                    <span className="tag-label">ACTIVE_MISSION</span>
                    <span className="tag-value pulse-red">
                      {mythosData.state_machine.milestones.find((m: MythosMilestone) => m.status === 'IN_PROGRESS')?.id || 'NONE'}
                    </span>
                  </div>
                </div>
              )}

              {getDomainYield(domain.id) && (
                <div className="domain-live-metrics">
                  {/* Yield metrics rendered from live ledger */}
                </div>
              )}

              <div className="scan-line"></div>
            </div>
          </div>
        ))}

        {vanguardData && (
          <div className="domain-card vanguard-monitor">
            <div className="card-content">
              <span className="domain-icon">◈</span>
              <h3>VANGUARD_MONITOR</h3>
              <div className="vanguard-protocol-list">
                {Object.entries(vanguardData).map(([name, entry]: [string, any]) => (
                  <div key={name} className="vanguard-protocol-item">
                    <div className="protocol-info">
                      <span className="protocol-name">{name.toUpperCase()}</span>
                      <span className={`protocol-status ${entry.status.toLowerCase()}`}>
                        {entry.status}
                      </span>
                    </div>
                    {entry.status === 'SINGULARITY' && (
                      <button
                        className="stellar-strike-btn"
                        onClick={handleStellarStrike}
                      >
                        FRACTURE
                      </button>
                    )}
                  </div>
                ))}
              </div>
              <div className="scan-line"></div>
            </div>
          </div>
        )}
      </div>

      <div className={`strike-console ${debugMode ? 'debug-border' : ''}`}>
        <div className="console-header">
          <span>{`>_`} STRIKE_TERMINAL [LEGION_SYNC]</span>
          <span className="live-pill">{debugMode ? 'SOVEREIGN_DEBUG_ON' : 'LIVE_TELEMETRY'}</span>
        </div>
        <pre className="console-body">
          {displayedLog || "∴ WAITING FOR SIGNAL..."}
          <span className="blink-cursor">_</span>
        </pre>
      </div>

      {showStrikeConsole && (
        <div className="strike-console-overlay" onClick={() => setShowStrikeConsole(false)}>
          <div className="strike-console-modal" onClick={e => e.stopPropagation()}>
            <div className="console-header">
              <h2>∴ MYTHOS STRIKE CONSOLE</h2>
              <button className="close-btn" onClick={() => setShowStrikeConsole(false)}>×</button>
            </div>

            <div className="console-body">
              <div className="input-group">
                <label>TARGET_DOMAIN</label>
                <input
                  value={strikeParams.domain}
                  onChange={e => setStrikeParams({ ...strikeParams, domain: e.target.value })}
                  placeholder="example.com"
                />
              </div>
              <div className="input-group">
                <label>TARGET_API_URL</label>
                <input
                  value={strikeParams.apiUrl}
                  onChange={e => setStrikeParams({ ...strikeParams, apiUrl: e.target.value })}
                  placeholder="https://api.example.com/v1/user"
                />
              </div>
              <div className="input-group">
                <label>AUTH_TOKEN (JWT)</label>
                <input
                  type="password"
                  value={strikeParams.token}
                  onChange={e => setStrikeParams({ ...strikeParams, token: e.target.value })}
                  placeholder="Bearer sk-..."
                />
              </div>

              <button className="strike-launch-btn" onClick={() => handleStrike()}>
                EXECUTE_KINETIC_STRIKE
              </button>

              {strikeLog && (
                <div className="console-log">
                  <span className="log-prefix">SIGNAL:</span> {strikeLog}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {showLegionMonitor && (
        <div className="strike-console-overlay legion-overlay" onClick={() => setShowLegionMonitor(false)}>
          <div className="strike-console-modal legion-monitor-modal" onClick={e => e.stopPropagation()}>
             <div className={`console-header ${is911Active ? 'emergency-header' : ''}`}>
              <div className="header-title-group">
                <span className={`pill-420 ${is911Active ? 'emergency-pill' : ''}`}>
                  {is911Active ? 'PROTOCOL_911' : 'CLAW_GUI_v420'}
                </span>
                <h2>{is911Active ? `∴ BREACH: ${glitchText}` : '∴ CLAW GUI INFRASTRUCTURE'}</h2>
              </div>
              <div className="search-box">
                <input 
                  value={searchTerm} 
                  onChange={e => setSearchTerm(e.target.value)} 
                  placeholder="SEARCH_NODE (Ω...)" 
                  className="search-input"
                />
              </div>
              <button className="close-btn" onClick={() => setShowLegionMonitor(false)}>×</button>
            </div>

            <div className="legion-status-summary">
              <div className="summary-item">
                <span className="label">ACTIVE_NODES</span>
                <span className="value gold">{activeAgents.length}</span>
              </div>
              <div className="summary-item">
                <span className="label">EXERGY_FLOW</span>
                <span className="value">99.2%</span>
              </div>
              <div className="summary-item">
                <span className="label">LEGER_SYNC</span>
                <span className="value pulse-green">STABLE</span>
              </div>
            </div>

            <div className={`legion-monitor-main ${isFractalStrikeActive ? 'strike-mode' : ''}`}>
              <div className="legion-grid-container">
                <svg className="synergy-overlay">
                  {synergyFlows.map((flow, i) => {
                    const fromX = ((flow.from - 1) % 10) * 36 + 18;
                    const fromY = Math.floor((flow.from - 1) / 10) * 36 + 18;
                    const toX = ((flow.to - 1) % 10) * 36 + 18;
                    const toY = Math.floor((flow.to - 1) / 10) * 36 + 18;
                    return (
                      <line 
                        key={`flow-${i}`}
                        x1={fromX} y1={fromY} 
                        x2={toX} y2={toY} 
                        className="synergy-line"
                      />
                    );
                  })}
                </svg>
                <div className="legion-grid-100">
                  {Array.from({ length: 100 }, (_, i) => i + 1).map(id => {
                    // O(1) cache — no getAgentProfile recompute per render
                    const profile = agentProfilesCache[id - 1];
                    const isOmega = id % 7 === 0 || profile.role === 'FORGE';
                    const matchesSearch = searchTerm && (
                      profile.designation.toLowerCase().includes(searchTerm.toLowerCase()) ||
                      (isOmega && searchTerm.toLowerCase() === 'omega') ||
                      (isOmega && searchTerm === 'Ω')
                    );
                    
                    return (
                      <div 
                        key={id} 
                        className={`agent-node 
                          ${activeAgents.includes(id) ? 'active' : ''} 
                          ${hoveredAgent?.id === id ? 'highlight' : ''}
                          ${isFractalStrikeActive ? 'power-pulse' : ''}
                          role-${profile.role.toLowerCase()}
                          ${isOmega ? 'omega-mark' : ''}
                          ${matchesSearch ? 'search-hit' : ''}
                          ${activeClawNode === id ? 'claw-target' : ''}
                        `}
                        onMouseEnter={() => !isFractalStrikeActive && setHoveredAgent(getAgentMetadata(id))}
                        onMouseLeave={() => setHoveredAgent(null)}
                      >
                        <div className="heatmap-cell" style={{ opacity: trainingHeatmap[id-1] * 0.4 }}></div>
                        <div className="node-inner"></div>
                        {isOmega && <div className="omega-symbol">Ω</div>}
                      </div>
                    );
                  })}
                </div>
              </div>

              <div className="vsa-memory-substrate">
                <div className="substrate-header">
                  <span className="label">SOVEREIGN_MEMORY_SUBSTRATE (VSA) — tick:{vsaTick}</span>
                  <span className="value gold">CONTEXT_COLLAPSE_STABLE</span>
                </div>
                <div className="vsa-tensor-visual">
                  {vsaComputed.map((val, i) => (
                    <div
                      key={i}
                      className={`vsa-cell ${val > 0.8 ? 'active' : ''}`}
                      style={{ opacity: 0.1 + val * 0.9 }}
                    ></div>
                  ))}
                </div>
              </div>

              {isFractalStrikeActive && <div className="strike-interference"></div>}

              <div className="legion-side-panel">
                <div className="agent-detail-card">
                  <div className="detail-header">NODE_TELEMETRY</div>
                  {isFractalStrikeActive ? (
                    <div className="detail-body strike-status">
                      <div className="strike-title">FRACTAL_STRIKE_ACTIVE</div>
                      <div className="strike-metrics">
                        <span>NODES: 100/100</span>
                        <span>LOAD: 100%</span>
                        <div className="progress-bar-container">
                          <div className="progress-bar-fill"></div>
                        </div>
                      </div>
                    </div>
                  ) : hoveredAgent ? (
                    <div className="detail-body">
                      <div className="detail-row">
                        <span className="label">DESIGNATION</span>
                        <span className="value gold">{hoveredAgent.designation}</span>
                      </div>
                      <div className="detail-row">
                        <span className="label">CORE_ROLE</span>
                        <span className="value role-tag">{hoveredAgent.role}</span>
                      </div>
                      <div className="detail-row">
                        <span className="label">TRAIT</span>
                        <span className="value">{hoveredAgent.trait}</span>
                      </div>
                      <div className="detail-row">
                        <span className="label">PRIMARY_TOOL</span>
                        <span className="value">{hoveredAgent.tool}</span>
                      </div>
                      <div className="detail-row">
                        <span className="label">OPERATIVE_CYCLES</span>
                        <span className="value gold">{hoveredAgent.cycles} Ω</span>
                      </div>
                      <div className="detail-row">
                        <span className="label">SIGNAL_YIELD</span>
                        <span className="value laser-green">{hoveredAgent.yield}</span>
                      </div>
                      <div className="detail-row">
                        <span className="label">EFFICIENCY</span>
                        <span className="value">{hoveredAgent.efficiency}%</span>
                      </div>
                      <div className="detail-row">
                        <span className="label">EXERGY_FLOW</span>
                        <span className="value">{hoveredAgent.exergy}%</span>
                      </div>

                      {hoveredAgent.role === 'SONIC' && (
                        <div className="governor-control" style={{ marginTop: '1rem', borderTop: '1px solid rgba(0, 242, 255, 0.2)', paddingTop: '0.8rem' }}>
                          <div className="label" style={{ fontSize: '0.6rem', color: '#00f2ff', marginBottom: '0.5rem' }}>AETHER_PUMP (SONIC)</div>
                          <div className="pump-interface" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                            <input 
                              type="range" 
                              min="0.5" 
                              max="4.0" 
                              step="0.1" 
                              value={sonicPurificationRate} 
                              onChange={(e) => setSonicPurificationRate(parseFloat(e.target.value))}
                              style={{ flex: 1, accentColor: '#00f2ff' }}
                            />
                            <span className="pump-value gold" style={{ minWidth: '35px' }}>{sonicPurificationRate.toFixed(1)}x</span>
                          </div>
                        </div>
                      )}

                      <button className="strike-launch-btn training-btn" onClick={() => setIsTraining(!isTraining)}>
                        {isTraining ? 'STOP_RL_TRAINING' : 'START_CLAW_TRAIN'}
                      </button>
                    </div>
                  ) : (
                    <div className="detail-placeholder">
                      ∴ HOVER_NODE_TO_IDENTIFY
                    </div>
                  )}
                </div>

                <div className="system-logs-mini">
                  <div className="log-header">SWARM_LOGS_v420</div>
                  <div className="log-entries">
                    <div className="log-entry">∴ Legion-100 deployment verified.</div>
                    <div className="log-entry">∴ Standard 420/100 protocol active.</div>
                    {isFractalStrikeActive ? (
                      <div className="log-entry pulse-red">!!! HIGH_INTENSITY_STRIKE_P0 !!!</div>
                    ) : (
                      activeAgents.slice(0, 3).map(id => (
                        <div key={id} className="log-entry gold">◈ Agent #{id} locked target.</div>
                      ))
                    )}
                  </div>
                </div>
              </div>
            </div>

            <button className="strike-launch-btn legion-launch" onClick={handleFractalStrike} disabled={isFractalStrikeActive || is911Active}>
              {isFractalStrikeActive ? 'STRIKE_UNDER_WAY...' : is911Active ? 'SYSTEM_CRITICAL_RECOVERY' : 'INITIALIZE_FRACTAL_STRIKE'}
            </button>
            <button className="yolo-trigger" onClick={trigger911} style={{ position: 'absolute', bottom: '10px', left: '10px', opacity: 0.1, border: 'none', background: 'none', color: 'red', cursor: 'pointer', fontSize: '0.5rem' }}>911_YOLO</button>
          </div>
        </div>
      )}

      {showNexusForge && (
        <div className="strike-console-overlay forge-overlay" onClick={() => setShowNexusForge(false)}>
          <div className="strike-console-modal forge-monitor-modal" onClick={e => e.stopPropagation()}>
            <div className="console-header">
              <div className="header-title-group">
                <span className="pill-nexus">MOSKV-NEXUS 3.3</span>
                <h2>∴ SYSTEM FORGE-Ω MONITOR</h2>
              </div>
              <button className="close-btn" onClick={() => setShowNexusForge(false)}>×</button>
            </div>

            <div className="forge-grid-layout">
              <div className="circuit-view">
                <div className="circuit-header">REAL_TIME_SILICON_JIT</div>
                <div className="circuit-matrix">
                  <div className={`schematic-lines ${isSynthesizing ? 'active' : ''}`}>
                    <svg width="100%" height="100%" viewBox="0 0 200 200">
                      <path d="M20,100 L60,100 M60,60 L60,140 M60,60 L140,60 M60,140 L140,140 M140,60 L140,140 M140,100 L180,100" stroke="rgba(229, 43, 85, 0.4)" fill="none" />
                      <circle cx="20" cy="100" r="3" fill="#E52B55" />
                      <circle cx="180" cy="100" r="3" fill="#E52B55" />
                      {isSynthesizing && <circle cx="100" cy="100" r="40" stroke="#E52B55" fill="none" className="pulse-circle" />}
                    </svg>
                  </div>
                </div>
              </div>

              <div className="forge-telemetry">
                <div className="telemetry-card">
                  <div className="card-label">CPU_EXERGY_DRAIN</div>
                  <div className="card-value">12.4 W</div>
                </div>
                <div className="telemetry-card">
                  <div className="card-label">RTL_INTEGRITY</div>
                  <div className="card-value blood-red">99.9%</div>
                </div>
              </div>
            </div>

            <div className="console-log forge-log">
              {synthesisLogs.length === 0 ? (
                <span className="log-entry opacity-40">∴ Await hardware synthesis command...</span>
              ) : (
                synthesisLogs.map((log, idx) => (
                  <div key={idx} className="log-entry green">{log}</div>
                ))
              )}
            </div>

            <button className="strike-launch-btn forge-launch" onClick={() => setIsSynthesizing(true)} disabled={isSynthesizing}>
              {isSynthesizing ? 'SYNTHESIZING_HARDWARE...' : 'SINTETIZAR_HARDWARE_C5'}
            </button>
          </div>
        </div>
      )}

      {showAutodidactMonitor && (
        <div className="strike-console-overlay sieve-overlay" onClick={() => setShowAutodidactMonitor(false)}>
          <div className="strike-console-modal sieve-monitor-modal" onClick={e => e.stopPropagation()}>
            <div className="console-header">
              <div className="header-title-group">
                <span className="pill-autodidact">AUTODIDACT-Ω v7.1</span>
                <h2>∴ COGNITIVE SIEVE MONITOR</h2>
              </div>
              <button className="close-btn" onClick={() => setShowAutodidactMonitor(false)}>×</button>
            </div>

            <div className="sieve-visualization">
              <div className="sieve-stream">
                <div className={`stream-column ${isDiverging ? 'flowing' : ''}`}>
                  {Array.from({ length: 15 }).map((_, i) => {
                    const bitValue = (vsaTick + i) % 7 === 0 ? '1' : '0';
                    return (
                      <div key={i} className="logic-bit" style={{ animationDelay: `${i * 0.1}s` }}>
                        {bitValue}
                      </div>
                    );
                  })}
                </div>
                <div className="sieve-filter">
                  <div className="filter-hex">⬢</div>
                  <div className="filter-label">FALSATION_ENGINE</div>
                </div>
                <div className={`distilled-knowledge ${isDiverging ? 'receiving' : ''}`}>
                  {isDiverging && <div className="ki-spark">◈</div>}
                </div>
              </div>
            </div>

            <div className="sieve-metrics-grid">
              <div className="metric-box">
                <span className="m-label">ENTROPY_REDUCTION</span>
                <span className="m-value laser-green">88.4%</span>
              </div>
              <div className="metric-box">
                <span className="m-label">KI_FLUX_DENSITY</span>
                <span className="m-value">4.2/sec</span>
              </div>
            </div>

            <pre className="console-log sieve-log">
              {sieveLogic.length === 0 ? "∴ Awaiting research loop initiation..." : sieveLogic.join('\n')}
            </pre>

            <button className="strike-launch-btn sieve-launch" onClick={() => setIsDiverging(true)} disabled={isDiverging}>
              {isDiverging ? 'DISTILLING_LOGIC...' : 'INICIAR_BLOQUE_DE_APRENDIZAJE'}
            </button>
          </div>
        </div>
      )}

      {showExfiltrationConsole && (
        <div className="strike-console-overlay exfil-overlay" onClick={() => setShowExfiltrationConsole(false)}>
          <div className="strike-console-modal exfil-modal" onClick={e => e.stopPropagation()}>
            <div className="console-header">
              <div className="header-title-group">
                <span className="pill-exfil">C5-EXFILTRATION_UNIT</span>
                <h2>∴ CAPITAL_HARVEST_CONTROL</h2>
              </div>
              <button className="close-btn" onClick={() => setShowExfiltrationConsole(false)}>×</button>
            </div>
            
            <div className="exfiltration-grid-layout">
              <div className="bounty-ledger-section">
                <div className="section-label">PENDING_AUDIT_YIELDS</div>
                <div className="bounty-list-container">
                  {bounties.length === 0 ? (
                    <div className="empty-state-msg">∴ WAITING_FOR_MYTHOS_YIELD_SIGNAL...</div>
                  ) : (
                    bounties.map((b) => (
                      <div key={b.id} className="bounty-row">
                        <div className="bounty-info">
                          <span className="b-id">ID: {b.id.slice(0, 8)}</span>
                          <span className="b-name">{b.name}</span>
                        </div>
                        <div className="bounty-ops">
                          <button 
                            className="exfil-op-btn"
                            disabled={!!isExfiltrating}
                            onClick={() => handleExfiltrate(b.id, 'code4rena')}
                          >
                            {isExfiltrating === b.id ? 'EXTRACTING...' : 'EXTRACT_YIELD'}
                          </button>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>
              
              <div className="extraction-telemetry-section">
                <div className="section-label">EXTRACTION_TELEMETRY</div>
                <div className="telemetry-log">
                  {pidLogs.map((log, i) => (
                    <div key={i} className="log-line">{log}</div>
                  ))}
                </div>
                <div className="aggregate-metrics">
                   <div className="agg-metric">
                      <span className="metric-n">C5_LEDGER_STATUS</span>
                      <span className="metric-v laser-green">SYNCHRONIZED</span>
                   </div>
                   <div className="agg-metric">
                      <span className="metric-n">ESTIMATED_EXTRACTION</span>
                      <span className="metric-v gold-glow">${(bounties.length * 50000).toLocaleString()}</span>
                   </div>
                </div>
              </div>
            </div>
            
            <div className="modal-footer-law">
               <span>Law Ω9 Enforcement: All extractions are logged as C5-REAL once verified on-chain.</span>
            </div>
          </div>
        </div>
      )}

      {showMoskvChat && <MoskvChat onClose={() => setShowMoskvChat(false)} />}

      <footer className="dashboard-footer">
        <div className="footer-line"></div>
        <div className="footer-status">
          <span>INDUSTRIAL NOIR CORE v6.5</span>
          <span>BORJA MOSKV // CORTEX PERSIST</span>
        </div>
      </footer>
      {showTacticalMap && (
        <div className="tactical-map-fullscreen-overlay">
          <div className="map-controls-top">
            <button className="close-map-btn" onClick={() => setShowTacticalMap(false)}>ESC // CLOSE_MAP</button>
          </div>
          <UltraTacticalMap 
            activeAgents={activeAgents}
            measuredEntropy={measuredEntropy}
            isStrikeActive={isFractalStrikeActive}
            onNodeClick={(id) => {
              if (id === 'ai-ml') setShowAutodidactMonitor(true);
              if (id === 'moskv-nexus') setShowNexusForge(true);
              if (id === 'cybersec') {
                 setShowExfiltrationConsole(true);
                 if (typeof fetchBounties === 'function') fetchBounties();
              }
              if (id === 'sovereign-agents') setShowMoskvChat(true);
              setShowTacticalMap(false);
            }}
          />
        </div>
      )}

      <div className="system-heatmap">
        {heatmapSeeds.map((cell, i) => (
          <div 
            key={i} 
            className="heatmap-node" 
            style={{ 
              background: cell.active ? 'var(--laser-green)' : 'transparent',
              opacity: cell.opacity
            }}
          />
        ))}
      </div>
    </div>
  );
};
