import React from 'react';

interface PhaseBadgeProps {
  phase: string;
}

export const PhaseBadge: React.FC<PhaseBadgeProps> = ({ phase }) => {
  const p = (phase || 'Unknown').toLowerCase();

  const colors: Record<string, string> = {
    production: '#f43f5e',
    deployment: '#a855f7',
    build: '#06b6d4',
    testing: '#10b981',
    staging: '#f59e0b',
    development: '#3b82f6',
    unknown: '#64748b',
  };

  const color = colors[p] || '#64748b';

  return (
    <span
      className="badge"
      style={{
        backgroundColor: `${color}18`,
        color: color,
        border: `1px solid ${color}40`,
      }}
    >
      {phase}
    </span>
  );
};
