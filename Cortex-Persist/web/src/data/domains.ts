export interface DomainConfig {
  id: string;
  title: string;
  description: string;
  icon: string;
  color: string;
  type?: 'primary' | 'secondary' | 'critical';
}

export const domains: DomainConfig[] = [
  {
    id: 'cybersec',
    title: 'strike.layerzero',
    description: 'extracción tri-strike contra layerzero stellar. reporte de fee theft, treasury dos y nonce bloat. c5-real inminente.',
    icon: '⚔️',
    color: '#E52B2B',
    type: 'critical'
  },
  {
    id: 'moskv-nexus',
    title: 'moskv.nexus',
    description: 'identidad soberana y forja de alta fidelidad. purificación mica noir v6.0 instalada. silencio de protocolo activo.',
    icon: 'Ω',
    color: '#FFFFFF'
  },
  {
    id: 'ai-ml',
    title: 'autodidact.sieve',
    description: 'procesamiento semántico autónomo. extracción de exergía mediante análisis sintáctico de ast (v3.2).',
    icon: '🧠',
    color: '#2BE58B'
  },
  {
    id: 'sovereign-agents',
    title: 'agents.archi',
    description: 'sistema operativo agéntico (aos) y registro de axiomas. orquestación de enjambres soberanos bajo mica noir v6.0.',
    icon: '◈',
    color: '#2B3BE5'
  },
  {
    id: 'exfiltration-c5',
    title: 'c5.exfiltrate',
    description: 'unidad de exfiltración de capital verificado (c5-real). nexo de liquidez directa y bypass de simulación.',
    icon: '💰',
    color: '#2BE58B'
  },
  {
    id: 's0p-governor',
    title: 's0p.governor',
    description: 'gobernador de homeostasis termodinámica. control de dimensionalidad vsa basado en pid agéntico.',
    icon: '⎈',
    color: '#E52B55'
  },
  {
    id: 's0p-ledger',
    title: 's0p.ledger',
    description: 'registro inmutable de hechos soberanos. persistencia sellada en el sustrato de verdad (causal_graph).',
    icon: '⛓️',
    color: '#E5E52B'
  },
  {
    id: 's0p-temporal',
    title: 's0p.temporal',
    description: 'arqueología temporal agéntica. reconstrucción de decisiones y flujos de exergía históricos.',
    icon: '💾',
    color: '#E5D02B'
  },
  {
    id: 'memory-altar',
    title: 'memory.altar',
    description: 'altar de persistencia profunda. cristalización de insights y homeostasis termodinámica manual.',
    icon: '🕯️',
    color: '#2B3BE5',
    type: 'critical'
  }
];
