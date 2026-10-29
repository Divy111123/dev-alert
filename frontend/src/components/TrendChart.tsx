import React from 'react';

interface TrendPoint {
  date: string;
  count: number;
  critical_count: number;
}

interface TrendChartProps {
  data: TrendPoint[];
}

export const TrendChart: React.FC<TrendChartProps> = ({ data }) => {
  if (!data || data.length === 0) {
    return <div style={{ color: 'var(--text-muted)', padding: '24px', textAlign: 'center' }}>No trend data available</div>;
  }

  const maxVal = Math.max(...data.map(d => Math.max(d.count, 5)));
  const height = 180;
  const width = 600;
  const padding = 30;

  const points = data.map((d, index) => {
    const x = padding + (index * (width - 2 * padding)) / (data.length - 1 || 1);
    const y = height - padding - (d.count / maxVal) * (height - 2 * padding);
    return { x, y, count: d.count, date: d.date.split('-').slice(1).join('/') };
  });

  const pathD = points.length > 0 
    ? `M ${points[0].x} ${points[0].y} ` + points.slice(1).map(p => `L ${p.x} ${p.y}`).join(' ')
    : '';

  const areaD = points.length > 0
    ? `${pathD} L ${points[points.length - 1].x} ${height - padding} L ${points[0].x} ${height - padding} Z`
    : '';

  return (
    <div style={{ width: '100%', overflowX: 'auto' }}>
      <svg viewBox={`0 0 ${width} ${height}`} style={{ width: '100%', height: 'auto', maxHeight: '200px' }}>
        <defs>
          <linearGradient id="trendGradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#38bdf8" stopOpacity="0.4" />
            <stop offset="100%" stopColor="#38bdf8" stopOpacity="0.0" />
          </linearGradient>
        </defs>

        {/* Grid lines */}
        {[0, 0.5, 1].map((ratio, i) => {
          const y = height - padding - ratio * (height - 2 * padding);
          return (
            <line
              key={i}
              x1={padding}
              y1={y}
              x2={width - padding}
              y2={y}
              stroke="var(--border-subtle)"
              strokeDasharray="4 4"
            />
          );
        })}

        {/* Filled Area */}
        <path d={areaD} fill="url(#trendGradient)" />

        {/* Stroke Line */}
        <path d={pathD} fill="none" stroke="#38bdf8" strokeWidth="2.5" />

        {/* Data points */}
        {points.map((p, i) => (
          <g key={i}>
            <circle cx={p.x} cy={p.y} r="4" fill="#38bdf8" stroke="var(--bg-secondary)" strokeWidth="2" />
            <text
              x={p.x}
              y={height - 10}
              fill="var(--text-muted)"
              fontSize="11"
              textAnchor="middle"
            >
              {p.date}
            </text>
            <text
              x={p.x}
              y={p.y - 8}
              fill="var(--text-primary)"
              fontSize="10"
              fontWeight="600"
              textAnchor="middle"
            >
              {p.count}
            </text>
          </g>
        ))}
      </svg>
    </div>
  );
};
