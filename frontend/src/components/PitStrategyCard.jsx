import React from 'react';
import { Flag, AlertTriangle, CheckCircle2 } from 'lucide-react';

const PitStrategyCard = ({ option = {} }) => {
  const isOptimal = option.recommendation === 'OPTIMAL';
  const isRisky = option.recommendation === 'RISKY';

  return (
    <div className={`strategy-card ${isOptimal ? 'optimal' : isRisky ? 'risky' : ''}`}>
      <div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
          <span className={`rec-pill ${isOptimal ? 'optimal' : isRisky ? 'risky' : 'balanced'}`}>
            {option.recommendation}
          </span>
          <span className="badge-honest">PREDICTED</span>
        </div>

        <h3 style={{ fontSize: '1.15rem', fontWeight: 800, marginBottom: '0.25rem' }}>
          {option.title}
        </h3>
        <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)', marginBottom: '1.25rem' }}>
          {option.action}
        </p>

        <div style={{ marginBottom: '1rem' }}>
          <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>
            Projected Time Delta
          </div>
          <div className={`big-stat-val ${isRisky ? 'red' : ''}`} style={{ fontSize: '2.2rem' }}>
            +{option.projected_time_delta_sec}s
          </div>
        </div>

        <div style={{ background: 'rgba(0, 0, 0, 0.2)', padding: '0.75rem', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.25rem' }}>
            Uncertainty Cone Range (95%)
          </div>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.88rem', color: 'var(--cyan-accent)' }}>
            +{option.lower_bound_sec}s to +{option.upper_bound_sec}s
          </div>
          <div style={{ fontSize: '0.72rem', color: 'var(--text-dim)', marginTop: '0.2rem' }}>
            Margin: ±{option.uncertainty_margin_sec}s
          </div>
        </div>
      </div>
    </div>
  );
};

export default PitStrategyCard;
