import React from 'react';
import { Info } from 'lucide-react';

const KPIRow = ({ kpis = {}, compound = 'SOFT' }) => {
  const compoundColors = {
    SOFT: 'var(--f1-red)',
    MEDIUM: 'var(--yellow-accent)',
    HARD: '#FFF'
  };

  return (
    <div className="kpi-row">
      <div className="kpi-card">
        <div className="kpi-label">Active Compound</div>
        <div className="kpi-value" style={{ color: compoundColors[compound] || '#FFF' }}>
          {compound}
        </div>
        <div className="kpi-sub">Pirelli Baseline Specs</div>
      </div>

      <div className="kpi-card">
        <div className="kpi-label">Degradation Rate</div>
        <div className="kpi-value">
          +{kpis.degradation_rate_sec ? kpis.degradation_rate_sec.toFixed(4) : '0.0600'}s
        </div>
        <div className="kpi-sub">
          <span className="badge-honest">ESTIMATED</span> per lap
        </div>
      </div>

      <div className="kpi-card">
        <div className="kpi-label">Uncertainty Band</div>
        <div className="kpi-value" style={{ color: 'var(--cyan-accent)' }}>
          ±{kpis.uncertainty_band_margin ? kpis.uncertainty_band_margin.toFixed(3) : '0.150'}s
        </div>
        <div className="kpi-sub">
          <span className="badge-honest">PREDICTED</span> 95% interval
        </div>
      </div>

      <div className="kpi-card">
        <div className="kpi-label">Remaining Life</div>
        <div className="kpi-value" style={{ color: 'var(--green-accent)' }}>
          ~{kpis.remaining_life_laps ?? 12} Laps
        </div>
        <div className="kpi-sub">Before +1.50s slowdown</div>
      </div>

      <div className="kpi-card">
        <div className="kpi-label">Recommended Pit Window</div>
        <div className="kpi-value" style={{ fontSize: '1.2rem' }}>
          {kpis.recommended_pit_window || 'Lap 14 - 18'}
        </div>
        <div className="kpi-sub">
          <span className="badge-honest">PREDICTED</span> optimal box
        </div>
      </div>
    </div>
  );
};

export default KPIRow;
