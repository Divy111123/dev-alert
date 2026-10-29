import React, { useState } from 'react';
import { Save, Bell, Shield, Mail, Bot, Sliders } from 'lucide-react';

export const Settings: React.FC = () => {
  const [cooldown, setCooldown] = useState('15');
  const [notifyOnNew, setNotifyOnNew] = useState(true);
  const [notifyOnEscalation, setNotifyOnEscalation] = useState(true);
  const [minSeverity, setMinSeverity] = useState('medium');
  const [aiEnabled, setAiEnabled] = useState(true);
  const [rateLimit, setRateLimit] = useState('120');
  const [saved, setSaved] = useState(false);

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    setSaved(true);
    setTimeout(() => setSaved(false), 2500);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px', maxWidth: '800px' }}>
      <div>
        <h1 style={{ fontSize: '24px', fontWeight: 700 }}>Platform Settings</h1>
        <p style={{ color: 'var(--text-muted)', fontSize: '14px', marginTop: '4px' }}>
          Configure global notification policies, rate limiting, and automated triage rules.
        </p>
      </div>

      <form onSubmit={handleSave} style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
        {/* Notification Policy */}
        <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '10px' }}>
            <Bell size={18} color="var(--accent)" />
            <h3 style={{ fontSize: '16px', fontWeight: 600 }}>Notification & Suppression Rules</h3>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
            <div>
              <label style={{ fontSize: '13px', fontWeight: 600, display: 'block', marginBottom: '6px' }}>
                Notification Cooldown (Minutes)
              </label>
              <input
                type="number"
                min="1"
                max="1440"
                value={cooldown}
                onChange={e => setCooldown(e.target.value)}
              />
              <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                Prevents alert storms by suppressing repeated notifications for duplicate incidents.
              </span>
            </div>

            <div>
              <label style={{ fontSize: '13px', fontWeight: 600, display: 'block', marginBottom: '6px' }}>
                Minimum Severity to Notify
              </label>
              <select value={minSeverity} onChange={e => setMinSeverity(e.target.value)}>
                <option value="low">Low (All Events)</option>
                <option value="medium">Medium and Above</option>
                <option value="high">High and Critical Only</option>
                <option value="critical">Critical Only</option>
              </select>
            </div>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', marginTop: '6px' }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: '10px', fontSize: '13px', cursor: 'pointer' }}>
              <input
                type="checkbox"
                checked={notifyOnNew}
                onChange={e => setNotifyOnNew(e.target.checked)}
                style={{ width: 'auto' }}
              />
              <span>Send instant email when a new incident fingerprint is first detected</span>
            </label>

            <label style={{ display: 'flex', alignItems: 'center', gap: '10px', fontSize: '13px', cursor: 'pointer' }}>
              <input
                type="checkbox"
                checked={notifyOnEscalation}
                onChange={e => setNotifyOnEscalation(e.target.checked)}
                style={{ width: 'auto' }}
              />
              <span>Send email alert on severity escalation (e.g. Medium escalated to Critical)</span>
            </label>
          </div>
        </div>

        {/* AI Analysis Settings */}
        <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '10px' }}>
            <Bot size={18} color="#818cf8" />
            <h3 style={{ fontSize: '16px', fontWeight: 600 }}>AI-Assisted Error Diagnosis</h3>
          </div>

          <label style={{ display: 'flex', alignItems: 'center', gap: '10px', fontSize: '13px', cursor: 'pointer' }}>
            <input
              type="checkbox"
              checked={aiEnabled}
              onChange={e => setAiEnabled(e.target.checked)}
              style={{ width: 'auto' }}
            />
            <span>Enable AI error analysis for suggested troubleshooting and root causes</span>
          </label>
          <p style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
            All stack traces, messages, and payloads are strictly scrubbed of API keys, passwords, and tokens before evaluation.
          </p>
        </div>

        {/* Rate Limiting & Security */}
        <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '10px' }}>
            <Shield size={18} color="var(--accent)" />
            <h3 style={{ fontSize: '16px', fontWeight: 600 }}>Security & Ingestion Safeguards</h3>
          </div>

          <div style={{ maxWidth: '320px' }}>
            <label style={{ fontSize: '13px', fontWeight: 600, display: 'block', marginBottom: '6px' }}>
              Rate Limit (Events per minute per project)
            </label>
            <input
              type="number"
              value={rateLimit}
              onChange={e => setRateLimit(e.target.value)}
            />
          </div>
        </div>

        <div style={{ display: 'flex', justifyContent: 'flex-start', alignItems: 'center', gap: '12px' }}>
          <button type="submit" className="btn btn-primary" style={{ padding: '10px 24px' }}>
            <Save size={16} /> Save Configuration
          </button>
          {saved && <span style={{ color: 'var(--success)', fontSize: '13px', fontWeight: 600 }}>Settings saved successfully!</span>}
        </div>
      </form>
    </div>
  );
};
