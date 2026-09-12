import React, { useState, useEffect } from 'react';
import WaterfallChart from '../components/WaterfallChart';
import { getLapForensics } from '../api';

const LapForensicsPage = ({ activeStint = 'stint_1', totalLaps = 52 }) => {
  const [selectedLap, setSelectedLap] = useState(6);
  const [waterfall, setWaterfall] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    setLoading(true);
    getLapForensics(selectedLap)
      .then((data) => {
        setWaterfall(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error(err);
        setLoading(false);
      });
  }, [selectedLap]);

  return (
    <div>
      <div className="section-header">
        <div>
          <h1 className="section-title">Single-Lap Pace Forensics</h1>
          <p className="section-subtitle">
            Additive waterfall breakdown showing fuel vs traffic vs track evolution vs tyre wear vs outlier noise.
          </p>
        </div>
        <span className="badge-honest">EXACT SUM RECONCILIATION</span>
      </div>

      {/* Lap Picker Bar */}
      <div className="chart-container-box" style={{ marginBottom: '1.5rem', padding: '1rem 1.5rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '1rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <span style={{ fontWeight: 700, fontSize: '0.9rem', color: 'var(--text-muted)' }}>SELECT LAP NUMBER:</span>
            <input
              type="range"
              min={1}
              max={totalLaps}
              value={selectedLap}
              onChange={(e) => setSelectedLap(Number(e.target.value))}
              style={{ width: '240px', accentColor: 'var(--f1-red)', cursor: 'pointer' }}
            />
            <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 800, fontSize: '1.2rem', color: '#FFF' }}>
              LAP {selectedLap}
            </span>
          </div>

          <div style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap' }}>
            {[2, 6, 12, 18, 27, 35, 42].map((num) => (
              <button
                key={num}
                className={`stint-btn ${selectedLap === num ? 'active' : ''}`}
                onClick={() => setSelectedLap(num)}
              >
                Lap {num}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Waterfall Chart */}
      {loading ? (
        <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-muted)' }}>Calculating Lap Forensics...</div>
      ) : (
        <WaterfallChart waterfallData={waterfall} />
      )}
    </div>
  );
};

export default LapForensicsPage;
