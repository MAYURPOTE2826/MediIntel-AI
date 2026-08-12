import React, { useState, useEffect } from 'react';
import { Users, Mail, ShieldAlert, FileText, CheckCircle, Clock, Shield, Download, Lock } from 'lucide-react';
import './FamilyDashboard.css';

const FamilyDashboard = () => {
  const [familyData, setFamilyData] = useState([]);
  const [loading, setLoading] = useState(true);
  
  // Invite form state
  const [inviteEmail, setInviteEmail] = useState('');
  const [shareMode, setShareMode] = useState('FULL');
  const [isEmergencyContact, setIsEmergencyContact] = useState(false);
  const [inviteStatus, setInviteStatus] = useState(null);

  useEffect(() => {
    fetchFamilyData();
  }, []);

  const fetchFamilyData = async () => {
    setLoading(true);
    try {
      // Mock data representing the Family Member fetching endpoint
      setTimeout(() => {
        setFamilyData([
          {
            member_id: 'user_123',
            name: 'Spouse (Jane Doe)',
            share_mode: 'FULL',
            recent_reports: [
              { date: '2026-08-01T10:00:00Z', type: 'Blood Test', findings: 'Normal lipid panel. Glucose levels optimal.' },
              { date: '2026-05-15T14:30:00Z', type: 'Chest X-Ray', findings: 'Clear lung fields. No abnormalities.' }
            ]
          },
          {
            member_id: 'user_456',
            name: 'Family Member',
            share_mode: 'ANONYMOUS',
            recent_reports: [
              { date: '2026-07-20T09:15:00Z', type: 'ECG', findings: 'Stable/Improving indicator' }
            ]
          }
        ]);
        setLoading(false);
      }, 800);
    } catch (error) {
      console.error("Failed to fetch family data", error);
      setLoading(false);
    }
  };

  const handleInvite = (e) => {
    e.preventDefault();
    if (!inviteEmail) return;
    
    // Simulate API call to /api/family/invite
    setInviteStatus({ type: 'loading', message: 'Sending invite...' });
    
    setTimeout(() => {
      setInviteStatus({ type: 'success', message: `Invite sent to ${inviteEmail}!` });
      setInviteEmail('');
      setIsEmergencyContact(false);
      setShareMode('FULL');
      
      setTimeout(() => setInviteStatus(null), 3000);
    }, 1000);
  };

  const triggerEmergencyAccess = (memberId) => {
    // Simulate API call to /api/family/emergency
    alert(`Emergency access triggered for member ${memberId}. This action has been securely logged.`);
  };

  const handleExportPdf = () => {
    // Simulate API call to /api/family/export
    alert('Generating PDF... (In a real app, this downloads the PDF file)');
  };

  return (
    <div className="family-container">
      <div className="family-header">
        <h1 className="family-title text-gradient">Family Health Dashboard</h1>
        <p style={{ color: 'var(--text-secondary)' }}>
          Securely share and monitor health records with your loved ones.
        </p>
      </div>
      
      <div className="family-grid">
        {/* Left Column: Invite Form & Actions */}
        <div className="family-sidebar">
          <div className="family-card invite-card">
            <h3><Users size={20} /> Invite Family Member</h3>
            <p className="card-subtitle">Grant access to your health timeline.</p>
            
            <form onSubmit={handleInvite} className="invite-form">
              <div className="form-group">
                <label>Email Address</label>
                <div className="input-with-icon">
                  <Mail size={16} />
                  <input 
                    type="email" 
                    value={inviteEmail}
                    onChange={(e) => setInviteEmail(e.target.value)}
                    placeholder="spouse@example.com"
                    required
                  />
                </div>
              </div>
              
              <div className="form-group">
                <label>Sharing Mode</label>
                <select value={shareMode} onChange={(e) => setShareMode(e.target.value)}>
                  <option value="FULL">Full Access (Names & Details)</option>
                  <option value="ANONYMOUS">Anonymous (Trends Only)</option>
                </select>
                <p className="help-text">
                  {shareMode === 'ANONYMOUS' 
                    ? "Names and specific details will be hidden."
                    : "They will see your full reports and name."}
                </p>
              </div>
              
              <div className="checkbox-group">
                <input 
                  type="checkbox" 
                  id="emergency-contact"
                  checked={isEmergencyContact}
                  onChange={(e) => setIsEmergencyContact(e.target.checked)}
                />
                <label htmlFor="emergency-contact">
                  <ShieldAlert size={16} color="var(--accent-danger)" />
                  Make Emergency Contact
                </label>
              </div>
              
              <button type="submit" className="btn-primary">
                Send Invitation
              </button>
              
              {inviteStatus && (
                <div className={`status-message ${inviteStatus.type}`}>
                  {inviteStatus.message}
                </div>
              )}
            </form>
          </div>
          
          <div className="family-card action-card">
            <h3><FileText size={20} /> Export Records</h3>
            <p className="card-subtitle">Download a comprehensive PDF of all shared family records.</p>
            <button onClick={handleExportPdf} className="btn-secondary">
              <Download size={16} /> Download PDF
            </button>
          </div>
        </div>

        {/* Right Column: Family Members List */}
        <div className="family-main">
          <h2><Shield size={24} color="var(--accent-primary)" /> Shared With You</h2>
          
          {loading ? (
            <div className="loading-spinner">
              <div className="spinner"></div>
            </div>
          ) : familyData.length === 0 ? (
            <div className="empty-state">
              <Users size={48} style={{ marginBottom: '1rem', opacity: 0.5 }} />
              <h3>No family records yet</h3>
              <p>Invite family members to start sharing health data.</p>
            </div>
          ) : (
            <div className="members-list">
              {familyData.map((member, idx) => (
                <div key={idx} className="member-card">
                  <div className="member-header">
                    <div className="member-info">
                      <div className="member-avatar">
                        {member.share_mode === 'ANONYMOUS' ? <Lock size={20} /> : <Users size={20} />}
                      </div>
                      <div>
                        <h4>{member.name}</h4>
                        <span className={`share-badge ${member.share_mode.toLowerCase()}`}>
                          {member.share_mode}
                        </span>
                      </div>
                    </div>
                    
                    <button 
                      onClick={() => triggerEmergencyAccess(member.member_id)}
                      className="btn-emergency"
                      title="Request emergency access to full records"
                    >
                      <ShieldAlert size={16} /> Emergency Access
                    </button>
                  </div>
                  
                  <div className="member-reports">
                    <h5>Recent Activity</h5>
                    {member.recent_reports.length > 0 ? (
                      <ul className="mini-timeline">
                        {member.recent_reports.map((report, rIdx) => (
                          <li key={rIdx}>
                            <span className="mini-date">
                              {new Date(report.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                            </span>
                            <span className="mini-type">{report.type}</span>
                            <p className="mini-findings">{report.findings}</p>
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <p className="no-reports">No reports shared yet.</p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default FamilyDashboard;
