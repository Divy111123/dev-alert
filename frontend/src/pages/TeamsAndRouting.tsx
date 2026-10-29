import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { Project, RoutingRule, OrgMember } from '../types';
import { Modal } from '../components/Modal';
import { Plus, Trash2, Play, Users, GitFork, CheckCircle, Shield } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export const TeamsAndRouting: React.FC = () => {
  const { currentOrg } = useAuth();
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<string>('');
  const [rules, setRules] = useState<RoutingRule[]>([]);
  const [members, setMembers] = useState<OrgMember[]>([]);
  const [loading, setLoading] = useState(true);

  // Create rule modal
  const [isRuleModalOpen, setIsRuleModalOpen] = useState(false);
  const [ruleName, setRuleName] = useState('');
  const [priority, setPriority] = useState(1);
  const [condService, setCondService] = useState('');
  const [condEnv, setCondEnv] = useState('');
  const [condErrorType, setCondErrorType] = useState('');
  const [condPhase, setCondPhase] = useState('');
  const [condSeverity, setCondSeverity] = useState('');
  const [targetType, setTargetType] = useState<'email' | 'team'>('email');
  const [targetVal, setTargetVal] = useState('');

  // Add member modal
  const [isMemberModalOpen, setIsMemberModalOpen] = useState(false);
  const [memberEmail, setMemberEmail] = useState('');
  const [memberRole, setMemberRole] = useState('developer');

  // Interactive Routing Rule Simulator
  const [testEnv, setTestEnv] = useState('production');
  const [testService, setTestService] = useState('payment-api');
  const [testErrorType, setTestErrorType] = useState('DatabaseConnectionError');
  const [testPhase, setTestPhase] = useState('deployment');
  const [testSeverity, setTestSeverity] = useState('high');
  const [simResult, setSimResult] = useState<any | null>(null);
  const [simulating, setSimulating] = useState(false);

  useEffect(() => {
    loadProjectsAndMembers();
  }, [currentOrg]);

  useEffect(() => {
    if (selectedProjectId) {
      loadRules(selectedProjectId);
    }
  }, [selectedProjectId]);

  const loadProjectsAndMembers = async () => {
    try {
      setLoading(true);
      const projs = await api.getProjects();
      setProjects(projs);
      if (projs.length > 0) {
        setSelectedProjectId(projs[0].id);
      }

      if (currentOrg) {
        const mems = await api.getOrgMembers(currentOrg.id);
        setMembers(mems);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const loadRules = async (projId: string) => {
    try {
      const r = await api.getRoutingRules(projId);
      setRules(r);
    } catch (err) {
      console.error(err);
    }
  };

  const handleCreateRule = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedProjectId) return;
    try {
      const conditions: Record<string, string> = {};
      if (condService) conditions.service = condService;
      if (condEnv) conditions.environment = condEnv;
      if (condErrorType) conditions.error_type = condErrorType;
      if (condPhase) conditions.phase = condPhase;
      if (condSeverity) conditions.severity = condSeverity;

      await api.createRoutingRule(selectedProjectId, {
        name: ruleName,
        priority: Number(priority),
        conditions,
        target_type: targetType,
        target_email: targetType === 'email' ? targetVal : undefined,
        target_team: targetType === 'team' ? targetVal : undefined,
      });

      setIsRuleModalOpen(false);
      setRuleName('');
      setCondService('');
      setCondEnv('');
      setCondErrorType('');
      setCondPhase('');
      setCondSeverity('');
      setTargetVal('');
      loadRules(selectedProjectId);
    } catch (err) {
      alert('Failed to create routing rule');
    }
  };

  const handleDeleteRule = async (ruleId: number) => {
    if (!confirm('Delete this routing rule?')) return;
    try {
      await api.deleteRoutingRule(selectedProjectId, ruleId);
      loadRules(selectedProjectId);
    } catch (err) {
      alert('Failed to delete rule');
    }
  };

  const handleAddMember = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!currentOrg) return;
    try {
      await api.addOrgMember(currentOrg.id, { email: memberEmail, role: memberRole });
      setIsMemberModalOpen(false);
      setMemberEmail('');
      const mems = await api.getOrgMembers(currentOrg.id);
      setMembers(mems);
    } catch (err: any) {
      alert(err.message || 'Failed to add member');
    }
  };

  const handleSimulateRouting = async () => {
    if (!selectedProjectId) return;
    try {
      setSimulating(true);
      const res = await api.testRouting(selectedProjectId, {
        environment: testEnv,
        service: testService,
        error_type: testErrorType,
        phase: testPhase,
        severity: testSeverity,
      });
      setSimResult(res);
    } catch (err) {
      alert('Simulation failed');
    } finally {
      setSimulating(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 style={{ fontSize: '24px', fontWeight: 700 }}>Developer Routing & Team Ownership</h1>
          <p style={{ color: 'var(--text-muted)', fontSize: '14px', marginTop: '4px' }}>
            Configure granular ownership rules across components, environments, error categories, and CI/CD stages.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '8px' }}>
          <button onClick={() => setIsMemberModalOpen(true)} className="btn btn-secondary">
            <Users size={16} /> Add Team Member
          </button>
          <button onClick={() => setIsRuleModalOpen(true)} className="btn btn-primary" disabled={!selectedProjectId}>
            <Plus size={16} /> New Routing Rule
          </button>
        </div>
      </div>

      {/* Project Selector */}
      <div className="card" style={{ display: 'flex', alignItems: 'center', gap: '16px', padding: '14px 20px' }}>
        <span style={{ fontSize: '14px', fontWeight: 600 }}>Active Project:</span>
        <select
          value={selectedProjectId}
          onChange={e => setSelectedProjectId(e.target.value)}
          style={{ maxWidth: '320px' }}
        >
          {projects.map(p => (
            <option key={p.id} value={p.id}>{p.name} ({p.id.slice(0, 8)}...)</option>
          ))}
        </select>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1.8fr 1.2fr', gap: '24px' }}>
        {/* Left Column: Routing Rules List */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div className="card">
            <h3 style={{ fontSize: '16px', fontWeight: 600, marginBottom: '6px' }}>Configured Ownership Rules</h3>
            <p style={{ fontSize: '13px', color: 'var(--text-muted)', marginBottom: '16px' }}>
              Evaluated strictly in priority order (Priority 1 = highest). If multiple match, the highest priority rule wins.
            </p>

            <div className="table-container">
              <table>
                <thead>
                  <tr>
                    <th>Priority</th>
                    <th>Rule Name</th>
                    <th>Matching Conditions</th>
                    <th>Target Owner</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {rules.map(rule => (
                    <tr key={rule.id}>
                      <td><span className="badge" style={{ backgroundColor: 'var(--accent-subtle)', color: 'var(--accent)' }}>#{rule.priority}</span></td>
                      <td><strong>{rule.name}</strong></td>
                      <td>
                        <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap' }}>
                          {Object.entries(rule.conditions || {}).map(([k, v]) => (
                            <span key={k} style={{ fontSize: '11px', padding: '2px 6px', borderRadius: '4px', backgroundColor: 'var(--bg-surface)', border: '1px solid var(--border-subtle)' }}>
                              {k}: <strong>{String(v)}</strong>
                            </span>
                          ))}
                        </div>
                      </td>
                      <td>
                        <span style={{ fontSize: '13px', color: 'var(--text-primary)', fontWeight: 500 }}>
                          {rule.target_email || rule.target_team}
                        </span>
                      </td>
                      <td>
                        <button
                          onClick={() => handleDeleteRule(rule.id)}
                          className="btn btn-secondary"
                          style={{ padding: '4px 8px', color: 'var(--critical)' }}
                        >
                          <Trash2 size={13} />
                        </button>
                      </td>
                    </tr>
                  ))}
                  {rules.length === 0 && (
                    <tr>
                      <td colSpan={5} style={{ padding: '24px', textAlign: 'center', color: 'var(--text-muted)' }}>
                        No custom rules configured. Errors will route to project default owner/team fallback.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>

          {/* Team Members List */}
          <div className="card">
            <h3 style={{ fontSize: '16px', fontWeight: 600, marginBottom: '14px' }}>Organization Members & Roles</h3>
            <div className="table-container">
              <table>
                <thead>
                  <tr>
                    <th>Member Email</th>
                    <th>Role</th>
                    <th>Joined</th>
                  </tr>
                </thead>
                <tbody>
                  {members.map(m => (
                    <tr key={m.id}>
                      <td>{m.user?.email || 'Member'}</td>
                      <td>
                        <span className="badge" style={{ backgroundColor: 'var(--accent-subtle)', color: 'var(--accent)' }}>
                          {m.role}
                        </span>
                      </td>
                      <td style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                        {new Date(m.created_at).toLocaleDateString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Right Column: Live Interactive Routing Engine Simulator */}
        <div className="card" style={{ height: 'fit-content', border: '1px solid var(--border-focus)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
            <Play size={18} color="var(--accent)" />
            <h3 style={{ fontSize: '16px', fontWeight: 600 }}>Interactive Routing Simulator</h3>
          </div>
          <p style={{ fontSize: '13px', color: 'var(--text-muted)', marginBottom: '16px' }}>
            Test hypothetical error attributes against your active rules to inspect who would be alerted and why.
          </p>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <div>
              <label style={{ fontSize: '12px', fontWeight: 600, display: 'block', marginBottom: '4px' }}>Component / Service</label>
              <input type="text" value={testService} onChange={e => setTestService(e.target.value)} />
            </div>

            <div>
              <label style={{ fontSize: '12px', fontWeight: 600, display: 'block', marginBottom: '4px' }}>Error Type</label>
              <input type="text" value={testErrorType} onChange={e => setTestErrorType(e.target.value)} />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
              <div>
                <label style={{ fontSize: '12px', fontWeight: 600, display: 'block', marginBottom: '4px' }}>Environment</label>
                <select value={testEnv} onChange={e => setTestEnv(e.target.value)}>
                  <option value="production">Production</option>
                  <option value="staging">Staging</option>
                  <option value="testing">Testing</option>
                  <option value="development">Development</option>
                </select>
              </div>

              <div>
                <label style={{ fontSize: '12px', fontWeight: 600, display: 'block', marginBottom: '4px' }}>Phase</label>
                <select value={testPhase} onChange={e => setTestPhase(e.target.value)}>
                  <option value="deployment">Deployment</option>
                  <option value="build">Build</option>
                  <option value="testing">Testing</option>
                  <option value="production">Production</option>
                </select>
              </div>
            </div>

            <div>
              <label style={{ fontSize: '12px', fontWeight: 600, display: 'block', marginBottom: '4px' }}>Severity</label>
              <select value={testSeverity} onChange={e => setTestSeverity(e.target.value)}>
                <option value="critical">Critical</option>
                <option value="high">High</option>
                <option value="medium">Medium</option>
                <option value="low">Low</option>
              </select>
            </div>

            <button onClick={handleSimulateRouting} disabled={simulating} className="btn btn-primary" style={{ marginTop: '8px' }}>
              {simulating ? 'Evaluating...' : 'Test Routing Engine'}
            </button>
          </div>

          {/* Simulator Result Output */}
          {simResult && (
            <div style={{ marginTop: '16px', padding: '14px', borderRadius: '6px', backgroundColor: 'var(--bg-surface)', border: '1px solid var(--border-subtle)' }}>
              <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: '4px' }}>Selected Target:</div>
              <div style={{ fontSize: '15px', fontWeight: 700, color: 'var(--accent)' }}>
                {simResult.target} ({simResult.target_type})
              </div>
              <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '6px' }}>
                <strong>Reason:</strong> {simResult.reason}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Modal: New Routing Rule */}
      <Modal isOpen={isRuleModalOpen} onClose={() => setIsRuleModalOpen(false)} title="Create Ownership Routing Rule">
        <form onSubmit={handleCreateRule} style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          <div>
            <label style={{ fontSize: '13px', fontWeight: 600, display: 'block', marginBottom: '4px' }}>Rule Name *</label>
            <input type="text" required placeholder="e.g. Auth Microservice Team" value={ruleName} onChange={e => setRuleName(e.target.value)} />
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
            <div>
              <label style={{ fontSize: '13px', fontWeight: 600, display: 'block', marginBottom: '4px' }}>Priority (1 = Highest)</label>
              <input type="number" min={1} max={100} value={priority} onChange={e => setPriority(Number(e.target.value))} />
            </div>

            <div>
              <label style={{ fontSize: '13px', fontWeight: 600, display: 'block', marginBottom: '4px' }}>Component / Service</label>
              <input type="text" placeholder="e.g. payment-api" value={condService} onChange={e => setCondService(e.target.value)} />
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
            <div>
              <label style={{ fontSize: '13px', fontWeight: 600, display: 'block', marginBottom: '4px' }}>Environment</label>
              <select value={condEnv} onChange={e => setCondEnv(e.target.value)}>
                <option value="">Any (*)</option>
                <option value="production">Production</option>
                <option value="staging">Staging</option>
                <option value="testing">Testing</option>
                <option value="development">Development</option>
              </select>
            </div>

            <div>
              <label style={{ fontSize: '13px', fontWeight: 600, display: 'block', marginBottom: '4px' }}>Phase</label>
              <select value={condPhase} onChange={e => setCondPhase(e.target.value)}>
                <option value="">Any (*)</option>
                <option value="Deployment">Deployment</option>
                <option value="Build">Build</option>
                <option value="Testing">Testing</option>
                <option value="Production">Production</option>
              </select>
            </div>
          </div>

          <div>
            <label style={{ fontSize: '13px', fontWeight: 600, display: 'block', marginBottom: '4px' }}>Error Category / Error Type Match</label>
            <input type="text" placeholder="e.g. DatabaseConnectionError or SyntaxError" value={condErrorType} onChange={e => setCondErrorType(e.target.value)} />
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '140px 1fr', gap: '10px' }}>
            <div>
              <label style={{ fontSize: '13px', fontWeight: 600, display: 'block', marginBottom: '4px' }}>Target Type</label>
              <select value={targetType} onChange={e => setTargetType(e.target.value as any)}>
                <option value="email">Developer Email</option>
                <option value="team">Team Name</option>
              </select>
            </div>

            <div>
              <label style={{ fontSize: '13px', fontWeight: 600, display: 'block', marginBottom: '4px' }}>Destination Email or Team *</label>
              <input type="text" required placeholder={targetType === 'email' ? 'alice@company.com' : 'Billing Squad'} value={targetVal} onChange={e => setTargetVal(e.target.value)} />
            </div>
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '10px' }}>
            <button type="button" onClick={() => setIsRuleModalOpen(false)} className="btn btn-secondary">Cancel</button>
            <button type="submit" className="btn btn-primary">Save Routing Rule</button>
          </div>
        </form>
      </Modal>

      {/* Modal: Add Member */}
      <Modal isOpen={isMemberModalOpen} onClose={() => setIsMemberModalOpen(false)} title="Invite Team Member">
        <form onSubmit={handleAddMember} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          <div>
            <label style={{ fontSize: '13px', fontWeight: 600, display: 'block', marginBottom: '4px' }}>Member Email Address *</label>
            <input type="email" required placeholder="developer@company.com" value={memberEmail} onChange={e => setMemberEmail(e.target.value)} />
          </div>

          <div>
            <label style={{ fontSize: '13px', fontWeight: 600, display: 'block', marginBottom: '4px' }}>Role</label>
            <select value={memberRole} onChange={e => setMemberRole(e.target.value)}>
              <option value="developer">Developer (View, Investigate, Resolve)</option>
              <option value="project_manager">Project Manager (Manage Projects & Rules)</option>
              <option value="admin">Organization Admin (Full Administrative Control)</option>
              <option value="viewer">Read-Only Viewer</option>
            </select>
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '10px' }}>
            <button type="button" onClick={() => setIsMemberModalOpen(false)} className="btn btn-secondary">Cancel</button>
            <button type="submit" className="btn btn-primary">Add Member</button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
