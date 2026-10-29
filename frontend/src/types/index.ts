export type Severity = 'low' | 'medium' | 'high' | 'critical';
export type IncidentStatus = 'open' | 'acknowledged' | 'investigating' | 'resolved' | 'reopened';
export type DevelopmentPhase = 'Development' | 'Testing' | 'Staging' | 'Build' | 'Deployment' | 'Production' | 'Unknown';

export interface User {
  id: number;
  email: string;
  full_name?: string;
  is_active: boolean;
  is_superuser: boolean;
  created_at: string;
}

export interface Organization {
  id: number;
  name: string;
  slug: string;
  description?: string;
  created_at: string;
  members_count: number;
  projects_count: number;
}

export interface OrgMember {
  id: number;
  user_id: number;
  organization_id: number;
  role: 'admin' | 'project_manager' | 'developer' | 'viewer';
  created_at: string;
  user?: User;
}

export interface Project {
  id: string;
  organization_id: number;
  name: string;
  slug: string;
  description?: string;
  repository_url?: string;
  default_owner_id?: number;
  default_owner_email?: string;
  default_team?: string;
  environments: string[];
  integration_secret?: string;
  settings: {
    cooldown_minutes: number;
    notify_on_new: boolean;
    notify_on_escalation: boolean;
    notify_on_resolve: boolean;
    min_severity_to_notify: string;
    rate_limit_per_minute: number;
  };
  created_at: string;
  updated_at: string;
  open_incidents_count: number;
  total_events_count: number;
}

export interface ApiKey {
  id: number;
  name: string;
  prefix: string;
  is_active: boolean;
  created_at: string;
  revoked_at?: string;
  last_used_at?: string;
  raw_key?: string;
}

export interface RoutingRule {
  id: number;
  project_id: string;
  name: string;
  description?: string;
  priority: number;
  is_active: boolean;
  conditions: Record<string, any>;
  target_type: 'user' | 'team' | 'email';
  target_user_id?: number;
  target_team?: string;
  target_email?: string;
  created_at: string;
}

export interface ErrorEvent {
  id: string;
  incident_id: string;
  project_id: string;
  event_id?: string;
  environment: string;
  phase: string;
  service: string;
  source: string;
  error_type: string;
  message: string;
  severity: Severity;
  timestamp: string;
  sanitized_stack_trace?: string;
  metadata_json: Record<string, any>;
  request_data: Record<string, any>;
  host?: string;
  release?: string;
  created_at: string;
}

export interface NotificationRecord {
  id: number;
  incident_id: string;
  notification_type: string;
  recipient_email: string;
  recipient_name?: string;
  subject: string;
  status: 'pending' | 'sent' | 'failed' | 'retrying';
  attempts_count: number;
  last_attempt_at?: string;
  error_message?: string;
  sent_at?: string;
  created_at: string;
}

export interface Incident {
  id: string;
  project_id: string;
  project_name?: string;
  fingerprint: string;
  title: string;
  error_type: string;
  message: string;
  severity: Severity;
  status: IncidentStatus;
  environment: string;
  phase: string;
  service: string;
  first_seen: string;
  last_seen: string;
  occurrence_count: number;
  assigned_user_id?: number;
  assigned_team?: string;
  assigned_email?: string;
  routing_reason?: string;
  last_notified_at?: string;
  notification_count: number;
  created_at: string;
  updated_at: string;
  assigned_user?: User;
  events?: ErrorEvent[];
  notifications?: NotificationRecord[];
  ai_summary?: string;
  ai_suggested_fix?: string;
}

export interface OverviewAnalytics {
  total_events: number;
  open_incidents: number;
  critical_incidents: number;
  resolved_incidents: number;
  errors_by_project: { name: string; count: number }[];
  errors_by_environment: { name: string; count: number }[];
  errors_by_phase: { name: string; count: number }[];
  errors_by_severity: { name: string; count: number }[];
  error_trends: { date: string; count: number; critical_count: number }[];
}

export interface AuditLog {
  id: number;
  organization_id: number;
  project_id?: string;
  user_id?: number;
  user_email?: string;
  action: string;
  resource_type: string;
  resource_id?: string;
  details: Record<string, any>;
  ip_address?: string;
  created_at: string;
}
