import React from 'react';
import F1CarParticleCanvas from '../components/F1CarParticleCanvas';
import KPIRow from '../components/KPIRow';

const OverviewPage = ({ overviewData = {}, activeStint = 'stint_1' }) => {
  const hero = overviewData.hero_comparison || {};
  const kpis = overviewData.kpis || {};

  return (
    <div>
      <div className="section-header">
        <div>
          <h1 className="section-title">Telemetry & Tyre Intelligence Overview</h1>
          <p className="section-subtitle">
            Isolating true tyre degradation from fuel weight, traffic penalties, and track rubbering evolution.
          </p>
        </div>
        <span className="badge-honest">HONEST UNCERTAINTY CONE</span>
      </div>

      {/* Signature UI Feature: F1 Car Particle Moving Dots Canvas */}
      <F1CarParticleCanvas compound={kpis.compound || 'SOFT'} />

      {/* Hero Comparison: RAW SLOWDOWN vs TRUE DEGRADATION */}
      <div className="hero-comparison-grid">
        <div className="comparison-card raw-slow">
          <div className="card-header-row">
            <span className="card-title">RAW UNCORRECTED SLOWDOWN</span>
            <span className="badge-sim">OBSERVED</span>
          </div>
          <div className="big-stat-val">
            +{hero.raw_slowdown_sec ? hero.raw_slowdown_sec.toFixed(3) : '0.000'}s
          </div>
          <div className="stat-desc">
            Raw telemetry delta between stint start and end. Confounded by fuel weight loss and track grip changes.
          </div>
        </div>

        <div className="comparison-card true-deg">
          <div className="card-header-row">
            <span className="card-title">TRUE ISOLATED DEGRADATION</span>
            <span className="badge-honest">ESTIMATED</span>
          </div>
          <div className="big-stat-val red">
            +{hero.true_degradation_total_sec ? hero.true_degradation_total_sec.toFixed(3) : '0.000'}s
          </div>
          <div className="stat-desc">
            True tyre degradation rate (**+{hero.true_degradation_rate_per_lap ? hero.true_degradation_rate_per_lap.toFixed(4) : '0.0600'}s/lap**). Stripped of **{hero.isolated_fuel_correction ? hero.isolated_fuel_correction.toFixed(3) : '0.000'}s** fuel mass latency.
          </div>
        </div>
      </div>

      {/* KPI Row */}
      <KPIRow kpis={kpis} compound={kpis.compound || 'SOFT'} />
    </div>
  );
};

export default OverviewPage;
