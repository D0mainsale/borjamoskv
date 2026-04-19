import React, { useState, useRef, useEffect } from 'react';

interface ArchiCommandBarProps {
  onDirective: (prompt: string) => void;
  isLoading?: boolean;
  statusMessage?: string;
}

/**
 * ArchiCommandBar — The Architect's Desk
 * Sovereign Directive Layer | ai.com minimalist v6.0
 */
import './ArchiCommandBar.css';
export const ArchiCommandBar: React.FC<ArchiCommandBarProps> = ({
  onDirective,
  isLoading = false,
  statusMessage = "awaiting directive"
}) => {
  const [prompt, setPrompt] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (prompt.trim() && !isLoading) {
      onDirective(prompt.trim());
      setPrompt(""); // Clear after submission
    }
  };

  // Focus on "/" keypress (standard CLI shortcut)
  useEffect(() => {
    const handleGlobalKeyDown = (e: KeyboardEvent) => {
      if (e.key === '/' && document.activeElement !== inputRef.current) {
        e.preventDefault();
        inputRef.current?.focus();
      }
    };
    window.addEventListener('keydown', handleGlobalKeyDown);
    return () => window.removeEventListener('keydown', handleGlobalKeyDown);
  }, []);

  return (
    <div className={`archi-command-bar ${isLoading ? 'is-loading' : ''}`}>
      <form onSubmit={handleSubmit} className="command-input-wrapper">
        <span className="archi-symbol">∴</span>
        <input
          ref={inputRef}
          type="text"
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder="enter directive"
          disabled={isLoading}
          autoComplete="off"
          spellCheck={false}
        />
      </form>

      <div className="command-status-minimal">
        {isLoading ? "∴ sintetizando fact soberano..." : statusMessage.toLowerCase()}
      </div>
    </div>
  );
};
