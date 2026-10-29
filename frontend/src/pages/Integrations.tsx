import React, { useState } from 'react';
import { Copy, Check, Terminal, Cpu, GitBranch, Webhook } from 'lucide-react';

export const Integrations: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'python' | 'jenkins' | 'github' | 'webhook'>('python');
  const [copiedSection, setCopiedSection] = useState<string | null>(null);

  const copyCode = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedSection(id);
    setTimeout(() => setCopiedSection(null), 2000);
  };

  const pythonSnippet = `import devalert
from devalert.integrations.fastapi import DevAlertFastAPIMiddleware
from fastapi import FastAPI

# 1. Initialize the DevAlert client at application startup
devalert.init(
    api_key="da_live_YOUR_PROJECT_API_KEY",
    endpoint="http://localhost:8000/api/v1/events",
    environment="production",
    service="payment-checkout-api",
    release="v1.2.0"
)

app = FastAPI()
# 2. Add the DevAlert middleware to catch all unhandled exceptions
app.add_middleware(DevAlertFastAPIMiddleware, service_name="payment-checkout-api")

# 3. Explicit exception capture example:
try:
    execute_transaction()
except Exception as e:
    devalert.capture_exception(
        exc=e,
        severity="high",
        metadata={"order_id": "ord_9921", "customer_tier": "enterprise"}
    )`;

  const jenkinsSnippet = `// In your Jenkinsfile post-failure stage:
post {
    failure {
        script {
            def failedStage = env.STAGE_NAME ?: "Build"
            def payload = """{
                "job_name": "\${env.JOB_NAME}",
                "build_number": "\${env.BUILD_NUMBER}",
                "stage": "\${failedStage}",
                "branch": "\${env.BRANCH_NAME ?: 'main'}",
                "commit_sha": "\${env.GIT_COMMIT ?: ''}",
                "build_url": "\${env.BUILD_URL}",
                "repository": "\${env.GIT_URL ?: ''}",
                "environment": "testing",
                "severity": "high",
                "error_message": "Jenkins pipeline failure in stage '\${failedStage}'"
            }"""

            httpRequest(
                url: 'http://devalert-backend:8000/api/v1/webhooks/jenkins',
                httpMode: 'POST',
                contentType: 'APPLICATION_JSON',
                customHeaders: [[name: 'X-API-Key', value: "\${DEVALERT_API_KEY}"]],
                requestBody: payload
            )
        }
    }
}`;

  const githubSnippet = `- name: Notify DevAlert on Failure
  if: failure()
  run: |
    curl -X POST "http://devalert-backend:8000/api/v1/webhooks/github" \\
      -H "X-API-Key: \${{ secrets.DEVALERT_PROJECT_API_KEY }}" \\
      -H "Content-Type: application/json" \\
      -d '{
        "workflow": "\${{ github.workflow }}",
        "run_id": "\${{ github.run_id }}",
        "job": "unit-tests",
        "failed_step": "\${{ steps.test.outcome == '\''failure'\'' && '\''Unit Tests'\'' || '\''Docker Build'\'' }}",
        "repository": "\${{ github.repository }}",
        "branch": "\${{ github.ref_name }}",
        "commit_sha": "\${{ github.sha }}",
        "message": "GitHub Actions automated build failed on branch \${{ github.ref_name }}",
        "severity": "high",
        "environment": "testing"
      }'`;

  const webhookSnippet = `curl -X POST "http://localhost:8000/api/v1/webhooks/generic" \\
  -H "X-API-Key: da_live_YOUR_PROJECT_API_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{
    "event_type": "KubernetesPodCrashLoop",
    "summary": "Container payment-worker exited with code 137 (OOMKilled)",
    "component": "k8s-cluster-prod",
    "environment": "production",
    "phase": "Production",
    "severity": "critical",
    "trace": "Memory cgroup out of memory: Killed process 8192 (python)",
    "metadata": {
      "node": "k8s-worker-04",
      "namespace": "billing"
    }
  }'`;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      <div>
        <h1 style={{ fontSize: '24px', fontWeight: 700 }}>Integrations & SDK Setup</h1>
        <p style={{ color: 'var(--text-muted)', fontSize: '14px', marginTop: '4px' }}>
          Connect applications, CI/CD pipelines, and monitoring systems to DevAlert with zero application rewrites.
        </p>
      </div>

      {/* Integration selector tabs */}
      <div style={{ display: 'flex', gap: '10px' }}>
        <button
          onClick={() => setActiveTab('python')}
          className={`btn ${activeTab === 'python' ? 'btn-primary' : 'btn-secondary'}`}
        >
          <Terminal size={16} /> Python SDK (FastAPI / Flask)
        </button>
        <button
          onClick={() => setActiveTab('jenkins')}
          className={`btn ${activeTab === 'jenkins' ? 'btn-primary' : 'btn-secondary'}`}
        >
          <Cpu size={16} /> Jenkins Pipeline
        </button>
        <button
          onClick={() => setActiveTab('github')}
          className={`btn ${activeTab === 'github' ? 'btn-primary' : 'btn-secondary'}`}
        >
          <GitBranch size={16} /> GitHub Actions
        </button>
        <button
          onClick={() => setActiveTab('webhook')}
          className={`btn ${activeTab === 'webhook' ? 'btn-primary' : 'btn-secondary'}`}
        >
          <Webhook size={16} /> Generic Webhook
        </button>
      </div>

      {/* Tab 1: Python SDK */}
      {activeTab === 'python' && (
        <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div>
            <h2 style={{ fontSize: '18px', fontWeight: 600 }}>Python SDK (`devalert-python`)</h2>
            <p style={{ fontSize: '14px', color: 'var(--text-secondary)', marginTop: '4px' }}>
              The lightweight, non-blocking Python SDK automatically captures uncaught exceptions, redacts sensitive secrets, tags environments and releases, and transmits errors in a background worker.
            </p>
          </div>

          <div>
            <h4 style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '6px' }}>Installation</h4>
            <div style={{ position: 'relative' }}>
              <pre className="code-snippet">pip install ./sdk/python</pre>
              <button
                onClick={() => copyCode('pip install ./sdk/python', 'pip')}
                className="btn btn-secondary"
                style={{ position: 'absolute', right: '8px', top: '8px', padding: '4px 8px', fontSize: '11px' }}
              >
                {copiedSection === 'pip' ? <Check size={12} /> : <Copy size={12} />}
              </button>
            </div>
          </div>

          <div>
            <h4 style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '6px' }}>Application Example (FastAPI)</h4>
            <div style={{ position: 'relative' }}>
              <pre className="code-snippet">{pythonSnippet}</pre>
              <button
                onClick={() => copyCode(pythonSnippet, 'pycode')}
                className="btn btn-secondary"
                style={{ position: 'absolute', right: '8px', top: '8px', padding: '4px 8px', fontSize: '11px' }}
              >
                {copiedSection === 'pycode' ? <Check size={12} /> : <Copy size={12} />}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Tab 2: Jenkins */}
      {activeTab === 'jenkins' && (
        <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div>
            <h2 style={{ fontSize: '18px', fontWeight: 600 }}>Jenkins Pipeline Webhook</h2>
            <p style={{ fontSize: '14px', color: 'var(--text-secondary)', marginTop: '4px' }}>
              Route Jenkins build, test, and container packaging failures automatically to the DevOps or stage owner with sanitized console log excerpts.
            </p>
          </div>

          <div style={{ position: 'relative' }}>
            <pre className="code-snippet">{jenkinsSnippet}</pre>
            <button
              onClick={() => copyCode(jenkinsSnippet, 'jenkins')}
              className="btn btn-secondary"
              style={{ position: 'absolute', right: '8px', top: '8px', padding: '4px 8px', fontSize: '11px' }}
            >
              {copiedSection === 'jenkins' ? <Check size={12} /> : <Copy size={12} />}
            </button>
          </div>
        </div>
      )}

      {/* Tab 3: GitHub Actions */}
      {activeTab === 'github' && (
        <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div>
            <h2 style={{ fontSize: '18px', fontWeight: 600 }}>GitHub Actions CI Integration</h2>
            <p style={{ fontSize: '14px', color: 'var(--text-secondary)', marginTop: '4px' }}>
              Report automated test failures and CI workflow breaks directly into DevAlert.
            </p>
          </div>

          <div style={{ position: 'relative' }}>
            <pre className="code-snippet">{githubSnippet}</pre>
            <button
              onClick={() => copyCode(githubSnippet, 'github')}
              className="btn btn-secondary"
              style={{ position: 'absolute', right: '8px', top: '8px', padding: '4px 8px', fontSize: '11px' }}
            >
              {copiedSection === 'github' ? <Check size={12} /> : <Copy size={12} />}
            </button>
          </div>
        </div>
      )}

      {/* Tab 4: Generic Webhook */}
      {activeTab === 'webhook' && (
        <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div>
            <h2 style={{ fontSize: '18px', fontWeight: 600 }}>Generic Alert Webhook Contract</h2>
            <p style={{ fontSize: '14px', color: 'var(--text-secondary)', marginTop: '4px' }}>
              Send custom error alerts from any infrastructure, script, or cloud provider.
            </p>
          </div>

          <div style={{ position: 'relative' }}>
            <pre className="code-snippet">{webhookSnippet}</pre>
            <button
              onClick={() => copyCode(webhookSnippet, 'webhook')}
              className="btn btn-secondary"
              style={{ position: 'absolute', right: '8px', top: '8px', padding: '4px 8px', fontSize: '11px' }}
            >
              {copiedSection === 'webhook' ? <Check size={12} /> : <Copy size={12} />}
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
