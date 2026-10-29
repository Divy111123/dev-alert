import React from 'react';
import { Severity } from '../types';

interface SeverityBadgeProps {
  severity: Severity | string;
}

export const SeverityBadge: React.FC<SeverityBadgeProps> = ({ severity }) => {
  const sev = (severity || 'medium').toLowerCase();
  
  const styles: Record<string, { bg: string; color: string; border: string }> = {
    critical: { bg: 'var(--critical-bg)', color: 'var(--critical)', border: 'rgba(239, 68, 68, 0.4)' },
    high: { bg: 'var(--high-bg)', color: 'var(--high)', border: 'rgba(249, 115, 22, 0.4)' },
    medium: { bg: 'var(--medium-bg)', color: 'var(--medium)', border: 'rgba(245, 158, 11, 0.4)' },
    low: { bg: 'var(--low-bg)', color: 'var(--low)', border: 'rgba(59, 130, 246, 0.4)' },
  };

  const current = styles[sev] || styles.medium;

  return (
    <span
      className="badge"
      style={{
        backgroundColor: current.bg,
        color: current.color,
        border: `1px solid ${current.border}`,
      }}
    >
      ● {sev.toUpperCase()}
    </span>
  );
};
