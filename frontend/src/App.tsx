import React, { useState } from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';
import { ThemeProvider } from './context/ThemeContext';
import { Navbar } from './components/Navbar';
import { Sidebar } from './components/Sidebar';
import { Overview } from './pages/Overview';
import { Incidents } from './pages/Incidents';
import { IncidentDetail } from './pages/IncidentDetail';
import { Projects } from './pages/Projects';
import { TeamsAndRouting } from './pages/TeamsAndRouting';
import { Integrations } from './pages/Integrations';
import { Settings } from './pages/Settings';
import { AuditLogs } from './pages/AuditLogs';
import { Login } from './pages/Login';
import { Register } from './pages/Register';

const DashboardContent: React.FC = () => {
  const { user, loading } = useAuth();
  const [authView, setAuthView] = useState<'login' | 'register'>('login');
  const [currentTab, setCurrentTab] = useState('overview');
  const [selectedIncidentId, setSelectedIncidentId] = useState<string | null>(null);

  if (loading) {
    return (
      <div style={{ height: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', backgroundColor: 'var(--bg-primary)', color: 'var(--text-muted)' }}>
        Initialising DevAlert Platform...
      </div>
    );
  }

  if (!user) {
    return authView === 'login' ? (
      <Login onSwitchToRegister={() => setAuthView('register')} />
    ) : (
      <Register onSwitchToLogin={() => setAuthView('login')} />
    );
  }

  const handleSelectIncident = (id: string) => {
    setSelectedIncidentId(id);
  };

  const handleBackToIncidents = () => {
    setSelectedIncidentId(null);
  };

  const handleTabChange = (tab: string) => {
    setSelectedIncidentId(null);
    setCurrentTab(tab);
  };

  return (
    <div className="app-container">
      <Sidebar currentTab={currentTab} onTabChange={handleTabChange} />

      <div className="main-content">
        <Navbar />

        <main className="page-body">
          {selectedIncidentId ? (
            <IncidentDetail incidentId={selectedIncidentId} onBack={handleBackToIncidents} />
          ) : (
            <>
              {currentTab === 'overview' && (
                <Overview onSelectIncident={handleSelectIncident} onNavigateTab={handleTabChange} />
              )}
              {currentTab === 'incidents' && (
                <Incidents onSelectIncident={handleSelectIncident} />
              )}
              {currentTab === 'projects' && (
                <Projects onNavigateTab={handleTabChange} />
              )}
              {currentTab === 'routing' && (
                <TeamsAndRouting />
              )}
              {currentTab === 'integrations' && (
                <Integrations />
              )}
              {currentTab === 'audit' && (
                <AuditLogs />
              )}
              {currentTab === 'settings' && (
                <Settings />
              )}
            </>
          )}
        </main>
      </div>
    </div>
  );
};

export const App: React.FC = () => {
  return (
    <ThemeProvider>
      <AuthProvider>
        <DashboardContent />
      </AuthProvider>
    </ThemeProvider>
  );
};

export default App;
