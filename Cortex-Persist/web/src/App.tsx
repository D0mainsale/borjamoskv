import React from 'react';
import { DomainDashboard } from './components/DomainDashboard';
import { StatusBar } from './components/StatusBar';
import { SemanticMemoryPanel } from './components/SemanticMemoryPanel';
import { StrikeTerminal } from './components/StrikeTerminal';
import { VSAMonitor } from './components/VSAMonitor';
import { HomeostasisMonitor } from './components/HomeostasisMonitor';
import { InteractiveSubstrate } from './components/InteractiveSubstrate';
import { StrategyProvider } from './contexts/StrategyContext';
import { FrontierLanding } from './components/FrontierLanding';
import './App.css';

export const App: React.FC = () => {
  const [isAbueloMode, setIsAbueloMode] = React.useState(false);
  const [isFrontierMode, setIsFrontierMode] = React.useState(true);
  const [sovereignHandle, setSovereignHandle] = React.useState<string | null>(null);
  const [activeStrike, setActiveStrike] = React.useState<{target: string, factId: number} | null>(null);

  const handleClaim = (handle: string) => {
    setSovereignHandle(handle);
    setIsFrontierMode(false);
  };

  return (
    <StrategyProvider>
      <div className={`app-shell ${isAbueloMode ? 'abuelo-mode' : ''} ${isFrontierMode ? 'frontier-active' : ''}`}>
        <InteractiveSubstrate isFrontierMode={isFrontierMode} />
        
        {isFrontierMode && <FrontierLanding onClaim={handleClaim} />}
        
        {!isFrontierMode && (
          <>
            <StatusBar 
              isAbueloMode={isAbueloMode} 
              onToggleAbuelo={() => setIsAbueloMode(!isAbueloMode)} 
            />
            {/* Main content layer */}
            <div className="app-content-minimal">
              <main className="app-main">
                <DomainDashboard 
                  isAbueloMode={isAbueloMode} 
                  sovereignHandle={sovereignHandle}
                  onInitiateStrike={(target, factId) => setActiveStrike({target, factId})}
                />
              </main>
              
              <aside className="app-sidebar-right">
                <HomeostasisMonitor />
                {activeStrike && (
                  <StrikeTerminal 
                    target={activeStrike.target} 
                    factId={activeStrike.factId} 
                    onClose={() => setActiveStrike(null)} 
                  />
                )}
                <VSAMonitor />
              </aside>
              <aside className="app-sidebar-left">
                <SemanticMemoryPanel />
              </aside>
            </div>
          </>
        )}
      </div>
    </StrategyProvider>
  );
};

export default App;
