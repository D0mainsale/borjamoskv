import React, { useState, useEffect } from 'react';
import './FrontierLanding.css';
import { sonic } from '../utils/SonicService';
import { useStrategy } from '../contexts/StrategyContext';
import { MagneticWrapper } from './common/MagneticWrapper';

interface FrontierLandingProps {
  onClaim: (handle: string) => void;
}

export const FrontierLanding: React.FC<FrontierLandingProps> = ({ onClaim }) => {
  const { claimSovereignHandle, checkHandleAvailability } = useStrategy();
  const [handle, setHandle] = useState('');
  const [isSynthesizing, setIsSynthesizing] = useState(false);
  const [isAvailable, setIsAvailable] = useState<boolean | null>(null);
  const [isSuccess, setIsSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Real-time availability check
  useEffect(() => {
    if (handle.length < 3) {
      setIsAvailable(null);
      return;
    }
    const timer = setTimeout(async () => {
      const available = await checkHandleAvailability(handle);
      setIsAvailable(available);
    }, 400);
    return () => clearTimeout(timer);
  }, [handle, checkHandleAvailability]);

  const handleStart = async () => {
    if (!handle.trim() || handle.length < 3) return;
    setIsSynthesizing(true);
    setError(null);
    sonic.playClick('deploy');
    sonic.updateDrone(80, 0.8); // Warp tension
    
    try {
      const result = await claimSovereignHandle(handle);
      if (result.success) {
        setIsSuccess(true);
        sonic.playClick('success');
        // Final Synthesis Transition
        setTimeout(() => {
          onClaim(handle);
        }, 2000); 
      } else {
        setIsSynthesizing(false);
        setError(result.msg || '∴ ERROR: HANDLE_CLAIM_FAILED');
        sonic.updateDrone(30, 0.1);
      }
    } catch (err) {
      setIsSynthesizing(false);
      setError('∴ CORTEX: CRITICAL_CONNECT_FAILURE');
      sonic.updateDrone(30, 0.1);
    }
  };

  return (
    <div className={`frontier-landing ${isSynthesizing ? 'warping' : ''}`}>
      {/* ai.com fluid background */}
      <div className="frontier-visual-substrate">
        <video autoPlay loop muted playsInline className="substrate-video">
          <source src="https://ai.com/static/bg-video.mp4" type="video/mp4" />
        </video>
        <div className="film-grain"></div>
      </div>

      <div className="frontier-content">
        <header className="frontier-nav-pill">
          <MagneticWrapper>
            <div className="nav-logo">agents.archi</div>
          </MagneticWrapper>
          <div className="nav-links-minimal">
            <MagneticWrapper><span>sign up</span></MagneticWrapper>
            <MagneticWrapper><span>log in</span></MagneticWrapper>
          </div>
        </header>

        <main className="frontier-main">
          <h1 className="frontier-title-cloned">agents.archi</h1>
          <p className="frontier-subtitle">minimal architecture for sovereign agents.</p>

          <div className="handle-container-minimal">
            <div className={`handle-input-wrapper-cloned ${isAvailable === false ? 'unavailable' : ''}`}>
              <span className="handle-symbol">∴</span>
              <input 
                type="text" 
                value={handle}
                onChange={(e) => setHandle(e.target.value.toLowerCase().replace(/[^a-z0-9]/g, ''))}
                placeholder="claim handle"
                className="handle-input-cloned"
                autoFocus
                onKeyDown={(e) => e.key === 'Enter' && handleStart()}
              />
            </div>
            
            <MagneticWrapper>
              <button 
                className={`start-btn-pill ${handle.length > 2 && isAvailable !== false ? 'is-ready' : ''} ${isSuccess ? 'is-success' : ''}`} 
                onClick={handleStart}
                disabled={isSynthesizing || handle.length < 3 || isAvailable === false || isSuccess}
              >
                {isSuccess ? 'verified' : isSynthesizing ? 'claiming...' : 'start'}
              </button>
            </MagneticWrapper>

            {error && <div className="frontier-error">{error}</div>}
          </div>
        </main>

        <footer className="frontier-footer">
          <div className="legal-status">{isSuccess ? 'IDENTITY_SEALED' : 'C5-REAL_PENDING'}</div>
        </footer>
      </div>
      
      {(isSynthesizing || isSuccess) && (
        <div className="synthesis-overlay">
          <div className="warp-core"></div>
        </div>
      )}
    </div>
  );
};
