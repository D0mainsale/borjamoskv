import React from 'react';

interface StrikeConsoleProps {
  showStrikeConsole: boolean;
  setShowStrikeConsole: (show: boolean) => void;
  strikeParams: { domain: string; apiUrl: string; token: string };
  setStrikeParams: (params: any) => void;
  handleStrike: () => void;
  displayedLog: string;
  debugMode: boolean;
}

import { MagneticWrapper } from './common/MagneticWrapper';

export const StrikeConsole: React.FC<StrikeConsoleProps> = ({
  showStrikeConsole, setShowStrikeConsole, strikeParams, setStrikeParams,
  handleStrike, displayedLog, debugMode
}) => {
  if (!showStrikeConsole) return null;

  return (
    <div className={`strike-console-ether ${debugMode ? 'is-debug' : ''}`}>
      <div className="strike-header-minimal">
        <div className="strike-branding">
          <span className="strike-symbol">∴</span> strike_terminal_v1
        </div>
        <MagneticWrapper>
          <button className="strike-close-minimal" onClick={() => setShowStrikeConsole(false)}>close</button>
        </MagneticWrapper>
      </div>
      
      <div className="strike-body-ether">
        <div className="strike-input-stack">
          <div className="strike-field">
            <label>target_domain</label>
            <input
              value={strikeParams.domain}
              onChange={e => setStrikeParams({ ...strikeParams, domain: e.target.value })}
              placeholder="enter domain"
              autoComplete="off"
            />
          </div>
          <div className="strike-field">
            <label>api_endpoint (optional)</label>
            <input
              value={strikeParams.apiUrl}
              onChange={e => setStrikeParams({ ...strikeParams, apiUrl: e.target.value })}
              placeholder="https://api..."
              autoComplete="off"
            />
          </div>
          <div className="strike-field">
            <label>auth_token (if required)</label>
            <input
              type="password"
              value={strikeParams.token}
              onChange={e => setStrikeParams({ ...strikeParams, token: e.target.value })}
              placeholder="••••••••"
            />
          </div>
          
          <MagneticWrapper>
            <button className="strike-launch-pill" onClick={handleStrike}>
              replicate_strike
            </button>
          </MagneticWrapper>
        </div>

        <div className="strike-log-substrate">
          <pre>{displayedLog || 'awaiting dispatch_directives...'}</pre>
        </div>
      </div>
    </div>
  );
};
