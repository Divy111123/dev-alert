const getAuthHeaders = () => {
  const token = localStorage.getItem('devalert_token');
  const orgId = localStorage.getItem('devalert_org_id');
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  if (token) headers['Authorization'] = `Bearer ${token}`;
  if (orgId) headers['X-Organization-Id'] = orgId;
  return headers;
};

export const api = {
  // Auth
  login: async (credentials: any) => {
    const res = await fetch('/api/v1/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(credentials),
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Login failed');
    }
    return res.json();
  },

  register: async (userData: any) => {
    const res = await fetch('/api/v1/auth/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(userData),
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Registration failed');
    }
    return res.json();
  },

  // Analytics
  getOverview: async () => {
    const res = await fetch('/api/v1/analytics/overview', {
      headers: getAuthHeaders(),
    });
    if (!res.ok) throw new Error('Failed to fetch analytics');
    return res.json();
  },

  // Incidents
  getIncidents: async (filters: Record<string, string> = {}) => {
    const query = new URLSearchParams(filters).toString();
    const res = await fetch(`/api/v1/incidents?${query}`, {
      headers: getAuthHeaders(),
    });
    if (!res.ok) throw new Error('Failed to fetch incidents');
    return res.json();
  },

  getIncident: async (id: string) => {
    const res = await fetch(`/api/v1/incidents/${id}`, {
      headers: getAuthHeaders(),
    });
    if (!res.ok) throw new Error('Failed to fetch incident details');
    return res.json();
  },

  updateIncident: async (id: string, updateData: any) => {
    const res = await fetch(`/api/v1/incidents/${id}`, {
      method: 'PATCH',
      headers: getAuthHeaders(),
      body: JSON.stringify(updateData),
    });
    if (!res.ok) throw new Error('Failed to update incident');
    return res.json();
  },

  analyzeIncidentAI: async (id: string) => {
    const res = await fetch(`/api/v1/incidents/${id}/ai-analyze`, {
      method: 'POST',
      headers: getAuthHeaders(),
    });
    if (!res.ok) throw new Error('Failed to run AI analysis');
    return res.json();
  },

  // Projects
  getProjects: async () => {
    const res = await fetch('/api/v1/projects', {
      headers: getAuthHeaders(),
    });
    if (!res.ok) throw new Error('Failed to fetch projects');
    return res.json();
  },

  createProject: async (projectData: any) => {
    const res = await fetch('/api/v1/projects', {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(projectData),
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Failed to create project');
    }
    return res.json();
  },

  updateProject: async (id: string, projectData: any) => {
    const res = await fetch(`/api/v1/projects/${id}`, {
      method: 'PUT',
      headers: getAuthHeaders(),
      body: JSON.stringify(projectData),
    });
    if (!res.ok) throw new Error('Failed to update project');
    return res.json();
  },

  deleteProject: async (id: string) => {
    const res = await fetch(`/api/v1/projects/${id}`, {
      method: 'DELETE',
      headers: getAuthHeaders(),
    });
    if (!res.ok) throw new Error('Failed to delete project');
    return true;
  },

  // API Keys
  getApiKeys: async (projectId: string) => {
    const res = await fetch(`/api/v1/projects/${projectId}/api-keys`, {
      headers: getAuthHeaders(),
    });
    if (!res.ok) throw new Error('Failed to fetch API keys');
    return res.json();
  },

  createApiKey: async (projectId: string, name: string) => {
    const res = await fetch(`/api/v1/projects/${projectId}/api-keys`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({ name }),
    });
    if (!res.ok) throw new Error('Failed to create API key');
    return res.json();
  },

  revokeApiKey: async (projectId: string, keyId: number) => {
    const res = await fetch(`/api/v1/projects/${projectId}/api-keys/${keyId}`, {
      method: 'DELETE',
      headers: getAuthHeaders(),
    });
    if (!res.ok) throw new Error('Failed to revoke API key');
    return true;
  },

  testEmailNotification: async (projectId: string, targetEmail?: string) => {
    const url = targetEmail 
      ? `/api/v1/projects/${projectId}/test-email?target_email=${encodeURIComponent(targetEmail)}`
      : `/api/v1/projects/${projectId}/test-email`;
    const res = await fetch(url, {
      method: 'POST',
      headers: getAuthHeaders(),
    });
    if (!res.ok) throw new Error('Failed to dispatch test email');
    return res.json();
  },

  // Routing Rules
  getRoutingRules: async (projectId: string) => {
    const res = await fetch(`/api/v1/routing/projects/${projectId}/rules`, {
      headers: getAuthHeaders(),
    });
    if (!res.ok) throw new Error('Failed to fetch routing rules');
    return res.json();
  },

  createRoutingRule: async (projectId: string, ruleData: any) => {
    const res = await fetch(`/api/v1/routing/projects/${projectId}/rules`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(ruleData),
    });
    if (!res.ok) throw new Error('Failed to create routing rule');
    return res.json();
  },

  deleteRoutingRule: async (projectId: string, ruleId: number) => {
    const res = await fetch(`/api/v1/routing/projects/${projectId}/rules/${ruleId}`, {
      method: 'DELETE',
      headers: getAuthHeaders(),
    });
    if (!res.ok) throw new Error('Failed to delete routing rule');
    return true;
  },

  testRouting: async (projectId: string, testData: any) => {
    const res = await fetch(`/api/v1/routing/projects/${projectId}/test`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(testData),
    });
    if (!res.ok) throw new Error('Routing evaluation failed');
    return res.json();
  },

  // Organizations & Members
  getOrgMembers: async (orgId: number) => {
    const res = await fetch(`/api/v1/organizations/${orgId}/members`, {
      headers: getAuthHeaders(),
    });
    if (!res.ok) throw new Error('Failed to fetch members');
    return res.json();
  },

  addOrgMember: async (orgId: number, memberData: any) => {
    const res = await fetch(`/api/v1/organizations/${orgId}/members`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(memberData),
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Failed to add member');
    }
    return res.json();
  },

  // Audit Logs
  getAuditLogs: async () => {
    const res = await fetch('/api/v1/audit', {
      headers: getAuthHeaders(),
    });
    if (!res.ok) throw new Error('Failed to fetch audit logs');
    return res.json();
  },
};
