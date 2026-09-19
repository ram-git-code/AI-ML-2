import React, { useEffect, useState } from 'react';
import { getBackendHealth, getPostgresHealth, HealthResponse } from '../api/healthApi';

export const Dashboard: React.FC = () => {
  const [backendStatus, setBackendStatus] = useState<HealthResponse | null>(null);
  const [postgresStatus, setPostgresStatus] = useState<HealthResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [lastChecked, setLastChecked] = useState<string>('');

  const fetchHealthStatuses = async () => {
    setLoading(true);
    const [bRes, pRes] = await Promise.all([
      getBackendHealth(),
      getPostgresHealth(),
    ]);

    setBackendStatus(bRes);
    setPostgresStatus(pRes);
    setLastChecked(new Date().toLocaleTimeString());
    setLoading(false);
  };

  useEffect(() => {
    fetchHealthStatuses();
    const interval = setInterval(fetchHealthStatuses, 10000);
    return () => clearInterval(interval);
  }, []);

  const renderBadge = (status?: string) => {
    const isConnected = status === 'ok' || status === 'CONNECTED';
    return (
      <div className={`status-badge ${isConnected ? 'connected' : 'disconnected'}`}>
        <span className={`status-dot ${isConnected ? 'connected' : 'disconnected'}`}></span>
        {isConnected ? 'CONNECTED' : 'DISCONNECTED'}
      </div>
    );
  };

  return (
    <div className="dashboard-container">
      <header className="dashboard-header">
        <h1 className="dashboard-title">AI Question Bank & RAG Tutor</h1>
        <p className="dashboard-subtitle">Phase 1 Infrastructure & Service Connection Status</p>
        {lastChecked && (
          <p style={{ fontSize: '0.85rem', color: '#64748b', marginTop: '0.5rem' }}>
            Auto-refreshing every 10s • Last checked: {lastChecked}
          </p>
        )}
      </header>

      <div className="status-grid">
        {/* Backend Card */}
        <div className="status-card">
          <div className="card-top">
            <h2 className="service-name">FastAPI Backend</h2>
            {renderBadge(backendStatus?.status)}
          </div>
          <div className="card-details">
            <p><strong>App:</strong> {backendStatus?.app_name || 'AI Question Bank API'}</p>
            <p><strong>Version:</strong> {backendStatus?.version || '1.0.0'}</p>
            <p><strong>Docs URL:</strong> <a href="http://localhost:8000/docs" target="_blank" rel="noreferrer" style={{ color: '#38bdf8' }}>http://localhost:8000/docs</a></p>
            {backendStatus?.error && <div className="error-msg">{backendStatus.error}</div>}
          </div>
        </div>

        {/* PostgreSQL Card */}
        <div className="status-card">
          <div className="card-top">
            <h2 className="service-name">PostgreSQL DB</h2>
            {renderBadge(postgresStatus?.status)}
          </div>
          <div className="card-details">
            <p><strong>Host:</strong> localhost:5432</p>
            <p><strong>Database:</strong> ai_project</p>
            <p><strong>Role:</strong> Source of Truth</p>
            {postgresStatus?.details && <p style={{ color: '#34d399', fontSize: '0.85rem' }}>✓ {postgresStatus.details}</p>}
            {postgresStatus?.error && <div className="error-msg">{postgresStatus.error}</div>}
          </div>
        </div>

      </div>

      <div className="refresh-bar">
        <button className="btn-refresh" onClick={fetchHealthStatuses} disabled={loading}>
          {loading ? 'Checking Connections...' : '🔄 Refresh Health Status'}
        </button>
      </div>
    </div>
  );
};
