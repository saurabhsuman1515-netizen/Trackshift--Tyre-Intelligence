import React from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js';
import { Line } from 'react-chartjs-2';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

const UncertaintyConeChart = ({ curve = [], warmupLaps = 2, compound = 'SOFT' }) => {
  const labels = curve.map((p) => `Age ${p.tyre_age}`);

  const predictedMeans = curve.map((p) => p.predicted_time);
  const upperBounds = curve.map((p) => p.upper_bound);
  const lowerBounds = curve.map((p) => p.lower_bound);

  const data = {
    labels,
    datasets: [
      {
        label: 'Upper Confidence Bound (+95%)',
        data: upperBounds,
        borderColor: 'transparent',
        backgroundColor: 'rgba(0, 240, 255, 0.12)',
        pointRadius: 0,
        fill: '+1' // Fill down to lower bound
      },
      {
        label: 'Lower Confidence Bound (-95%)',
        data: lowerBounds,
        borderColor: 'rgba(0, 240, 255, 0.3)',
        backgroundColor: 'transparent',
        borderDash: [4, 4],
        pointRadius: 0,
        fill: false
      },
      {
        label: 'Predicted Pace Curve',
        data: predictedMeans,
        borderColor: '#FF1801',
        backgroundColor: '#FF1801',
        borderWidth: 3,
        pointRadius: (ctx) => {
          const index = ctx.dataIndex;
          return index < warmupLaps ? 5 : 3;
        },
        pointBackgroundColor: (ctx) => {
          const index = ctx.dataIndex;
          return index < warmupLaps ? '#FFD700' : '#FF1801';
        }
      }
    ]
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top',
        labels: {
          color: '#8A99AD',
          font: { family: 'Inter', size: 12 }
        }
      },
      tooltip: {
        callbacks: {
          label: (context) => {
            const index = context.dataIndex;
            const pt = curve[index];
            if (pt) {
              return `Pace: ${pt.predicted_time}s (±${pt.uncertainty_margin}s) ${pt.is_warmup ? '[WARM-UP]' : ''}`;
            }
            return context.formattedValue;
          }
        }
      }
    },
    scales: {
      x: {
        grid: { color: 'rgba(255, 255, 255, 0.05)' },
        ticks: { color: '#8A99AD', font: { family: 'JetBrains Mono' } }
      },
      y: {
        title: { display: true, text: 'Tyre-Isolated Lap Time (sec)', color: '#8A99AD' },
        grid: { color: 'rgba(255, 255, 255, 0.05)' },
        ticks: { color: '#8A99AD', font: { family: 'JetBrains Mono' } }
      }
    }
  };

  return (
    <div className="chart-container-box" style={{ height: '420px' }}>
      <div className="card-header-row">
        <div>
          <h3 className="section-title" style={{ fontSize: '1.1rem' }}>
            Tyre Degradation Curve & Widening Uncertainty Cone
          </h3>
          <p className="section-subtitle">
            Yellow points indicate warm-up phase (Laps 1-{warmupLaps}). Shaded cyan band shows 95% confidence interval widening with projection horizon (proportional to √n laps ahead).
          </p>
        </div>
        <span className="badge-honest">PREDICTED</span>
      </div>
      <div style={{ height: '330px', marginTop: '1rem' }}>
        <Line data={data} options={options} />
      </div>
    </div>
  );
};

export default UncertaintyConeChart;
