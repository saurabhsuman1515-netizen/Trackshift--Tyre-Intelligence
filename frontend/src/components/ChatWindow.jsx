import React, { useState, useEffect } from 'react';
import { Send, ShieldCheck, HelpCircle } from 'lucide-react';

const ChatWindow = ({ messages = [], onSendMessage, examples = [], activeStint = 'stint_1' }) => {
  const [inputQuery, setInputQuery] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!inputQuery.trim()) return;
    onSendMessage(inputQuery);
    setInputQuery('');
  };

  const handleChipClick = (question) => {
    onSendMessage(question);
  };

  return (
    <div className="chat-container">
      <div className="chat-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <ShieldCheck size={20} color="var(--cyan-accent)" />
          <div>
            <div style={{ fontWeight: 800, fontSize: '0.95rem' }}>DETERMINISTIC RACE ENGINEER ASSISTANT</div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              Strict mathematical intent matching • Grounded directly in telemetry engine • NO LLM
            </div>
          </div>
        </div>
        <span className="badge-honest">DATA GROUNDED</span>
      </div>

      <div className="chat-messages-area">
        {messages.map((msg, idx) => (
          <div key={idx} className={`chat-msg ${msg.role}`}>
            <div style={{ fontWeight: 700, fontSize: '0.78rem', marginBottom: '0.35rem', color: msg.role === 'user' ? '#FFF' : 'var(--cyan-accent)' }}>
              {msg.role === 'user' ? 'DRIVER / STRATEGIST' : 'RACE ENGINEER'}
            </div>
            <div style={{ whiteSpace: 'pre-line' }}>{msg.text}</div>
            {msg.citation && (
              <div className="chat-citation">
                📌 Grounding: {msg.citation}
              </div>
            )}
          </div>
        ))}
      </div>

      {examples.length > 0 && (
        <div className="chat-chips-row">
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
            <HelpCircle size={14} /> SUGGESTED:
          </span>
          {examples.map((ex, i) => (
            <button key={i} className="chip-btn" onClick={() => handleChipClick(ex.question)}>
              {ex.question}
            </button>
          ))}
        </div>
      )}

      <form className="chat-input-row" onSubmit={handleSubmit}>
        <input
          type="text"
          className="chat-input"
          placeholder="Ask Race Engineer (e.g. 'When should we pit?', 'Why was lap 6 slow?')..."
          value={inputQuery}
          onChange={(e) => setInputQuery(e.target.value)}
        />
        <button type="submit" className="chat-send-btn">
          <Send size={16} />
        </button>
      </form>
    </div>
  );
};

export default ChatWindow;
