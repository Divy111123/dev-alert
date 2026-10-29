import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { Incident, Project } from '../types';
import { SeverityBadge } from '../components/SeverityBadge';
import { StatusBadge } from '../components/StatusBadge';
import { PhaseBadge } from '../components/PhaseBadge';
import { Search, Filter, RefreshCw, Eye } from 'lucide-react';

interface IncidentsProps {
  onSelectIncident: (id: string) => void;
}

export const Incidents: React.FC<IncidentsProps> = ({ onSelectIncident }) => {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);

  // Filters
  const [search, setSearch] = useState('');
  const [selectedProject, setSelectedProject] = useState('');
  const [selectedSeverity, setSelectedSeverity] = useState('');
  const [selectedStatus, setSelectedStatus] = useState('');
  const [selectedPhase, setSelectedPhase] = useState('');
  const [selectedEnv, setSelectedEnv] = useState('');

  useEffect(() => {
    loadProjects();
    fetchIncidents();
  }, []);

  const loadProjects = async () => {
    try {
      const projs = await api.getProjects();
      setProjects(projs);
    } catch (err) {
      console.error(err);
    }
  };

  const fetchIncidents = async () => {
    try {
      setLoading(true);
      const filters: Record<string, string> = {};
      if (search) filters.search = search;
      if (selectedProject) filters.project_id = selectedProject;
      if (selectedSeverity) filters.severity = selectedSeverity;
      if (selectedStatus) filters.status = selectedStatus;
      if (selectedPhase) filters.phase = selectedPhase;
      if (selectedEnv) filters.environment = selectedEnv;

      const data = await api.getIncidents(filters);
      setIncidents(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    fetchIncidents();
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 style={{ fontSize: '24px', fontWeight: 700 }}>Incidents Management</h1>
          <p style={{ color: 'var(--text-muted)', fontSize: '14px', marginTop: '4px' }}>
            Browse, search, investigate, and triage automatically grouped application failures.
          </p>
        </div>
        <button onClick={fetchIncidents} className="btn btn-secondary">
          <RefreshCw size={14} /> Refresh
        </button>
      </div>

      {/* Filter and Search Bar */}
      <div className="card" style={{ padding: '16px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
        <form onSubmit={handleSearchSubmit} style={{ display: 'flex', gap: '10px' }}>
          <div style={{ position: 'relative', flex: 1 }}>
            <Search size={16} style={{ position: 'absolute', left: '12px', top: '12px', color: 'var(--text-muted)' }} />
            <input
              type="text"
              placeholder="Search by error type, message, or service name..."
              value={search}
              onChange={e => setSearch(e.target.value)}
              style={{ paddingLeft: '36px' }}
            />
          </div>
          <button type="submit" className="btn btn-primary">
            Search
          </button>
        </form>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: '10px' }}>
          <select value={selectedProject} onChange={e => setSelectedProject(e.target.value)}>
            <option value="">All Projects</option>
            {projects.map(p => (
              <option key={p.id} value={p.id}>{p.name}</option>
            ))}
          </select>

          <select value={selectedSeverity} onChange={e => setSelectedSeverity(e.target.value)}>
            <option value="">All Severities</option>
            <option value="critical">Critical</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>

          <select value={selectedStatus} onChange={e => setSelectedStatus(e.target.value)}>
            <option value="">All Statuses</option>
            <option value="open">Open</option>
            <option value="acknowledged">Acknowledged</option>
            <option value="investigating">Investigating</option>
            <option value="resolved">Resolved</option>
            <option value="reopened">Reopened</option>
          </select>

          <select value={selectedPhase} onChange={e => setSelectedPhase(e.target.value)}>
            <option value="">All Phases</option>
            <option value="Development">Development</option>
            <option value="Testing">Testing</option>
            <option value="Staging">Staging</option>
            <option value="Build">Build</option>
            <option value="Deployment">Deployment</option>
            <option value="Production">Production</option>
          </select>

          <select value={selectedEnv} onChange={e => setSelectedEnv(e.target.value)}>
            <option value="">All Environments</option>
            <option value="production">Production</option>
            <option value="staging">Staging</option>
            <option value="testing">Testing</option>
            <option value="development">Development</option>
          </select>

          <button onClick={fetchIncidents} className="btn btn-secondary">
            <Filter size={14} /> Apply Filters
          </button>
        </div>
      </div>

      {/* Incidents Table */}
      <div className="card" style={{ padding: '0' }}>
        {loading ? (
          <div style={{ padding: '32px', textAlign: 'center', color: 'var(--text-muted)' }}>Loading incidents...</div>
        ) : incidents.length > 0 ? (
          <div className="table-container" style={{ border: 'none' }}>
            <table>
              <thead>
                <tr>
                  <th>Severity</th>
                  <th>Incident</th>
                  <th>Project</th>
                  <th>Environment</th>
                  <th>Phase</th>
                  <th>Occurrences</th>
                  <th>Assigned Owner</th>
                  <th>Status</th>
                  <th>Last Seen</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {incidents.map(inc => (
                  <tr key={inc.id}>
                    <td><SeverityBadge severity={inc.severity} /></td>
                    <td style={{ maxWidth: '300px' }}>
                      <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{inc.error_type}</div>
                      <div style={{ fontSize: '12px', color: 'var(--text-muted)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                        {inc.message}
                      </div>
                    </td>
                    <td>{inc.project_name}</td>
                    <td><span style={{ textTransform: 'capitalize' }}>{inc.environment}</span></td>
                    <td><PhaseBadge phase={inc.phase} /></td>
                    <td><strong>{inc.occurrence_count}×</strong></td>
                    <td>
                      <div style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
                        {inc.assigned_email || inc.assigned_team || 'Unassigned'}
                      </div>
                    </td>
                    <td><StatusBadge status={inc.status} /></td>
                    <td style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                      {new Date(inc.last_seen).toLocaleString()}
                    </td>
                    <td>
                      <button
                        onClick={() => onSelectIncident(inc.id)}
                        className="btn btn-secondary"
                        style={{ padding: '6px 12px', fontSize: '12px' }}
                      >
                        <Eye size={13} /> View
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div style={{ padding: '48px', textAlign: 'center', color: 'var(--text-muted)' }}>
            No matching incidents found for the selected filter criteria.
          </div>
        )}
      </div>
    </div>
  );
};
