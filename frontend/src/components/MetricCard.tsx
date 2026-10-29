import React from 'react';

interface MetricCardProps {
  title: string;
  value: number | string;
  subtitle?: string;
  icon: React.ReactNode;
  trend?: string;
  trendColor?: string;
}

export const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  subtitle,
  icon,
  trend,
  trendColor = 'var(--accent)',
}) => {
  return (
    <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-secondary)' }}>
          {title}
        </span>
        <div style={{ padding: '8px', borderRadius: '8px', backgroundColor: 'var(--accent-subtle)', color: 'var(--accent)' }}>
          {icon}
        </div>
      </div>
      <div style={{ fontSize: '28px', fontWeight: 700, color: 'var(--text-primary)' }}>
        {value}
      </div>
      {(subtitle || trend) && (
        <div style={{ fontSize: '12px', color: 'var(--text-muted)', display: 'flex', gap: '6px' }}>
          {trend && <span style={{ color: trendColor, fontWeight: 600 }}>{trend}</span>}
          {subtitle && <span>{subtitle}</span>}
        </div>
      )}
    </div>
  );
};
