import { useState } from 'react';

export const useSovereignActions = (apiHost: string) => {
  const [strikeLog, setStrikeLog] = useState<string | null>(null);
  const [isExfiltrating, setIsExfiltrating] = useState<string | null>(null);
  const [isFractalStrikeActive, setIsFractalStrikeActive] = useState(false);
  const [pidLogs, setPidLogs] = useState<string[]>([]);
  const [bounties, setBounties] = useState<any[]>([]);

  const fetchBounties = async () => {
    try {
      const res = await fetch(`${apiHost}/api/bounties`);
      const data = await res.json();
      setBounties(data.bounties || []);
    } catch (err) {
      console.warn("FAILED_TO_FETCH_BOUNTIES");
    }
  };

  const handleExfiltrate = async (reportId: string, method: 'code4rena' | 'onchain') => {
    setIsExfiltrating(reportId);
    setPidLogs(prev => [`[${new Date().toLocaleTimeString()}] INITIATING_EXFILTRATION: ${reportId}`, ...prev.slice(0, 4)]);
    
    try {
      const response = await fetch(`${apiHost}/api/exfiltrate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ report_id: reportId, method })
      });
      const data = await response.json();
      setPidLogs(prev => [`[${new Date().toLocaleTimeString()}] EXFILTRATION_${data.status}: ${data.mode}`, ...prev.slice(0, 4)]);
      fetchBounties();
    } catch (err) {
      setPidLogs(prev => [`[${new Date().toLocaleTimeString()}] EXFILTRATION_CRIT_FAIL: ${err}`, ...prev.slice(0, 4)]);
    } finally {
      setIsExfiltrating(null);
    }
  };

  const handleStrike = async (params: { domain: string; apiUrl: string; token: string }) => {
    const { domain, apiUrl, token } = params;
    if (!domain) return;

    try {
      setStrikeLog(`◈ INITIATING YOLO_STRIKE: ${domain}\n∴ Agents.archi: Dispatching Autonomous Swarm...`);
      const response = await fetch(`${apiHost}/api/strike/execute`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ target: domain, api_url: apiUrl, auth_token: token })
      });
      const data = await response.json();
      setStrikeLog(prev => prev + `\n✅ ${data.status} | Target: ${data.target}\n📊 Log: Terminal stream active.`);
    } catch (err) {
      setStrikeLog(prev => prev + `\n❌ YOLO_STRIKE_FAILED: ${err}`);
    }
  };

  const handleFractalStrike = async (setActiveAgents: (ids: number[]) => void) => {
    setIsFractalStrikeActive(true);
    setStrikeLog(`◈ INITIATING FRACTAL STRIKE [LEGION-100]\n∴ Agents.archi: Hooking into Swarm Substrate...`);

    try {
      const res = await fetch(`${apiHost}/api/strike/fractal`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mode: 'FRACTAL_V6' })
      });
      const data = await res.json();
      
      setActiveAgents(Array.from({ length: 100 }, (_, i) => i + 1));
      setStrikeLog(prev => prev + `\n🔥 ${data.msg}\n∴ STRIKE_ID: ${data.strike_id}\n` + (data.persist_hash ? `∴ SEALED_PROOF: ${data.persist_hash.slice(0, 32)}...\n` : ""));
      
      setTimeout(() => setStrikeLog(prev => prev + "◈ PHASE: SCANNING_VULNERABILITIES...\n"), 1000);
      setTimeout(() => {
        setIsFractalStrikeActive(false);
        setActiveAgents([]);
        setStrikeLog(prev => prev + `\n✅ STRIKE_COMPLETE | ID=${data.strike_id}\n∴ EXERGY_SNAPSHOT: 99.1%`);
      }, (data.duration_est || 5) * 1000);
    } catch (e) {
      setStrikeLog(prev => prev + `\n🛑 C5-REAL BINDING FAILED: API unreachable.`);
      setIsFractalStrikeActive(false);
    }
  };

  return {
    strikeLog,
    isExfiltrating,
    isFractalStrikeActive,
    pidLogs,
    bounties,
    handleExfiltrate,
    handleStrike,
    handleFractalStrike,
    fetchBounties
  };
};
