import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { OverviewAnalytics, Incident } from '../types';
import { MetricCard } from '../components/MetricCard';
import { SeverityBadge } from '../components/SeverityBadge';
import { StatusBadge } from '../components/StatusBadge';
import { PhaseBadge } from '../components/PhaseBadge';
import { TrendChart } from '../components/TrendChart';
import { Activity, AlertOctagon, CheckCircle2, ShieldAlert, ArrowRight } from 'lucide-react';

interface OverviewProps {
  onSelectIncident: (id: string) => void;
  onNavigateTab: (tab: string) => void;
}

export const Overview: React.FC<OverviewProps> = ({ onSelectIncident, onNavigateTab }) => {
  const [data, setData] = useState<OverviewAnalytics | null>(null);
  const [recentIncidents, setRecentIncidents] = useState<Incident[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadOverview();
  }, []);

  const loadOverview = async () => {
    try {
      setLoading(true);
      const [analyticsData, incidentsData] = await Promise.all([
        api.getOverview(),
        api.getIncidents({ limit: '6' }),
      ]);
      setData(analyticsData);
      setRecentIncidents(incidentsData);
    } catch (err) {
      console.error('Error loading dashboard overview:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading && !data) {
    return <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>Loading dashboard metrics...</div>;
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Top Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 style={{ fontSize: '24px', fontWeight: 700 }}>System Health Overview</h1>
          <p style={{ color: 'var(--text-muted)', fontSize: '14px', marginTop: '4px' }}>
            Live error monitoring, developer routing, and incident analytics.
          </p>
        </div>
        <button onClick={loadOverview} className="btn btn-secondary">
          Refresh Metrics
        </button>
      </div>

      {/* Metric Cards Row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px' }}>
        <MetricCard
          title="Total Events Ingested"
          value={data?.total_events || 0}
          icon={<Activity size={20} />}
          subtitle="All recorded error occurrences"
        />
        <MetricCard
          title="Active Open Incidents"
          value={data?.open_incidents || 0}
          icon={<ShieldAlert size={20} />}
          subtitle="Requiring triage or resolution"
          trendColor="var(--high)"
        />
        <MetricCard
          title="Critical Incidents"
          value={data?.critical_incidents || 0}
          icon={<AlertOctagon size={20} />}
          subtitle="Immediate action required"
          trendColor="var(--critical)"
        />
        <MetricCard
          title="Resolved Incidents"
          value={data?.resolved_incidents || 0}
          icon={<CheckCircle2 size={20} />}
          subtitle="Closed issues"
          trendColor="var(--success)"
        />
      </div>

      {/* Trend & Breakdown Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '20px' }}>
        {/* Trend Chart */}
        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
            <h3 style={{ fontSize: '16px', fontWeight: 600 }}>Error Ingestion Trends (7 Days)</h3>
            <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Daily Volume</span>
          </div>
          <TrendChart data={data?.error_trends || []} />
        </div>

        {/* Errors by Phase Breakdown */}
        <div className="card">
          <h3 style={{ fontSize: '16px', fontWeight: 600, marginBottom: '16px' }}>Development Phase Distribution</h3>
          {data?.errors_by_phase && data.errors_by_phase.length > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {data.errors_by_phase.map((item, idx) => (
                <div key={idx} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <PhaseBadge phase={item.name} />
                  <span style={{ fontSize: '14px', fontWeight: 600, color: 'var(--text-primary)' }}>
                    {item.count} events
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <div style={{ color: 'var(--text-muted)', fontSize: '13px' }}>No phase telemetry recorded yet.</div>
          )}
        </div>
      </div>

      {/* Secondary Distribution Row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '20px' }}>
        <div className="card">
          <h3 style={{ fontSize: '15px', fontWeight: 600, marginBottom: '14px' }}>Errors by Environment</h3>
          {data?.errors_by_environment.map((item, i) => (
            <div key={i} style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 0', borderBottom: '1px solid var(--border-subtle)', fontSize: '13px' }}>
              <span style={{ textTransform: 'capitalize', color: 'var(--text-secondary)' }}>{item.name}</span>
              <span style={{ fontWeight: 600 }}>{item.count}</span>
            </div>
          ))}
          {(!data?.errors_by_environment || data.errors_by_environment.length === 0) && (
            <span style={{ color: 'var(--text-muted)', fontSize: '13px' }}>No environment data.</span>
          )}
        </div>

        <div className="card">
          <h3 style={{ fontSize: '15px', fontWeight: 600, marginBottom: '14px' }}>Errors by Severity</h3>
          {data?.errors_by_severity.map((item, i) => (
            <div key={i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '6px 0', borderBottom: '1px solid var(--border-subtle)', fontSize: '13px' }}>
              <SeverityBadge severity={item.name} />
              <span style={{ fontWeight: 600 }}>{item.count}</span>
            </div>
          ))}
          {(!data?.errors_by_severity || data.errors_by_severity.length === 0) && (
            <span style={{ color: 'var(--text-muted)', fontSize: '13px' }}>No severity data.</span>
          )}
        </div>

        <div className="card">
          <h3 style={{ fontSize: '15px', fontWeight: 600, marginBottom: '14px' }}>Errors by Project</h3>
          {data?.errors_by_project.map((item, i) => (
            <div key={i} style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 0', borderBottom: '1px solid var(--border-subtle)', fontSize: '13px' }}>
              <span style={{ color: 'var(--text-secondary)' }}>{item.name}</span>
              <span style={{ fontWeight: 600 }}>{item.count}</span>
            </div>
          ))}
          {(!data?.errors_by_project || data.errors_by_project.length === 0) && (
            <span style={{ color: 'var(--text-muted)', fontSize: '13px' }}>No projects registered yet.</span>
          )}
        </div>
      </div>

      {/* Recent Incidents Table */}
      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <div>
            <h3 style={{ fontSize: '16px', fontWeight: 600 }}>Recent Incidents</h3>
            <p style={{ fontSize: '13px', color: 'var(--text-muted)' }}>Latest grouped runtime issues and automatic assignments</p>
          </div>
          <button onClick={() => onNavigateTab('incidents')} className="btn btn-secondary" style={{ fontSize: '13px' }}>
            View All Incidents <ArrowRight size={14} />
          </button>
        </div>

        {recentIncidents.length > 0 ? (
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>Severity</th>
                  <th>Incident / Error</th>
                  <th>Project</th>
                  <th>Env / Phase</th>
                  <th>Occurrences</th>
                  <th>Assigned To</th>
                  <th>Status</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {recentIncidents.map(inc => (
                  <tr key={inc.id}>
                    <td><SeverityBadge severity={inc.severity} /></td>
                    <td>
                      <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{inc.error_type}</div>
                      <div style={{ fontSize: '12px', color: 'var(--text-muted)', maxWidth: '300px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                        {inc.message}
                      </div>
                    </td>
                    <td>{inc.project_name || 'Project'}</td>
                    <td>
                      <div style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
                        <span style={{ fontSize: '12px', textTransform: 'capitalize' }}>{inc.environment}</span>
                        <PhaseBadge phase={inc.phase} />
                      </div>
                    </td>
                    <td><strong>{inc.occurrence_count}×</strong></td>
                    <td>
                      <span style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
                        {inc.assigned_email || inc.assigned_team || 'Unassigned'}
                      </span>
                    </td>
                    <td><StatusBadge status={inc.status} /></td>
                    <td>
                      <button
                        onClick={() => onSelectIncident(inc.id)}
                        className="btn btn-secondary"
                        style={{ padding: '4px 10px', fontSize: '12px' }}
                      >
                        Inspect
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div style={{ padding: '32px', textAlign: 'center', color: 'var(--text-muted)' }}>
            No incidents reported yet. Integrate an application using the Python SDK or Webhooks to start monitoring!
          </div>
        )}
      </div>
    </div>
  );
};
