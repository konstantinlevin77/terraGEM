import { useId } from 'react';
import { useMeasure } from '@/components/charts/useMeasure';

interface SparklineProps {
  data: number[];
  color: string;
  height?: number;
}

export function Sparkline({ data, color, height = 34 }: SparklineProps) {
  const [ref, width] = useMeasure();
  const uid = useId();
  const d = data ?? [];

  if (d.length < 2) {
    return (
      <div ref={ref} style={{ height }} className="mt-auto">
        <svg width="100%" height={height} />
      </div>
    );
  }

  let min = Infinity;
  let max = -Infinity;
  for (const v of d) {
    if (v < min) min = v;
    if (v > max) max = v;
  }
  const span = max - min || 1;
  const pad = 3;
  const x = (i: number) => pad + (i / (d.length - 1)) * (width - pad * 2);
  const y = (v: number) => height - pad - ((v - min) / span) * (height - pad * 2);
  const line = d.map((v, i) => `${i ? 'L' : 'M'}${x(i).toFixed(1)} ${y(v).toFixed(1)}`).join('');
  const area = `${line}L${x(d.length - 1).toFixed(1)} ${height}L${x(0).toFixed(1)} ${height}Z`;

  return (
    <div ref={ref} className="mt-auto" style={{ marginInline: -4, marginBottom: -2 }}>
      <svg width="100%" height={height} role="img">
        <defs>
          <linearGradient id={uid} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0" stopColor={color} stopOpacity=".22" />
            <stop offset="1" stopColor={color} stopOpacity="0" />
          </linearGradient>
        </defs>
        <path d={area} fill={`url(#${uid})`} />
        <path d={line} fill="none" stroke={color} strokeWidth="1.6" strokeLinejoin="round" />
        <circle cx={x(d.length - 1)} cy={y(d[d.length - 1])} r="2.4" fill={color} />
      </svg>
    </div>
  );
}
