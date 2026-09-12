import React from 'react';
import { Activity, TrendingDown, Crosshair, Cpu, ShieldCheck } from 'lucide-react';

const Navbar = ({ activeTab, setActiveTab, activeStint, setActiveStint, stints = [] }) => {
  const tabs = [
    { id: 'overview', label: 'Overview', icon: Activity },
    { id: 'degradation', label: 'Degradation', icon: TrendingDown },
    { id: 'forensics', label: 'Lap Forensics', icon: Crosshair },
    { id: 'strategy', label: 'Strategy Simulator', icon: Cpu },
    { id: 'engineer', label: 'Race Engineer', icon: ShieldCheck }
  ];

  return (
    <nav className="navbar">
      <div className="nav-brand">
        <span className="brand-logo-badge">F1</span>
        <span className="brand-title">TRACKSHIFT</span>
        <span className="badge-sim">SIMULATION MODE</span>
      </div>

      <div className="nav-tabs">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          return (
            <button
              key={tab.id}
              className={`nav-tab-btn ${activeTab === tab.id ? 'active' : ''}`}
              onClick={() => setActiveTab(tab.id)}
            >
              <Icon size={16} />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>

      <div className="stint-selector">
        <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 700 }}>STINT:</span>
        {stints.map((stint) => (
          <button
            key={stint.stint_id}
            className={`stint-btn ${activeStint === stint.stint_id ? 'active' : ''}`}
            onClick={() => setActiveStint(stint.stint_id)}
          >
            {stint.compound}
          </button>
        ))}
      </div>
    </nav>
  );
};

export default Navbar;
