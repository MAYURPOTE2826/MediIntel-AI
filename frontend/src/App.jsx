import React, { useState } from 'react';
import Timeline from './components/Timeline';
import FamilyDashboard from './components/FamilyDashboard';
import CompareReports from './components/CompareReports';
import ReportChat from './components/ReportChat';
import './App.css';

function App() {
  const [currentView, setCurrentView] = useState('timeline');

  return (
    <div className="app-wrapper">
      <header className="app-header">
        <div className="logo text-gradient">MediIntel AI</div>
        <nav className="app-nav">
          <a href="#" className="nav-link">Dashboard</a>
          <a href="#" className={`nav-link ${currentView === 'timeline' ? 'active' : ''}`} onClick={(e) => { e.preventDefault(); setCurrentView('timeline'); }}>Timeline</a>
          <a href="#" className={`nav-link ${currentView === 'compare' ? 'active' : ''}`} onClick={(e) => { e.preventDefault(); setCurrentView('compare'); }}>Compare</a>
          <a href="#" className={`nav-link ${currentView === 'family' ? 'active' : ''}`} onClick={(e) => { e.preventDefault(); setCurrentView('family'); }}>Family Sharing</a>
          <a href="#" className={`nav-link ${currentView === 'reports' ? 'active' : ''}`} onClick={(e) => { e.preventDefault(); setCurrentView('reports'); }}>Reports</a>
        </nav>
        <div className="user-profile">
          <img src="https://ui-avatars.com/api/?name=Patient+User&background=3B82F6&color=fff" alt="Profile" className="avatar" />
        </div>
      </header>
      
      <main className="app-main">
        {currentView === 'timeline' && <Timeline />}
        {currentView === 'family' && <FamilyDashboard />}
        {currentView === 'compare' && <CompareReports />}
        {currentView === 'reports' && <ReportChat />}
      </main>
    </div>
  );
}

export default App;
