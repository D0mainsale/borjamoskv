import React from 'react';
import { DomainDashboard } from './components/DomainDashboard';
import { StatusBar } from './components/StatusBar';
import { SemanticMemoryPanel } from './components/SemanticMemoryPanel';
import './App.css';

export const App: React.FC = () => {

  return (
    <div className="app-shell">
      <StatusBar />
      <div className="app-content">
        <main className="app-main">
          <DomainDashboard />
        </main>
        <aside className="app-sidebar">
          <SemanticMemoryPanel />
        </aside>
      </div>
    </div>
  );
};
