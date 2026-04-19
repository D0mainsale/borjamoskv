import { useStrategy } from '../contexts/StrategyContext';

export const StatusBar: React.FC<{ isAbueloMode: boolean; onToggleAbuelo: () => void }> = ({ isAbueloMode, onToggleAbuelo }) => {
  const { exergyLevel, measuredEntropy, vsaMetrics, sealedFacts } = useStrategy();
  const [clock, setClock] = useState(new Date().toLocaleTimeString('en-GB'));

  useEffect(() => {
    const clockInterval = setInterval(() => setClock(new Date().toLocaleTimeString('en-GB')), 1000);
    return () => clearInterval(clockInterval);
  }, []);

  return (
    <div className="status-bar-minimal">
      <div className="status-item">
        <span className="label">exergy</span>
        <span className="value">{exergyLevel.toFixed(1)}%</span>
      </div>
      <div className="status-item">
        <span className="label">entropy</span>
        <span className="value">{measuredEntropy.toFixed(2)}</span>
      </div>
      <div className="status-item">
        <span className="label">vsa_ratio</span>
        <span className="value">{vsaMetrics.ratio}</span>
      </div>
      <div className="status-item hide-mobile">
        <span className="label">sealed_facts</span>
        <span className="value">∴ {sealedFacts}</span>
      </div>

      <div className="status-bar-right">
        <button 
          className={`abuelo-toggle-btn ${isAbueloMode ? 'active' : ''}`}
          onClick={onToggleAbuelo}
        >
          {isAbueloMode ? 'mode: h' : 'mode: a'}
        </button>
        <span className="signal-text">c5:real</span>
        <span className="status-clock">{clock.toLowerCase()}</span>
      </div>
    </div>
  );
};
