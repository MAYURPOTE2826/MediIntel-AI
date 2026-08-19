import React, { useState, useEffect } from 'react';
import Timeline from './components/Timeline';
import FamilyDashboard from './components/FamilyDashboard';
import CompareReports from './components/CompareReports';
import ReportChat from './components/ReportChat';
import './App.css';

const SUPPORTED_LANGUAGES = [
  { code: 'en', name: 'English' },
  { code: 'hi', name: 'Hindi' },
  { code: 'mr', name: 'Marathi' },
  { code: 'ta', name: 'Tamil' },
  { code: 'te', name: 'Telugu' },
  { code: 'kn', name: 'Kannada' },
  { code: 'ml', name: 'Malayalam' },
  { code: 'bn', name: 'Bengali' },
  { code: 'gu', name: 'Gujarati' },
  { code: 'pa', name: 'Punjabi' }
];

function App() {
  const [currentView, setCurrentView] = useState('timeline');
  const [language, setLanguage] = useState('en');

  useEffect(() => {
    const browserLang = navigator.language.split('-')[0];
    const supported = SUPPORTED_LANGUAGES.find(l => l.code === browserLang);
    if (supported) {
      setLanguage(supported.code);
    }
  }, []);

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
        <div className="user-profile" style={{ display: 'flex', alignItems: 'center', gap: '15px' }}>
          <select 
            value={language} 
            onChange={(e) => setLanguage(e.target.value)}
            style={{ padding: '5px 10px', borderRadius: '5px', background: '#1e293b', color: 'white', border: '1px solid #334155' }}
          >
            {SUPPORTED_LANGUAGES.map(lang => (
              <option key={lang.code} value={lang.code}>{lang.name}</option>
            ))}
          </select>
          <img src="https://ui-avatars.com/api/?name=Patient+User&background=3B82F6&color=fff" alt="Profile" className="avatar" />
        </div>
      </header>
      
      <main className="app-main">
        {currentView === 'timeline' && <Timeline language={language} />}
        {currentView === 'family' && <FamilyDashboard language={language} />}
        {currentView === 'compare' && <CompareReports language={language} />}
        {currentView === 'reports' && <ReportChat language={language} />}
      </main>
    </div>
  );
}

export default App;
