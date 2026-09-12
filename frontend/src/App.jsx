import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import ErrorBoundary from './components/ErrorBoundary';
import OverviewPage from './pages/OverviewPage';
import DegradationPage from './pages/DegradationPage';
import LapForensicsPage from './pages/LapForensicsPage';
import StrategyPage from './pages/StrategyPage';
import RaceEngineerPage from './pages/RaceEngineerPage';
import { getMetadata, getStints, getOverview, getDegradation } from './api';

function App() {
  const [activeTab, setActiveTab] = useState('overview');
  const [activeStint, setActiveStint] = useState('stint_1');
  const [meta, setMeta] = useState(null);
  const [stints, setStints] = useState([]);
  const [overviewData, setOverviewData] = useState({});
  const [degData, setDegData] = useState({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Initial fetch metadata & stints
    Promise.all([getMetadata(), getStints()])
      .then(([metaRes, stintsRes]) => {
        setMeta(metaRes);
        setStints(stintsRes.stints || []);
      })
      .catch((err) => console.error('API Load Error:', err));
  }, []);

  useEffect(() => {
    // Fetch data for active stint
    setLoading(true);
    Promise.all([getOverview(activeStint), getDegradation(activeStint)])
      .then(([ovRes, degRes]) => {
        setOverviewData(ovRes);
        setDegData(degRes);
        setLoading(false);
      })
      .catch((err) => {
        console.error(err);
        setLoading(false);
      });
  }, [activeStint]);

  const renderActivePage = () => {
    if (loading && !overviewData.hero_comparison) {
      return (
        <div style={{ padding: '4rem', textAlign: 'center', color: 'var(--text-muted)' }}>
          Loading F1 Telemetry Data...
        </div>
      );
    }

    switch (activeTab) {
      case 'overview':
        return <OverviewPage overviewData={overviewData} activeStint={activeStint} />;
      case 'degradation':
        return <DegradationPage degData={degData} activeStint={activeStint} />;
      case 'forensics':
        return <LapForensicsPage activeStint={activeStint} totalLaps={meta?.total_laps || 52} />;
      case 'strategy':
        return <StrategyPage activeStint={activeStint} />;
      case 'engineer':
        return <RaceEngineerPage activeStint={activeStint} />;
      default:
        return <OverviewPage overviewData={overviewData} activeStint={activeStint} />;
    }
  };

  return (
    <div className="app-container">
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        activeStint={activeStint}
        setActiveStint={setActiveStint}
        stints={stints}
      />
      <main className="main-content">
        <ErrorBoundary resetKey={activeTab}>{renderActivePage()}</ErrorBoundary>
      </main>
    </div>
  );
}

export default App;
