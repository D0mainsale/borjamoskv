import React, { useState, useEffect, useRef, KeyboardEvent } from 'react';
import './MoskvChat.css';

interface Message {
  id: string;
  sender: 'user' | 'agent' | 'system' | 'tool';
  text: string;
  timestamp: string;
  isStreaming?: boolean;
  toolName?: string;
  thinkingSteps?: string[];
  model?: string;
}

interface MoskvChatProps {
  onClose: () => void;
}

const MODELS = [
  { id: 'ollama-llama3', label: 'Llama 3 (Local)', provider: 'Ollama', latency: '~80ms' },
  { id: 'gemini-2.0-flash', label: 'Gemini 2.0 Flash', provider: 'Google', latency: '~220ms' },
  { id: 'gpt-4.1', label: 'GPT-4.1', provider: 'OpenAI', latency: '~400ms' },
  { id: 'kimi-k2.5', label: 'Kimi K2.5', provider: 'Moonshot', latency: '~350ms' },
];

export const MoskvChat: React.FC<MoskvChatProps> = ({ onClose }) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputVal, setInputVal] = useState('');
  const [isConnected, setIsConnected] = useState(false);
  const [isThinking, setIsThinking] = useState(false);
  const [activeModel, setActiveModel] = useState(MODELS[0]);
  const [showModelPicker, setShowModelPicker] = useState(false);
  const [showTools, setShowTools] = useState(false);
  const [toolLog, setToolLog] = useState<string[]>([]);
  const [ghostMode, setGhostMode] = useState(false);
  const [latencyMs, setLatencyMs] = useState<number | null>(null);
  const [tokenCount, setTokenCount] = useState(0);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [sessions, setSessions] = useState<{ id: string; title: string; active: boolean }[]>([
    { id: 'session-1', title: 'Current Session', active: true }
  ]);

  // const wsRef = useRef<WebSocket | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const sendTimestamp = useRef<number>(0);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };
  useEffect(() => { scrollToBottom(); }, [messages]);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 200) + 'px';
    }
  }, [inputVal]);

  // REST Dispatch logic
  const handleSend = async () => {
    if (!inputVal.trim() || isThinking) return;

    const userMsg: Message = {
      id: `msg-${Date.now()}`,
      sender: 'user',
      text: inputVal,
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMsg]);
    setInputVal('');
    setIsThinking(true);
    sendTimestamp.current = Date.now();

    try {
      const response = await fetch('http://127.0.0.1:8000/api/agent/dispatch', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          prompt: inputVal,
          session_id: sessions.find(s => s.active)?.id || 'default'
        })
      });

      const data = await response.json();
      const now = Date.now();
      setLatencyMs(now - sendTimestamp.current);
      setIsThinking(false);

      if (data.status === 'success') {
        setMessages(prev => [...prev, {
          id: `msg-${Date.now()}`,
          sender: 'agent',
          text: data.response,
          model: activeModel.label,
          timestamp: new Date().toISOString()
        }]);
      } else {
        throw new Error(data.error || 'Unknown dispatch error');
      }
    } catch (error: any) {
      setIsThinking(false);
      setMessages(prev => [...prev, {
        id: `err-${Date.now()}`,
        sender: 'system',
        text: `⚠ DISPATCH_FAILURE: ${error.message}`,
        timestamp: new Date().toISOString()
      }]);
    }
  };

  useEffect(() => {
    // Initial system greeting
    setMessages([{
      id: `sys-${Date.now()}`,
      sender: 'system',
      text: '∴ CORTEX_RUNTIME LOCKED | C5-REAL | Agentic Loop Ready',
      timestamp: new Date().toISOString()
    }]);
    setIsConnected(true);
  }, []);



  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const copyMessage = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  const newSession = () => {
    const id = `session-${Date.now()}`;
    setSessions(prev => [
      ...prev.map(s => ({ ...s, active: false })),
      { id, title: `Session ${prev.length + 1}`, active: true }
    ]);
    setMessages([]);
    setTokenCount(0);
    setToolLog([]);
  };

  const formatTime = (iso: string) => {
    return new Date(iso).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <div className="moskv-chat-overlay" onClick={onClose}>
      <div className="moskv-chat-container" onClick={e => e.stopPropagation()}>

        {/* SIDEBAR */}
        <div className={`chat-sidebar ${sidebarCollapsed ? 'collapsed' : ''}`}>
          <div className="sidebar-top">
            <button className="sidebar-collapse-btn" onClick={() => setSidebarCollapsed(!sidebarCollapsed)}>
              {sidebarCollapsed ? '→' : '←'}
            </button>
            {!sidebarCollapsed && (
              <>
                <div className="sidebar-brand">
                  <span className="brand-icon">Ω</span>
                  <span className="brand-text">MOSKVBOT</span>
                </div>

                <button className="new-session-btn" onClick={newSession}>
                  <span>+</span> New Thread
                </button>

                <div className="session-list">
                  {sessions.map(s => (
                    <div key={s.id} className={`session-item ${s.active ? 'active' : ''}`}>
                      <span className="session-dot" />
                      <span className="session-title">{s.title}</span>
                    </div>
                  ))}
                </div>
              </>
            )}
          </div>

          {!sidebarCollapsed && (
            <div className="sidebar-bottom">
              <div className="sidebar-status-row">
                <div className={`conn-dot ${isConnected ? 'on' : 'off'}`} />
                <span>{isConnected ? 'GATEWAY:18789' : 'OFFLINE'}</span>
              </div>
              <div className="sidebar-status-row">
                <span className="ghost-label">GHOST</span>
                <button
                  className={`ghost-toggle ${ghostMode ? 'active' : ''}`}
                  onClick={() => setGhostMode(!ghostMode)}
                >
                  <div className="ghost-thumb" />
                </button>
              </div>
            </div>
          )}
        </div>

        {/* MAIN */}
        <div className="chat-main">
          {/* HEADER */}
          <header className="chat-header">
            <div className="header-left">
              <div className="model-selector" onClick={() => setShowModelPicker(!showModelPicker)}>
                <span className="model-provider">{activeModel.provider}</span>
                <span className="model-name">{activeModel.label}</span>
                <span className="model-chevron">▾</span>
                {showModelPicker && (
                  <div className="model-dropdown">
                    {MODELS.map(m => (
                      <div
                        key={m.id}
                        className={`model-option ${m.id === activeModel.id ? 'selected' : ''}`}
                        onClick={(e) => {
                          e.stopPropagation();
                          setActiveModel(m);
                          setShowModelPicker(false);
                        }}
                      >
                        <span className="option-name">{m.label}</span>
                        <span className="option-meta">{m.provider} · {m.latency}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            <div className="header-right">
              <div className="header-metrics">
                {latencyMs !== null && (
                  <span className={`metric-pill ${latencyMs < 200 ? 'fast' : latencyMs < 500 ? 'medium' : 'slow'}`}>
                    {latencyMs}ms
                  </span>
                )}
                <span className="metric-pill neutral">{tokenCount} tok</span>
              </div>
              <button
                className={`tools-toggle ${showTools ? 'active' : ''}`}
                onClick={() => setShowTools(!showTools)}
                title="MCP Tool Inspector"
              >
                ⚙
              </button>
              <button className="close-chat-btn" onClick={onClose}>×</button>
            </div>
          </header>

          {/* BODY */}
          <div className="chat-body-wrapper">
            <div className={`chat-messages ${showTools ? 'with-tools' : ''}`}>
              {messages.length === 0 && !isConnected && (
                <div className="empty-state">
                  <div className="empty-icon">Ω</div>
                  <h2>MOSKVBOT SOVEREIGN ENGINE</h2>
                  <p>Connecting to local gateway...</p>
                </div>
              )}
              {messages.length === 0 && isConnected && (
                <div className="empty-state">
                  <div className="empty-icon">Ω</div>
                  <h2>MOSKVBOT SOVEREIGN ENGINE</h2>
                  <p>Gateway locked. Ask anything.</p>
                  <div className="quick-actions">
                    {['Think about CORTEX architecture', 'Run system diagnostics', 'Analyze current repo'].map((q, i) => (
                      <button key={i} className="quick-btn" onClick={() => {
                        setInputVal(q);
                        textareaRef.current?.focus();
                      }}>
                        {q}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {messages.map((msg) => (
                <div key={msg.id} className={`message-row ${msg.sender}`}>
                  <div className="message-avatar-col">
                    <div className={`msg-avatar ${msg.sender}`}>
                      {msg.sender === 'user' ? 'U' :
                       msg.sender === 'tool' ? '⚙' :
                       msg.sender === 'system' ? '∴' : 'Ω'}
                    </div>
                  </div>
                  <div className="message-body">
                    <div className="msg-meta">
                      <span className="msg-sender-name">
                        {msg.sender === 'user' ? 'You' :
                         msg.sender === 'tool' ? msg.toolName || 'Tool' :
                         msg.sender === 'system' ? 'System' : 'MoskvBot'}
                      </span>
                      {msg.model && <span className="msg-model-tag">{msg.model}</span>}
                      <span className="msg-time">{formatTime(msg.timestamp)}</span>
                    </div>
                    <div className="msg-content">
                      {msg.text.split('\n').map((line, i) => (
                        <p key={i}>{line || '\u00A0'}</p>
                      ))}
                    </div>
                    {msg.sender !== 'system' && (
                      <div className="msg-actions">
                        <button className="action-btn" onClick={() => copyMessage(msg.text)} title="Copy">⧉</button>
                        {msg.sender === 'agent' && (
                          <button className="action-btn" onClick={() => {
                            setInputVal(messages.find(m => m.sender === 'user' && new Date(m.timestamp) < new Date(msg.timestamp))?.text || '');
                          }} title="Retry">↻</button>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              ))}

              {isThinking && (
                <div className="message-row agent">
                  <div className="message-avatar-col">
                    <div className="msg-avatar agent thinking-pulse">Ω</div>
                  </div>
                  <div className="message-body">
                    <div className="msg-meta">
                      <span className="msg-sender-name">MoskvBot</span>
                      <span className="msg-model-tag">{activeModel.label}</span>
                    </div>
                    <div className="thinking-indicator">
                      <div className="thinking-dots">
                        <span /><span /><span />
                      </div>
                      <span className="thinking-label">Reasoning...</span>
                    </div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* TOOL INSPECTOR PANEL */}
            {showTools && (
              <div className="tool-inspector">
                <div className="tool-inspector-header">
                  <span>MCP TOOL INSPECTOR</span>
                  <span className="tool-count">{toolLog.length}</span>
                </div>
                <div className="tool-log-list">
                  {toolLog.length === 0 && (
                    <div className="tool-empty">No tool executions yet</div>
                  )}
                  {toolLog.map((entry, i) => (
                    <div key={i} className="tool-log-entry">{entry}</div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* INPUT */}
          <div className="chat-input-area">
            <div className="input-container">
              <textarea
                ref={textareaRef}
                value={inputVal}
                onChange={e => setInputVal(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Message MoskvBot..."
                rows={1}
              />
              <div className="input-actions">
                <button
                  className={`send-btn ${inputVal.trim() ? 'ready' : ''}`}
                  onClick={handleSend}
                  disabled={!inputVal.trim()}
                >
                  <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                    <path d="M8 14V2M8 2L3 7M8 2L13 7" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                  </svg>
                </button>
              </div>
            </div>
            <div className="input-meta">
              <span>MoskvBot 3.3 · {activeModel.provider} · {ghostMode ? 'Ghost Mode' : 'Logged'} · ⌘↵ Send</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
