import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { Incident, ErrorEvent, NotificationRecord } from '../types';
import { SeverityBadge } from '../components/SeverityBadge';
import { StatusBadge } from '../components/StatusBadge';
import { PhaseBadge } from '../components/PhaseBadge';
import {
  ArrowLeft,
  Bot,
  Clock,
  Send,
  UserCheck,
  CheckCircle,
  AlertTriangle,
  RotateCcw,
  Sparkles,
} from 'lucide-react';

interface IncidentDetailProps {
  incidentId: string;
  onBack: () => void;
}

export const IncidentDetail: React.FC<IncidentDetailProps> = ({ incidentId, onBack }) => {
  const [incident, setIncident] = useState<Incident | null>(null);
  const [activeTab, setActiveTab] = useState<'details' | 'events' | 'notifications'>('details');
  const [loading, setLoading] = useState(true);
  const [updating, setUpdating] = useState(false);
  const [aiAnalyzing, setAiAnalyzing] = useState(false);

  // Assignment edit
  const [assignedEmail, setAssignedEmail] = useState('');
  const [assignedTeam, setAssignedTeam] = useState('');

  useEffect(() => {
    fetchIncident();
  }, [incidentId]);

  const fetchIncident = async () => {
    try {
      setLoading(true);
      const data = await api.getIncident(incidentId);
      setIncident(data);
      setAssignedEmail(data.assigned_email || '');
      setAssignedTeam(data.assigned_team || '');
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleStatusChange = async (newStatus: string) => {
    try {
      setUpdating(true);
      const updated = await api.updateIncident(incidentId, { status: newStatus });
      setIncident(prev => prev ? { ...prev, status: updated.status } : null);
    } catch (err) {
      alert('Failed to update status');
    } finally {
      setUpdating(false);
    }
  };

  const handleAssignmentSave = async () => {
    try {
      setUpdating(true);
      const updated = await api.updateIncident(incidentId, {
        assigned_email: assignedEmail,
        assigned_team: assignedTeam,
      });
      setIncident(prev => prev ? { ...prev, assigned_email: updated.assigned_email, assigned_team: updated.assigned_team } : null);
      alert('Assignment updated successfully.');
    } catch (err) {
      alert('Failed to save assignment');
    } finally {
      setUpdating(false);
    }
  };

  const handleRunAI = async () => {
    try {
      setAiAnalyzing(true);
      const res = await api.analyzeIncidentAI(incidentId);
      setIncident(prev => prev ? { ...prev, ai_summary: res.ai_summary, ai_suggested_fix: res.ai_suggested_fix } : null);
    } catch (err) {
      alert('AI analysis failed');
    } finally {
      setAiAnalyzing(false);
    }
  };

  if (loading && !incident) {
    return <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>Loading incident telemetry...</div>;
  }

  if (!incident) {
    return (
      <div style={{ padding: '40px', textAlign: 'center' }}>
        <p>Incident not found.</p>
        <button onClick={onBack} className="btn btn-secondary" style={{ marginTop: '12px' }}>
          Back to Incidents
        </button>
      </div>
    );
  }

  const latestEvent = incident.events && incident.events.length > 0 ? incident.events[0] : null;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Navigation and Actions Bar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
        <button onClick={onBack} className="btn btn-secondary" style={{ fontSize: '13px' }}>
          <ArrowLeft size={16} /> Back to Incidents
        </button>

        <div style={{ display: 'flex', gap: '8px' }}>
          {incident.status === 'open' && (
            <button onClick={() => handleStatusChange('acknowledged')} disabled={updating} className="btn btn-secondary">
              Acknowledge
            </button>
          )}
          {incident.status !== 'investigating' && incident.status !== 'resolved' && (
            <button onClick={() => handleStatusChange('investigating')} disabled={updating} className="btn btn-secondary">
              Investigate
            </button>
          )}
          {incident.status !== 'resolved' ? (
            <button onClick={() => handleStatusChange('resolved')} disabled={updating} className="btn btn-primary" style={{ backgroundColor: 'var(--success)' }}>
              <CheckCircle size={16} /> Mark as Resolved
            </button>
          ) : (
            <button onClick={() => handleStatusChange('reopened')} disabled={updating} className="btn btn-secondary">
              <RotateCcw size={16} /> Reopen Incident
            </button>
          )}
        </div>
      </div>

      {/* Incident Header Card */}
      <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '12px' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px' }}>
              <SeverityBadge severity={incident.severity} />
              <StatusBadge status={incident.status} />
              <PhaseBadge phase={incident.phase} />
              <span style={{ fontSize: '13px', color: 'var(--text-muted)' }}>
                Occurred <strong>{incident.occurrence_count} times</strong>
              </span>
            </div>
            <h1 style={{ fontSize: '22px', fontWeight: 700, color: 'var(--text-primary)' }}>
              {incident.error_type} in {incident.service}
            </h1>
            <p style={{ color: 'var(--text-secondary)', fontSize: '14px', marginTop: '4px' }}>
              {incident.message}
            </p>
          </div>

          <div style={{ fontSize: '12px', color: 'var(--text-muted)', textAlign: 'right' }}>
            <div>Incident ID: <code>{incident.id}</code></div>
            <div>Fingerprint: <code>{incident.fingerprint.slice(0, 16)}...</code></div>
          </div>
        </div>

        {/* Routing & Ownership banner */}
        <div style={{ padding: '12px 16px', backgroundColor: 'var(--bg-surface)', borderRadius: '6px', fontSize: '13px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '10px' }}>
          <div>
            <strong>Assigned Developer / Team: </strong>
            <span style={{ color: 'var(--accent)' }}>{incident.assigned_email || incident.assigned_team || 'Unassigned'}</span>
            <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '2px' }}>
              Routing reason: {incident.routing_reason || 'Default routing policy'}
            </div>
          </div>

          <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
            <input
              type="text"
              placeholder="Developer Email"
              value={assignedEmail}
              onChange={e => setAssignedEmail(e.target.value)}
              style={{ width: '180px', padding: '4px 8px', fontSize: '12px' }}
            />
            <input
              type="text"
              placeholder="Team"
              value={assignedTeam}
              onChange={e => setAssignedTeam(e.target.value)}
              style={{ width: '120px', padding: '4px 8px', fontSize: '12px' }}
            />
            <button onClick={handleAssignmentSave} className="btn btn-secondary" style={{ padding: '4px 10px', fontSize: '12px' }}>
              Reassign
            </button>
          </div>
        </div>
      </div>

      {/* AI Troubleshooting Assistant Box */}
      <div className="card" style={{ borderLeft: '4px solid #818cf8', backgroundColor: 'rgba(99, 102, 241, 0.05)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Bot size={20} color="#818cf8" />
            <h3 style={{ fontSize: '15px', fontWeight: 600, color: '#a5b4fc' }}>
              AI-Assisted Error Diagnosis & Remediation
            </h3>
            <span style={{ fontSize: '11px', padding: '2px 6px', borderRadius: '4px', backgroundColor: 'rgba(129, 140, 248, 0.2)', color: '#c7d2fe' }}>
              Safe Redacted Input
            </span>
          </div>

          <button onClick={handleRunAI} disabled={aiAnalyzing} className="btn btn-secondary" style={{ fontSize: '12px', padding: '4px 10px' }}>
            <Sparkles size={13} color="#818cf8" /> {aiAnalyzing ? 'Analyzing...' : 'Re-analyze with AI'}
          </button>
        </div>

        <div style={{ fontSize: '14px', lineHeight: 1.6, color: 'var(--text-primary)' }}>
          {incident.ai_summary ? (
            <div>
              <p style={{ marginBottom: '8px', fontWeight: 500 }}>{incident.ai_summary}</p>
              {incident.ai_suggested_fix && (
                <div style={{ marginTop: '8px', padding: '10px 14px', backgroundColor: 'var(--bg-secondary)', borderRadius: '6px', fontSize: '13px', whiteSpace: 'pre-wrap' }}>
                  {incident.ai_suggested_fix}
                </div>
              )}
            </div>
          ) : (
            <p style={{ color: 'var(--text-muted)' }}>No diagnosis generated yet. Click "Re-analyze with AI" to generate troubleshooting suggestions.</p>
          )}
        </div>
      </div>

      {/* Tabs for Details, Event Stream, Notifications */}
      <div style={{ display: 'flex', gap: '8px', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '8px' }}>
        <button
          onClick={() => setActiveTab('details')}
          style={{
            padding: '8px 16px',
            borderRadius: '6px',
            border: 'none',
            background: activeTab === 'details' ? 'var(--bg-surface)' : 'transparent',
            color: activeTab === 'details' ? 'var(--text-primary)' : 'var(--text-secondary)',
            fontWeight: 600,
            cursor: 'pointer',
          }}
        >
          Stack Trace & Metadata
        </button>

        <button
          onClick={() => setActiveTab('events')}
          style={{
            padding: '8px 16px',
            borderRadius: '6px',
            border: 'none',
            background: activeTab === 'events' ? 'var(--bg-surface)' : 'transparent',
            color: activeTab === 'events' ? 'var(--text-primary)' : 'var(--text-secondary)',
            fontWeight: 600,
            cursor: 'pointer',
          }}
        >
          Event History ({incident.events?.length || 0})
        </button>

        <button
          onClick={() => setActiveTab('notifications')}
          style={{
            padding: '8px 16px',
            borderRadius: '6px',
            border: 'none',
            background: activeTab === 'notifications' ? 'var(--bg-surface)' : 'transparent',
            color: activeTab === 'notifications' ? 'var(--text-primary)' : 'var(--text-secondary)',
            fontWeight: 600,
            cursor: 'pointer',
          }}
        >
          Dispatched Alerts ({incident.notifications?.length || 0})
        </button>
      </div>

      {/* Tab 1: Details & Stack Trace */}
      {activeTab === 'details' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div className="card">
            <h3 style={{ fontSize: '15px', fontWeight: 600, marginBottom: '12px' }}>Sanitized Stack Trace</h3>
            {latestEvent?.sanitized_stack_trace ? (
              <pre className="code-snippet" style={{ color: '#f87171' }}>
                {latestEvent.sanitized_stack_trace}
              </pre>
            ) : (
              <p style={{ color: 'var(--text-muted)', fontSize: '13px' }}>No stack trace captured for this incident.</p>
            )}
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '16px' }}>
            <div className="card">
              <h3 style={{ fontSize: '15px', fontWeight: 600, marginBottom: '12px' }}>Integration Metadata</h3>
              <pre className="code-snippet" style={{ color: 'var(--accent)' }}>
                {JSON.stringify(latestEvent?.metadata_json || {}, null, 2)}
              </pre>
            </div>

            <div className="card">
              <h3 style={{ fontSize: '15px', fontWeight: 600, marginBottom: '12px' }}>Request Context</h3>
              <pre className="code-snippet" style={{ color: 'var(--text-secondary)' }}>
                {JSON.stringify(latestEvent?.request_data || {}, null, 2)}
              </pre>
            </div>
          </div>
        </div>
      )}

      {/* Tab 2: Event History */}
      {activeTab === 'events' && (
        <div className="card" style={{ padding: '0' }}>
          <div className="table-container" style={{ border: 'none' }}>
            <table>
              <thead>
                <tr>
                  <th>Timestamp</th>
                  <th>Source</th>
                  <th>Environment</th>
                  <th>Phase</th>
                  <th>Host / Node</th>
                  <th>Release</th>
                </tr>
              </thead>
              <tbody>
                {incident.events?.map(evt => (
                  <tr key={evt.id}>
                    <td>{new Date(evt.timestamp).toLocaleString()}</td>
                    <td><code>{evt.source}</code></td>
                    <td><span style={{ textTransform: 'capitalize' }}>{evt.environment}</span></td>
                    <td><PhaseBadge phase={evt.phase} /></td>
                    <td>{evt.host || 'unknown'}</td>
                    <td>{evt.release || 'latest'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Tab 3: Notifications History */}
      {activeTab === 'notifications' && (
        <div className="card" style={{ padding: '0' }}>
          <div className="table-container" style={{ border: 'none' }}>
            <table>
              <thead>
                <tr>
                  <th>Type</th>
                  <th>Recipient Email</th>
                  <th>Subject</th>
                  <th>Status</th>
                  <th>Attempts</th>
                  <th>Sent At</th>
                </tr>
              </thead>
              <tbody>
                {incident.notifications?.map(notif => (
                  <tr key={notif.id}>
                    <td><code>{notif.notification_type}</code></td>
                    <td><strong>{notif.recipient_email}</strong></td>
                    <td style={{ maxWidth: '280px', overflow: 'hidden', textOverflow: 'ellipsis' }}>{notif.subject}</td>
                    <td>
                      <span
                        className="badge"
                        style={{
                          backgroundColor: notif.status === 'sent' ? 'var(--success-bg)' : 'var(--critical-bg)',
                          color: notif.status === 'sent' ? 'var(--success)' : 'var(--critical)',
                        }}
                      >
                        {notif.status}
                      </span>
                    </td>
                    <td>{notif.attempts_count}</td>
                    <td>{notif.sent_at ? new Date(notif.sent_at).toLocaleString() : 'Pending'}</td>
                  </tr>
                ))}
                {(!incident.notifications || incident.notifications.length === 0) && (
                  <tr>
                    <td colSpan={6} style={{ textAlign: 'center', padding: '24px', color: 'var(--text-muted)' }}>
                      No notifications recorded for this incident.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
