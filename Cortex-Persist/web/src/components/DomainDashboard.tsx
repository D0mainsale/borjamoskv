import React, { useState } from 'react';
import './DomainDashboard.css';

interface Domain {
  id: string;
  title: string;
  description: string;
  icon: string;
  color: string;
}

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
    description: 'Detección de exploits Zero-Day mediante herramientas SIEM (Splunk/OSCP).',
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
    title: 'Blockchain',
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
  }
];

export const DomainDashboard: React.FC = () => {
  const [activeDomain, setActiveDomain] = useState<string | null>(null);

  return (
    <div className="domain-dashboard-container">
      <header className="dashboard-header">
        <h1>SOVEREIGN DOMAINS 2026</h1>
        <p className="signal-status">CORTEX SIGNAL: <span className="status-blink">ACTIVE</span> | EXERGY: 98.4%</p>
      </header>

      <div className="domain-grid">
        {domains.map((domain) => (
          <div 
            key={domain.id} 
            className={`domain-card ${activeDomain === domain.id ? 'active' : ''}`}
            onMouseEnter={() => setActiveDomain(domain.id)}
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
              <div className="scan-line"></div>
            </div>
          </div>
        ))}
      </div>

      <footer className="dashboard-footer">
        <div className="footer-line"></div>
        <div className="footer-status">
          <span>INDUSTRIAL NOIR CORE v6.5</span>
          <span>BORJA MOSKV // CORTEX PERSIST</span>
        </div>
      </footer>
    </div>
  );
};
