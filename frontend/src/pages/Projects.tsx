import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { Project, ApiKey } from '../types';
import { Modal } from '../components/Modal';
import { Plus, Key, Mail, Trash2, Copy, Check, ExternalLink, ShieldCheck } from 'lucide-react';

interface ProjectsProps {
  onNavigateTab: (tab: string) => void;
}

export const Projects: React.FC<ProjectsProps> = ({ onNavigateTab }) => {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);

  // Modal states
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [isKeysOpen, setIsKeysOpen] = useState(false);
  const [activeProject, setActiveProject] = useState<Project | null>(null);
  const [apiKeys, setApiKeys] = useState<ApiKey[]>([]);
  const [newKeyName, setNewKeyName] = useState('');
  const [rawCreatedKey, setRawCreatedKey] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  // Form state
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [repoUrl, setRepoUrl] = useState('');
  const [defaultOwnerEmail, setDefaultOwnerEmail] = useState('');
  const [defaultTeam, setDefaultTeam] = useState('Engineering');
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    loadProjects();
  }, []);

  const loadProjects = async () => {
    try {
      setLoading(true);
      const data = await api.getProjects();
      setProjects(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setSubmitting(true);
      await api.createProject({
        name,
        description,
        repository_url: repoUrl,
        default_owner_email: defaultOwnerEmail,
        default_team: defaultTeam,
      });
      setIsCreateOpen(false);
      setName('');
      setDescription('');
      setRepoUrl('');
      setDefaultOwnerEmail('');
      loadProjects();
    } catch (err: any) {
      alert(err.message || 'Failed to create project');
    } finally {
      setSubmitting(false);
    }
  };

  const openKeyManager = async (project: Project) => {
    setActiveProject(project);
    setRawCreatedKey(null);
    try {
      const keys = await api.getApiKeys(project.id);
      setApiKeys(keys);
      setIsKeysOpen(true);
    } catch (err) {
      alert('Failed to load project API keys');
    }
  };

  const handleGenerateKey = async () => {
    if (!activeProject || !newKeyName) return;
    try {
      const created = await api.createApiKey(activeProject.id, newKeyName);
      setRawCreatedKey(created.raw_key);
      setNewKeyName('');
      const keys = await api.getApiKeys(activeProject.id);
      setApiKeys(keys);
    } catch (err) {
      alert('Failed to generate API key');
    }
  };

  const handleRevokeKey = async (keyId: number) => {
    if (!activeProject || !confirm('Are you sure you want to revoke this API key? Applications using it will lose access.')) return;
    try {
      await api.revokeApiKey(activeProject.id, keyId);
      const keys = await api.getApiKeys(activeProject.id);
      setApiKeys(keys);
    } catch (err) {
      alert('Failed to revoke API key');
    }
  };

  const handleSendTestEmail = async (project: Project) => {
    try {
      const res = await api.testEmailNotification(project.id);
      alert(`Success: ${res.message}`);
    } catch (err: any) {
      alert(`Error: ${err.message}`);
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 style={{ fontSize: '24px', fontWeight: 700 }}>Registered Projects</h1>
          <p style={{ color: 'var(--text-muted)', fontSize: '14px', marginTop: '4px' }}>
            Manage monitored services, API credentials, and default notification ownership.
          </p>
        </div>
        <button onClick={() => setIsCreateOpen(true)} className="btn btn-primary">
          <Plus size={16} /> Register New Project
        </button>
      </div>

      {/* Projects Grid */}
      {loading ? (
        <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>Loading projects...</div>
      ) : projects.length > 0 ? (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: '20px' }}>
          {projects.map(proj => (
            <div key={proj.id} className="card" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div>
                  <h3 style={{ fontSize: '18px', fontWeight: 600 }}>{proj.name}</h3>
                  <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '2px' }}>
                    ID: <code>{proj.id}</code>
                  </div>
                </div>
                <span className="badge" style={{ backgroundColor: 'var(--accent-subtle)', color: 'var(--accent)' }}>
                  {proj.default_team || 'Engineering'}
                </span>
              </div>

              <p style={{ fontSize: '13px', color: 'var(--text-secondary)', minHeight: '38px' }}>
                {proj.description || 'No description provided.'}
              </p>

              {/* Environments pill */}
              <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
                {proj.environments?.map(env => (
                  <span
                    key={env}
                    style={{
                      fontSize: '11px',
                      padding: '2px 8px',
                      borderRadius: '4px',
                      backgroundColor: 'var(--bg-surface)',
                      border: '1px solid var(--border-subtle)',
                      textTransform: 'capitalize',
                    }}
                  >
                    {env}
                  </span>
                ))}
              </div>

              {/* Metrics row */}
              <div style={{ display: 'flex', justifyContent: 'space-between', padding: '10px 14px', backgroundColor: 'var(--bg-surface)', borderRadius: '6px', fontSize: '12px' }}>
                <div>
                  <span style={{ color: 'var(--text-muted)' }}>Open Incidents: </span>
                  <strong style={{ color: proj.open_incidents_count > 0 ? 'var(--critical)' : 'var(--success)' }}>
                    {proj.open_incidents_count}
                  </strong>
                </div>
                <div>
                  <span style={{ color: 'var(--text-muted)' }}>Total Events: </span>
                  <strong>{proj.total_events_count}</strong>
                </div>
              </div>

              {/* Owner details */}
              <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                Default Owner: <span style={{ color: 'var(--text-primary)' }}>{proj.default_owner_email || 'Not configured'}</span>
              </div>

              {/* Actions */}
              <div style={{ display: 'flex', gap: '8px', marginTop: 'auto', paddingTop: '10px', borderTop: '1px solid var(--border-subtle)' }}>
                <button
                  onClick={() => openKeyManager(proj)}
                  className="btn btn-secondary"
                  style={{ flex: 1, fontSize: '12px' }}
                >
                  <Key size={14} /> API Keys
                </button>

                <button
                  onClick={() => handleSendTestEmail(proj)}
                  className="btn btn-secondary"
                  style={{ fontSize: '12px' }}
                  title="Send test verification email"
                >
                  <Mail size={14} /> Test Alert
                </button>

                <button
                  onClick={() => onNavigateTab('integrations')}
                  className="btn btn-secondary"
                  style={{ fontSize: '12px' }}
                  title="View setup guide"
                >
                  <ExternalLink size={14} /> Guide
                </button>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="card" style={{ padding: '48px', textAlign: 'center' }}>
          <h3>No Projects Configured</h3>
          <p style={{ color: 'var(--text-muted)', fontSize: '14px', marginTop: '8px' }}>
            Create your first project to generate an API key and start monitoring errors.
          </p>
          <button onClick={() => setIsCreateOpen(true)} className="btn btn-primary" style={{ marginTop: '16px' }}>
            <Plus size={16} /> Create Project
          </button>
        </div>
      )}

      {/* Modal: Create Project */}
      <Modal isOpen={isCreateOpen} onClose={() => setIsCreateOpen(false)} title="Register Monitored Project">
        <form onSubmit={handleCreate} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          <div>
            <label style={{ fontSize: '13px', fontWeight: 600, display: 'block', marginBottom: '6px' }}>
              Project Name *
            </label>
            <input
              type="text"
              required
              placeholder="e.g. Payment Gateway API"
              value={name}
              onChange={e => setName(e.target.value)}
            />
          </div>

          <div>
            <label style={{ fontSize: '13px', fontWeight: 600, display: 'block', marginBottom: '6px' }}>
              Description
            </label>
            <textarea
              rows={2}
              placeholder="Brief description of the service and responsibilities"
              value={description}
              onChange={e => setDescription(e.target.value)}
            />
          </div>

          <div>
            <label style={{ fontSize: '13px', fontWeight: 600, display: 'block', marginBottom: '6px' }}>
              Git Repository URL
            </label>
            <input
              type="url"
              placeholder="https://github.com/company/repo"
              value={repoUrl}
              onChange={e => setRepoUrl(e.target.value)}
            />
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
            <div>
              <label style={{ fontSize: '13px', fontWeight: 600, display: 'block', marginBottom: '6px' }}>
                Default Owner Email
              </label>
              <input
                type="email"
                placeholder="developer@company.com"
                value={defaultOwnerEmail}
                onChange={e => setDefaultOwnerEmail(e.target.value)}
              />
            </div>
            <div>
              <label style={{ fontSize: '13px', fontWeight: 600, display: 'block', marginBottom: '6px' }}>
                Development Team
              </label>
              <input
                type="text"
                placeholder="Core Platform"
                value={defaultTeam}
                onChange={e => setDefaultTeam(e.target.value)}
              />
            </div>
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '12px' }}>
            <button type="button" onClick={() => setIsCreateOpen(false)} className="btn btn-secondary">
              Cancel
            </button>
            <button type="submit" disabled={submitting} className="btn btn-primary">
              {submitting ? 'Creating...' : 'Register Project'}
            </button>
          </div>
        </form>
      </Modal>

      {/* Modal: API Key Management */}
      <Modal isOpen={isKeysOpen} onClose={() => setIsKeysOpen(false)} title={`API Keys — ${activeProject?.name}`}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <p style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
            API keys authenticate incoming error telemetry from your applications, Python SDK, or CI/CD pipelines.
          </p>

          {/* Newly created raw key banner */}
          {rawCreatedKey && (
            <div style={{ padding: '14px', borderRadius: '6px', backgroundColor: 'rgba(16, 185, 129, 0.1)', border: '1px solid var(--success)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--success)', fontWeight: 600, fontSize: '14px', marginBottom: '6px' }}>
                <ShieldCheck size={18} /> API Key Generated Successfully!
              </div>
              <p style={{ fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '8px' }}>
                Copy your key now. For security purposes, it will never be displayed again.
              </p>
              <div style={{ display: 'flex', gap: '8px' }}>
                <input
                  type="text"
                  readOnly
                  value={rawCreatedKey}
                  style={{ fontFamily: 'var(--font-mono)', fontSize: '13px', backgroundColor: 'var(--bg-secondary)' }}
                />
                <button
                  type="button"
                  onClick={() => copyToClipboard(rawCreatedKey)}
                  className="btn btn-primary"
                  style={{ whiteSpace: 'nowrap' }}
                >
                  {copied ? <Check size={14} /> : <Copy size={14} />} {copied ? 'Copied' : 'Copy'}
                </button>
              </div>
            </div>
          )}

          {/* Create new key input */}
          <div style={{ display: 'flex', gap: '8px' }}>
            <input
              type="text"
              placeholder="e.g. Production Ingestion Key"
              value={newKeyName}
              onChange={e => setNewKeyName(e.target.value)}
            />
            <button
              onClick={handleGenerateKey}
              disabled={!newKeyName}
              className="btn btn-primary"
              style={{ whiteSpace: 'nowrap' }}
            >
              Generate Key
            </button>
          </div>

          {/* Keys list */}
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>Key Name</th>
                  <th>Prefix</th>
                  <th>Created</th>
                  <th>Status</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {apiKeys.map(k => (
                  <tr key={k.id}>
                    <td><strong>{k.name}</strong></td>
                    <td><code>{k.prefix}</code></td>
                    <td style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                      {new Date(k.created_at).toLocaleDateString()}
                    </td>
                    <td>
                      <span
                        className="badge"
                        style={{
                          backgroundColor: k.is_active ? 'var(--success-bg)' : 'var(--critical-bg)',
                          color: k.is_active ? 'var(--success)' : 'var(--critical)',
                        }}
                      >
                        {k.is_active ? 'Active' : 'Revoked'}
                      </span>
                    </td>
                    <td>
                      {k.is_active && (
                        <button
                          onClick={() => handleRevokeKey(k.id)}
                          className="btn btn-danger"
                          style={{ padding: '4px 8px', fontSize: '11px' }}
                        >
                          <Trash2 size={12} /> Revoke
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </Modal>
    </div>
  );
};
