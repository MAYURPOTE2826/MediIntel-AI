import React, { useState, useEffect } from 'react';
import { FileText, Calendar, Activity, CheckCircle, Clock, Stethoscope, User, HeartPulse, TrendingUp, TrendingDown, Minus } from 'lucide-react';
import './Timeline.css';

const Timeline = () => {
  const [timelineData, setTimelineData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({
    startDate: '',
    endDate: '',
    reportType: ''
  });

  useEffect(() => {
    fetchTimelineData();
  }, [filters]);

  const fetchTimelineData = async () => {
    setLoading(true);
    try {
      // Build query string
      const queryParams = new URLSearchParams();
      if (filters.startDate) queryParams.append('start_date', new Date(filters.startDate).toISOString());
      if (filters.endDate) queryParams.append('end_date', new Date(filters.endDate).toISOString());
      if (filters.reportType) queryParams.append('report_type', filters.reportType);
      
      const queryString = queryParams.toString();
      const url = `/api/timeline${queryString ? `?${queryString}` : ''}`;
      
      // We would normally use the backend endpoint here
      // const response = await fetch(url, { headers: { Authorization: `Bearer ${token}` } });
      // const data = await response.json();
      
      // Mock data based on acceptance criteria (5 reports over 6 months)
      // Removing this once endpoint is fully connected on the frontend
      setTimeout(() => {
        setTimelineData([
          {
            id: '1',
            date: '2026-08-10T10:30:00Z',
            report_type: 'Blood Test',
            document_type: 'Comprehensive Metabolic Panel',
            key_findings: 'Cholesterol levels have improved. Fasting glucose is within normal limits. Vitamin D is slightly low.',
            specialist_seen: 'General Physician',
            status: 'Reviewed',
            trend: 'Improving'
          },
          {
            id: '2',
            date: '2026-06-15T14:20:00Z',
            report_type: 'ECG',
            document_type: 'Electrocardiogram',
            key_findings: 'Normal sinus rhythm. No acute ischemic changes noted compared to previous ECG.',
            specialist_seen: 'Cardiologist',
            status: 'Reviewed',
            trend: 'Stable'
          },
          {
            id: '3',
            date: '2026-05-02T09:15:00Z',
            report_type: 'Chest X-Ray',
            document_type: 'PA and Lateral View',
            key_findings: 'Clear lung fields. No focal consolidation, pleural effusion, or pneumothorax.',
            specialist_seen: 'Radiologist',
            status: 'Reviewed',
            trend: 'Stable'
          },
          {
            id: '4',
            date: '2026-03-20T11:45:00Z',
            report_type: 'Blood Test',
            document_type: 'Lipid Panel',
            key_findings: 'Elevated LDL cholesterol. Recommended dietary changes and follow-up in 3 months.',
            specialist_seen: 'General Physician',
            status: 'Reviewed',
            trend: 'Worsening'
          },
          {
            id: '5',
            date: '2026-02-10T16:00:00Z',
            report_type: 'MRI',
            document_type: 'Lumbar Spine MRI',
            key_findings: 'Mild disc desiccation at L4-L5 without significant stenosis or nerve root impingement.',
            specialist_seen: 'Neurologist',
            status: 'Pending Review',
            trend: 'Stable'
          }
        ]);
        setLoading(false);
      }, 800);
      
    } catch (error) {
      console.error("Failed to fetch timeline", error);
      setLoading(false);
    }
  };

  const handleFilterChange = (e) => {
    const { name, value } = e.target;
    setFilters(prev => ({ ...prev, [name]: value }));
  };

  const getStatusIcon = (status) => {
    if (status === 'Reviewed') return <CheckCircle size={16} />;
    return <Clock size={16} />;
  };

  const getTrendIcon = (trend) => {
    if (trend === 'Improving') return <TrendingUp size={16} />;
    if (trend === 'Worsening') return <TrendingDown size={16} />;
    return <Minus size={16} />;
  };

  const getTypeIcon = (type) => {
    if (type.toLowerCase().includes('blood')) return <Activity size={16} />;
    if (type.toLowerCase().includes('ecg') || type.toLowerCase().includes('cardio')) return <HeartPulse size={16} />;
    return <FileText size={16} />;
  };

  return (
    <div className="timeline-container">
      <div className="timeline-header">
        <h1 className="timeline-title text-gradient">Your Health Journey</h1>
        <p style={{ color: 'var(--text-secondary)' }}>Track and understand your medical history over time</p>
      </div>

      <div className="timeline-filters">
        <div className="filter-group">
          <label className="filter-label">From Date</label>
          <input 
            type="date" 
            name="startDate" 
            className="filter-input" 
            value={filters.startDate}
            onChange={handleFilterChange}
          />
        </div>
        <div className="filter-group">
          <label className="filter-label">To Date</label>
          <input 
            type="date" 
            name="endDate" 
            className="filter-input" 
            value={filters.endDate}
            onChange={handleFilterChange}
          />
        </div>
        <div className="filter-group">
          <label className="filter-label">Report Type</label>
          <select 
            name="reportType" 
            className="filter-select"
            value={filters.reportType}
            onChange={handleFilterChange}
          >
            <option value="">All Types</option>
            <option value="Blood Test">Blood Test</option>
            <option value="ECG">ECG</option>
            <option value="Chest X-Ray">Chest X-Ray</option>
            <option value="MRI">MRI</option>
          </select>
        </div>
      </div>

      {loading ? (
        <div className="loading-spinner">
          <div className="spinner"></div>
        </div>
      ) : timelineData.length === 0 ? (
        <div className="empty-state">
          <FileText size={48} style={{ marginBottom: '1rem', opacity: 0.5 }} />
          <h3>No reports found</h3>
          <p>Try adjusting your filters or upload a new medical report.</p>
        </div>
      ) : (
        <div className="timeline">
          {timelineData.map((item) => (
            <div className="timeline-item" key={item.id}>
              <div className="timeline-marker"></div>
              <div className="timeline-card">
                <div className="card-header">
                  <div className="card-date">
                    <Calendar size={18} />
                    {new Date(item.date).toLocaleDateString('en-US', { 
                      year: 'numeric', month: 'long', day: 'numeric' 
                    })}
                  </div>
                  <div className="card-type">
                    {getTypeIcon(item.report_type)}
                    {item.report_type}
                  </div>
                </div>
                
                <div className="card-body">
                  <h4 style={{ marginBottom: '0.5rem', fontSize: '1.1rem' }}>{item.document_type}</h4>
                  <p className="card-findings">{item.key_findings}</p>
                  
                  <div className={`trend-badge trend-${item.trend.toLowerCase()}`}>
                    {getTrendIcon(item.trend)}
                    Trend: {item.trend}
                  </div>
                </div>
                
                <div className="card-footer">
                  <div className="specialist-info">
                    <User size={16} color="var(--accent-primary)" />
                    Seen by: <strong>{item.specialist_seen}</strong>
                  </div>
                  
                  <div className={`status-badge ${item.status === 'Reviewed' ? 'status-reviewed' : 'status-pending'}`}>
                    {getStatusIcon(item.status)}
                    {item.status}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default Timeline;
