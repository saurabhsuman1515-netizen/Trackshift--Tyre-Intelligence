import React from 'react';
import UncertaintyConeChart from '../components/UncertaintyConeChart';

const DegradationPage = ({ degData = {}, activeStint = 'stint_1' }) => {
  const curve = degData.uncertainty_curve || [];
  const fit = degData.fit || {};
  const compTable = degData.comparison_table || [];

  return (
    <div>
      <div className="section-header">
        <div>
          <h1 className="section-title">Tyre Degradation Analysis & Confidence Cone</h1>
          <p className="section-subtitle">
            Two-phase warm-up changepoint fit with asymmetric outlier downweighting and expanding uncertainty.
          </p>
        </div>
        <span className="badge-honest">TWO-PHASE MODEL</span>
      </div>

      <UncertaintyConeChart
        curve={curve}
        warmupLaps={fit.detected_warmup_laps || 2}
        compound={fit.compound || 'SOFT'}
      />

      <div className="f1-table-box" style={{ marginTop: '2rem' }}>
        <div style={{ padding: '1.25rem 1.5rem', borderBottom: '1px solid var(--border-color)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h3 style={{ fontSize: '1.1rem', fontWeight: 800 }}>Cross-Compound Degradation Benchmarking</h3>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              Comparative wear rate, warm-up duration, and residual standard error (σ).
            </p>
          </div>
          <span className="badge-honest">ESTIMATED</span>
        </div>

        <table className="f1-table">
          <thead>
            <tr>
              <th>Stint</th>
              <th>Compound</th>
              <th>Warm-up Laps</th>
              <th>Degradation Rate (s/lap)</th>
              <th>Residual Error (σ)</th>
              <th>Remaining Life</th>
              <th>Recommended Pit Lap</th>
            </tr>
          </thead>
          <tbody>
            {compTable.map((row) => (
              <tr key={row.stint_id} style={{ background: row.stint_id === activeStint ? 'rgba(255, 24, 1, 0.08)' : 'transparent' }}>
                <td>{row.stint_id.toUpperCase()}</td>
                <td style={{ fontWeight: 700, color: row.compound === 'SOFT' ? 'var(--f1-red)' : row.compound === 'MEDIUM' ? 'var(--yellow-accent)' : '#FFF' }}>
                  {row.compound}
                </td>
                <td>{row.detected_warmup_laps} Laps</td>
                <td style={{ color: 'var(--f1-red)', fontWeight: 700 }}>
                  +{row.degradation_rate_sec_per_lap.toFixed(4)}s
                </td>
                <td>±{row.residual_std_error.toFixed(4)}s</td>
                <td>{row.remaining_laps} Laps</td>
                <td style={{ color: 'var(--cyan-accent)', fontWeight: 700 }}>Lap {row.recommended_pit_lap}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default DegradationPage;
