import { useState, useEffect } from 'react';
import { PersistMode, GovernorMetrics } from '../types/sovereign';

export interface HechoSoberano {
  id: number;
  id_sesion: string;
  dominio: string;
  contenido: string;
  exergia: number;
  entropia: number;
  cristalizado: number;
  timestamp: string;
}

export const useSovereignTelemetry = (apiHost: string) => {
  const [persistMode, setPersistMode] = useState<PersistMode>('DESCONECTADO');
  const [sealedFacts, setSealedFacts] = useState(0);
  const [factCount, setFactCount] = useState(0);
  const [yieldData, setYieldData] = useState<any>(null);
  const [governorMetrics, setGovernorMetrics] = useState<GovernorMetrics | null>(null);
  const [internalAuditFeed, setInternalAuditFeed] = useState<string[]>([]);
  const [hechosSoberanos, setHechosSoberanos] = useState<HechoSoberano[]>([]);
  const [legion, setLegion] = useState<any[]>([]); // Elites
  const [swarmStats, setSwarmStats] = useState<any>(null); // Global stats
  const [vsaMetrics, setVsaMetrics] = useState<any>({ tensor_id: '0x0000', fact_count: 0, ratio: '1:1' });

  useEffect(() => {
    let socket: WebSocket | null = null;
    let reconnectTimeout: any = null;

    const connect = () => {
      const wsHost = apiHost.replace('http', 'ws');
      socket = new WebSocket(`${wsHost}/v1/telemetry/ws`);

      socket.onopen = () => {
        setPersistMode('CONSOLIDADO');
        console.log("C5-REAL: Substrato de telemetría vinculado.");
      };

      socket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === 'HEARTBEAT') {
            setSealedFacts(data.sealed_facts);
            setFactCount(data.total_facts);
            if (data.metrics) {
              setGovernorMetrics(data.metrics);
              if (data.metrics.legion) {
                // Support both old array and new hierarchical object
                if (Array.isArray(data.metrics.legion)) {
                  setLegion(data.metrics.legion);
                } else {
                  setLegion(data.metrics.legion.elites || []);
                  setSwarmStats(data.metrics.legion.stats || null);
                }
              }
            }
            if (data.vsa) setVsaMetrics(data.vsa);
          }
          if (data.type === 'AUDIT_LOG') {
            setInternalAuditFeed(prev => [data.message, ...prev].slice(0, 10));
          }
          if (data.type === 'YIELD_UPDATE') {
            setYieldData(data.data);
          }
        } catch (err) {
          console.warn("C5_FALLO_PARSE_WS:", err);
        }
      };

      socket.onclose = () => {
        setPersistMode('DESCONECTADO');
        reconnectTimeout = setTimeout(connect, 3000);
      };

      socket.onerror = () => {
        socket?.close();
      };
    };

    connect();

    return () => {
      if (socket) socket.close();
      if (reconnectTimeout) clearTimeout(reconnectTimeout);
    };
  }, [apiHost]);

  // Ω-PERSIST: Puente de Sondeo de Hechos
  useEffect(() => {
    const fetchFacts = async () => {
      try {
        const response = await fetch(`${apiHost}/api/facts`);
        const data = await response.json();
        if (data.status === 'SUCCESS') {
          setHechosSoberanos(data.facts);
        }
      } catch (err) {
        console.warn("C5_FALLO_SONDEO_HECHOS:", err);
      }
    };

    fetchFacts();
    const interval = setInterval(fetchFacts, 5000);
    return () => clearInterval(interval);
  }, [apiHost]);

  return {
    persistMode,
    sealedFacts,
    factCount,
    yieldData,
    governorMetrics,
    internalAuditFeed,
    hechosSoberanos,
    legion,
    swarmStats,
    vsaMetrics
  };
};
