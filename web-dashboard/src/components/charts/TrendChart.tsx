import { useId, useState } from 'react';
import { clamp } from '@/lib/math';
import { fmtDateTime } from '@/lib/format';
import { useLang } from '@/i18n';
import { useMeasure } from '@/components/charts/useMeasure';

export interface ChartSeries {
  key: string;
  label: string;
  color: string;
  data: { t: number; v: number }[];
  fmt: (v: number) => string;
}

export interface ChartBand {
  min: number;
  max: number;
  color: string;
}

interface TrendChartProps {
  series: ChartSeries[];
  band?: ChartBand | null;
  height?: number;
  tickFmt?: (t: number) => string;
}

export function TrendChart({ series, band = null, height = 250, tickFmt }: TrendChartProps) {
  const [ref, width] = useMeasure();
  const [hovT, setHovT] = useState<number | null>(null);
  const { lang } = useLang();

  const vis = series.filter((s) => s.data.length > 1);
  const padL = 48;
  const padR = 14;
  const padT = 12;
  const padB = 26;
  const iw = Math.max(width - padL - padR, 40);
  const ih = height - padT - padB;

  if (vis.length === 0) {
    return (
      <div ref={ref} className="px-2.5 pt-1.5 pb-2.5" style={{ height }}>
        <svg width="100%" height={height} />
      </div>
    );
  }

  let t0 = Infinity;
  let t1 = -Infinity;
  let vmin = Infinity;
  let vmax = -Infinity;
  for (const s of vis) {
    for (const p of s.data) {
      if (p.t < t0) t0 = p.t;
      if (p.t > t1) t1 = p.t;
      if (p.v < vmin) vmin = p.v;
      if (p.v > vmax) vmax = p.v;
    }
  }
  if (band) {
    vmin = Math.min(vmin, band.min);
    vmax = Math.max(vmax, band.max);
  }
  const vspan = vmax - vmin || 1;
  vmin -= vspan * 0.1;
  vmax += vspan * 0.08;

  const X = (t: number) => padL + ((t - t0) / (t1 - t0 || 1)) * iw;
  const Y = (v: number) => padT + ih - ((v - vmin) / (vmax - vmin)) * ih;

  const axisFmt =
    vis.length === 1
      ? vis[0].fmt
      : (v: number) => String(Math.round(v * 10) / 10);
  const yTicks = [0, 0.25, 0.5, 0.75, 1].map((f) => [vmax - f * (vmax - vmin), padT + f * ih] as const);
  const xTicks = [0, 0.25, 0.5, 0.75, 1].map((f) => t0 + f * (t1 - t0));
  const base = vis[0].data;
  const fmtTick = tickFmt ?? ((t: number) => fmtDateTime(t, lang));

  const onMove = (e: React.MouseEvent<HTMLDivElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const px = e.clientX - rect.left;
    const t = t0 + ((px - padL) / iw) * (t1 - t0);
    let best: number | null = null;
    let bd = Infinity;
    for (const p of base) {
      const dd = Math.abs(p.t - t);
      if (dd < bd) {
        bd = dd;
        best = p.t;
      }
    }
    setHovT(best);
  };

  const nearest = (s: ChartSeries) => {
    if (hovT == null) return null;
    let bp = s.data[0];
    let bd = Infinity;
    for (const p of s.data) {
      const dd = Math.abs(p.t - hovT);
      if (dd < bd) {
        bd = dd;
        bp = p;
      }
    }
    return bp;
  };

  return (
    <div ref={ref} className="relative px-2.5 pt-1.5 pb-2.5" onMouseMove={onMove} onMouseLeave={() => setHovT(null)}>
      <svg width="100%" height={height} role="img">
        {yTicks.map(([v, y], i) => (
          <g key={i}>
            <line x1={padL} x2={padL + iw} y1={y} y2={y} stroke="var(--border)" strokeWidth="1" />
            <text
              x={padL - 8}
              y={y + 3}
              textAnchor="end"
              fontSize="10"
              fontFamily="ui-monospace,Menlo,monospace"
              fill="var(--muted)"
            >
              {axisFmt(v)}
            </text>
          </g>
        ))}

        {band && (
          <g>
            <rect
              x={padL}
              y={Y(band.max)}
              width={iw}
              height={Math.max(Y(band.min) - Y(band.max), 1)}
              fill={`color-mix(in oklab, ${band.color} 7%, transparent)`}
            />
            <line x1={padL} x2={padL + iw} y1={Y(band.max)} y2={Y(band.max)} stroke={band.color} strokeDasharray="3 4" opacity=".55" />
            <line x1={padL} x2={padL + iw} y1={Y(band.min)} y2={Y(band.min)} stroke={band.color} strokeDasharray="3 4" opacity=".55" />
          </g>
        )}

        {vis.map((s) => (
          <TrendPath key={s.key} series={s} X={X} Y={Y} baseY={padT + ih} />
        ))}

        {xTicks.map((t, i) => (
          <text
            key={`x${i}`}
            x={clamp(X(t), padL + 18, padL + iw - 18)}
            y={height - 8}
            textAnchor="middle"
            fontSize="10"
            fontFamily="ui-monospace,Menlo,monospace"
            fill="var(--muted)"
          >
            {fmtTick(t)}
          </text>
        ))}

        {hovT != null && (
          <g>
            <line x1={X(hovT)} x2={X(hovT)} y1={padT} y2={padT + ih} stroke="var(--border-strong)" strokeWidth="1" />
            {vis.map((s) => {
              const bp = nearest(s);
              return bp ? (
                <circle key={s.key} cx={X(bp.t)} cy={Y(bp.v)} r="3.5" fill="var(--surface)" stroke={s.color} strokeWidth="2" />
              ) : null;
            })}
          </g>
        )}
      </svg>

      {hovT != null && (
        <div className="tooltip pointer-events-none absolute top-2 z-5 min-w-[150px] rounded-[9px] border border-border-strong bg-surface px-3 py-2 shadow-[var(--shadow-pop)]" style={{ left: clamp(X(hovT) + 14, 10, Math.max(width - 170, 10)) }}>
          <div className="mb-1 text-[10.5px] text-muted">{fmtDateTime(hovT, lang)}</div>
          {vis.map((s) => {
            const bp = nearest(s);
            return bp ? (
              <div key={s.key} className="flex items-center gap-1.5 py-0.5 text-xs">
                <span className="h-[7px] w-[7px] shrink-0 rounded-[2.5px]" style={{ background: s.color }} />
                <span className="flex-1 pr-2 text-muted">{s.label}</span>
                <span className="mono font-semibold">{s.fmt(bp.v)}</span>
              </div>
            ) : null;
          })}
        </div>
      )}
    </div>
  );
}

function TrendPath({
  series,
  X,
  Y,
  baseY,
}: {
  series: ChartSeries;
  X: (t: number) => number;
  Y: (v: number) => number;
  baseY: number;
}) {
  const uid = useId();
  const path = series.data.map((p, i) => `${i ? 'L' : 'M'}${X(p.t).toFixed(1)} ${Y(p.v).toFixed(1)}`).join('');
  const area = `${path}L${X(series.data[series.data.length - 1].t).toFixed(1)} ${baseY}L${X(series.data[0].t).toFixed(1)} ${baseY}Z`;
  return (
    <g>
      <defs>
        <linearGradient id={uid} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor={series.color} stopOpacity=".14" />
          <stop offset="1" stopColor={series.color} stopOpacity="0" />
        </linearGradient>
      </defs>
      <path d={area} fill={`url(#${uid})`} />
      <path d={path} fill="none" stroke={series.color} strokeWidth="2" strokeLinejoin="round" />
    </g>
  );
}
