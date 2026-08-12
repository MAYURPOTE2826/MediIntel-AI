import React from 'react';
import Timeline from './components/Timeline';
import './App.css';

function App() {
  return (
    <div className="app-wrapper">
      <header className="app-header">
        <div className="logo text-gradient">MediIntel AI</div>
        <nav className="app-nav">
          <a href="#" className="nav-link">Dashboard</a>
          <a href="#" className="nav-link active">Timeline</a>
          <a href="#" className="nav-link">Reports</a>
          <a href="#" className="nav-link">Specialists</a>
        </nav>
        <div className="user-profile">
          <img src="https://ui-avatars.com/api/?name=Patient+User&background=3B82F6&color=fff" alt="Profile" className="avatar" />
        </div>
      </header>
      
      <main className="app-main">
        <Timeline />
      </main>
    </div>
  );
}

export default App;
