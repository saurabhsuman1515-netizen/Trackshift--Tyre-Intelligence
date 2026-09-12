import React from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
} from 'chart.js';
import { Bar } from 'react-chartjs-2';

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
);

const WaterfallChart = ({ waterfallData = {} }) => {
  if (!waterfallData || !waterfallData.waterfall_components) {
    return <div style={{ color: 'var(--text-muted)' }}>Select a lap to render forensics waterfall.</div>;
  }

  const comps = waterfallData.waterfall_components;

  const labels = [
    'Fuel Weight',
    'Traffic Penalty',
    'Track Evolution',
    'Tyre Wear / Warmup',
    'Outlier / Driver Noise'
  ];

  const values = [
    comps.fuel_weight_delta,
    comps.traffic_penalty_delta,
    comps.track_evolution_delta,
    comps.tyre_wear_or_warmup_delta,
    comps.outlier_residual_noise
  ];

  const backgroundColors = values.map((val) =>
    val >= 0 ? 'rgba(255, 24, 1, 0.75)' : 'rgba(0, 240, 255, 0.75)'
  );

  const borderColors = values.map((val) =>
    val >= 0 ? '#FF1801' : '#00F0FF'
  );

  const data = {
    labels,
    datasets: [
      {
        label: 'Lap Pace Delta Contribution (sec)',
        data: values,
        backgroundColor: backgroundColors,
        borderColor: borderColors,
        borderWidth: 1.5,
        borderRadius: 4
      }
    ]
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      tooltip: {
        callbacks: {
          label: (context) => `Delta: ${context.formattedValue}s`
        }
      }
    },
    scales: {
      x: {
        grid: { color: 'rgba(255, 255, 255, 0.05)' },
        ticks: { color: '#8A99AD', font: { family: 'Inter', size: 11 } }
      },
      y: {
        title: { display: true, text: 'Delta vs Baseline Pace (sec)', color: '#8A99AD' },
        grid: { color: 'rgba(255, 255, 255, 0.05)' },
        ticks: { color: '#8A99AD', font: { family: 'JetBrains Mono' } }
      }
    }
  };

  return (
    <div className="chart-container-box" style={{ height: '360px' }}>
      <div className="card-header-row">
        <div>
          <h3 className="section-title" style={{ fontSize: '1.1rem' }}>
            Lap {waterfallData.session_lap} Waterfall Pace Decomposition
          </h3>
          <p className="section-subtitle">
            Observed Raw Delta: +{waterfallData.raw_delta_sec}s • Components sum strictly to +{waterfallData.sum_of_components}s
          </p>
        </div>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          {waterfallData.is_warmup && <span className="badge-sim">WARM-UP LAP</span>}
          {waterfallData.is_outlier_downweighted && <span className="badge-honest" style={{ color: 'var(--f1-red)', borderColor: 'var(--f1-red)' }}>OUTLIER DOWNWEIGHTED</span>}
          <span className="badge-honest">ESTIMATED</span>
        </div>
      </div>
      <div style={{ height: '260px', marginTop: '1rem' }}>
        <Bar data={data} options={options} />
      </div>
    </div>
  );
};

export default WaterfallChart;
