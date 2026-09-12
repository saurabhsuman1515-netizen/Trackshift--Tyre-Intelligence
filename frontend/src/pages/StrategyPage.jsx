import React, { useState, useEffect } from 'react';
import PitStrategyCard from '../components/PitStrategyCard';
import { simulateStrategy } from '../api';

const StrategyPage = ({ activeStint = 'stint_1' }) => {
  const [pitInNLaps, setPitInNLaps] = useState(5);
  const [strategyData, setStrategyData] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    setLoading(true);
    simulateStrategy(activeStint, pitInNLaps)
      .then((data) => {
        setStrategyData(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error(err);
        setLoading(false);
      });
  }, [activeStint, pitInNLaps]);

  const options = strategyData?.options || [];

  return (
    <div>
      <div className="section-header">
        <div>
          <h1 className="section-title">Pit Stop Strategy Simulator</h1>
          <p className="section-subtitle">
            Simulate stay-out vs pit-now vs pit-in-N using the uncertainty-aware degradation curve.
          </p>
        </div>
        <span className="badge-honest">UNCERTAINTY AWARE</span>
      </div>

      {/* Simulator Controls Bar */}
      <div className="chart-container-box" style={{ marginBottom: '1.5rem', padding: '1.25rem 1.5rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem' }}>
          <span style={{ fontWeight: 700, fontSize: '0.9rem', color: 'var(--text-muted)' }}>
            SIMULATE DELAYED PIT STOP (N LAPS):
          </span>
          <input
            type="range"
            min={1}
            max={15}
            value={pitInNLaps}
            onChange={(e) => setPitInNLaps(Number(e.target.value))}
            style={{ width: '220px', accentColor: 'var(--f1-red)', cursor: 'pointer' }}
          />
          <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 800, fontSize: '1.2rem', color: 'var(--cyan-accent)' }}>
            +{pitInNLaps} LAPS
          </span>
        </div>
      </div>

      {/* Strategy Grid Cards */}
      {loading ? (
        <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-muted)' }}>Simulating Strategy Outcomes...</div>
      ) : (
        <div className="strategy-grid">
          {options.map((opt) => (
            <PitStrategyCard key={opt.id} option={opt} />
          ))}
        </div>
      )}
    </div>
  );
};

export default StrategyPage;
