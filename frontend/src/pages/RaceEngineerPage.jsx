import React, { useState, useEffect } from 'react';
import ChatWindow from '../components/ChatWindow';
import { askRaceEngineer, getAskExamples } from '../api';

const RaceEngineerPage = ({ activeStint = 'stint_1' }) => {
  const [messages, setMessages] = useState([
    {
      role: 'engineer',
      text: "Race Engineer standing by. All queries are resolved deterministically against computed session analytics (no LLM generation). How can I assist with tyre strategy or lap pace forensics?",
      citation: "Telemetry engine initialized & calibrated."
    }
  ]);
  const [examples, setExamples] = useState([]);

  useEffect(() => {
    getAskExamples()
      .then((data) => setExamples(data.examples || []))
      .catch((err) => console.error(err));
  }, []);

  const handleSendMessage = (queryText) => {
    // Add user message
    const userMsg = { role: 'user', text: queryText };
    setMessages((prev) => [...prev, userMsg]);

    // Send query to backend
    askRaceEngineer(queryText, activeStint)
      .then((resp) => {
        const engMsg = {
          role: 'engineer',
          text: resp.answer,
          citation: resp.grounding_citation
        };
        setMessages((prev) => [...prev, engMsg]);
      })
      .catch((err) => {
        console.error(err);
        setMessages((prev) => [
          ...prev,
          {
            role: 'engineer',
            text: "Connection error reaching telemetry assistant.",
            citation: "Network error."
          }
        ]);
      });
  };

  return (
    <div>
      <div className="section-header">
        <div>
          <h1 className="section-title">Telemetry Race Engineer</h1>
          <p className="section-subtitle">
            Deterministic Q&A engine grounded directly in computed session analytics.
          </p>
        </div>
        <span className="badge-honest">ZERO HALLUCINATION</span>
      </div>

      <ChatWindow
        messages={messages}
        onSendMessage={handleSendMessage}
        examples={examples}
        activeStint={activeStint}
      />
    </div>
  );
};

export default RaceEngineerPage;
