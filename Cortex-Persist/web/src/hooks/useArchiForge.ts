import { useState, useEffect, useCallback } from 'react';

export interface ArchiProduct {
  id: string;
  directive: string;
  timestamp: string;
  status?: string;
}

export const useArchiForge = (apiHost: string) => {
  const [isArchiLoading, setIsArchiLoading] = useState(false);
  const [archiStatus, setArchiStatus] = useState("Awaiting Directive...");
  const [recentProducts, setRecentProducts] = useState<ArchiProduct[]>([]);

  const fetchHistory = useCallback(async () => {
    try {
      const res = await fetch(`${apiHost}/v1/archi/history`, {
        headers: { 'X-Agent-ID': 'borjamoskv-omega' }
      });
      if (res.ok) {
        const history = await res.json();
        setRecentProducts(history.map((item: any) => ({
          id: item.id,
          directive: item.directive,
          timestamp: new Date(item.timestamp * 1000).toISOString()
        })));
      }
    } catch (err) {
      console.error("Failed to fetch Archi history:", err);
    }
  }, [apiHost]);

  useEffect(() => {
    fetchHistory();
  }, [fetchHistory]);

  const handleArchiDirective = async (prompt: string, addNotification: (msg: string, type?: 'success' | 'error') => void) => {
    setIsArchiLoading(true);
    setArchiStatus("Architecting...");
    
    try {
      const response = await fetch(`${apiHost}/v1/archi/directive`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('cortex_token')}`
        },
        body: JSON.stringify({ prompt })
      });
      
      if (!response.ok) throw new Error("Archi forge saturation detected");
      
      const result = await response.json();
      setArchiStatus(`Product Synced: ${result.fact_id.slice(0, 8)}`);
      
      const newProduct: ArchiProduct = {
        id: result.fact_id,
        directive: prompt,
        timestamp: new Date().toISOString()
      };

      setRecentProducts(prev => [newProduct, ...prev].slice(0, 10));
      addNotification(`Product Synthesized: ${result.fact_id.slice(0, 8)}`);
      return result;
    } catch (err: any) {
      setArchiStatus(`Forge Error: ${err.message}`);
      addNotification(`Forge Saturation: ${err.message}`, 'error');
      throw err;
    } finally {
      setIsArchiLoading(false);
    }
  };

  return {
    isArchiLoading,
    archiStatus,
    recentProducts,
    handleArchiDirective,
    refreshHistory: fetchHistory
  };
};
