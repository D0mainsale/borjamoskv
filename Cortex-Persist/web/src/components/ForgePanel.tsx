import React from 'react';
import './ForgePanel.css';
import { ArchiCommandBar } from './ArchiCommandBar';
import { ArchiProduct } from '../types/sovereign';

interface ForgePanelProps {
  recentProducts: ArchiProduct[];
  isArchiLoading: boolean;
  archiStatus: string;
  handleArchiDirective: (prompt: string) => void;
}

export const ForgePanel: React.FC<ForgePanelProps> = ({ 
  recentProducts, isArchiLoading, archiStatus, handleArchiDirective 
}) => {
  return (
    <>
      <ArchiCommandBar 
        onDirective={handleArchiDirective} 
        isLoading={isArchiLoading} 
        statusMessage={archiStatus}
      />

      {recentProducts.length > 0 && (
        <div className="forge-history-container">
          <h3>
            <span className="pulse-dot"></span>
            recent_synthesis
          </h3>
          <div className="forge-history-list">
            {recentProducts.map(p => (
              <div key={p.id} className="forge-history-item" onClick={() => console.log("Auditing:", p.id)}>
                <span className="fact-id">∴ {p.id.slice(0, 12)}</span>
                <span className="directive-preview">{p.directive}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </>
  );
};
