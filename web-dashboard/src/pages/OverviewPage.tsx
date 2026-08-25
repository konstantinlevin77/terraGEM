import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link, useNavigate } from 'react-router';
import { Warehouse, AlertTriangle, Sprout, Plus } from 'lucide-react';
import { metricsApi } from '@/api/metrics';
import { alertsApi } from '@/api/alerts';
import { useActiveGh } from '@/hooks/useActiveGh';
import { useScope } from '@/hooks/useScope';
import { useT, useLang } from '@/i18n';
import { fmtClock, fmtNum, fmtUnit, fmtVal, mapApiStatus, relTime } from '@/lib/format';
import { sensorMeta } from '@/lib/sensorMeta';
import { cn } from '@/lib/utils';
import type { MetricCard, SensorType, SensorUnit } from '@/types';
import { PageHead } from '@/components/ui/PageHead';
import { StatusBadge, type StatusLevel } from '@/components/ui/StatusBadge';
import { TypePill } from '@/components/ui/TypePill';
import { Sparkline } from '@/components/charts/Sparkline';
import { TrendChart, type ChartSeries } from '@/components/charts/TrendChart';

export function OverviewPage() {
  const t = useT();
  const { lang } = useLang();
  const { ghId, greenhouse } = useActiveGh();
  const { live } = useScope();
  const navigate = useNavigate();
  const [hidden, setHidden] = useState<Set<SensorType>>(new Set());

  const enabled = ghId != null;
  const metricsQ = useQuery({
    queryKey: ['latest-metrics', ghId],
    queryFn: () => metricsApi.latestMetrics(ghId!),
    enabled,
    refetchInterval: live ? 15_000 : false,
  });
  const overviewQ = useQuery({
    queryKey: ['day-overview', ghId],
    queryFn: () => metricsApi.dayOverview(ghId!),
    enabled,
    refetchInterval: live ? 60_000 : false,
  });
  const todayQ = useQuery({
    queryKey: ['today-summary', ghId],
    queryFn: () => metricsApi.todaySummary(ghId!),
    enabled,
  });
  const snapshotQ = useQuery({
    queryKey: ['gh-latest', ghId],
    queryFn: () => metricsApi.latestSnapshot(ghId!),
    enabled,
    refetchInterval: live ? 30_000 : false,
  });
  const alertsQ = useQuery({
    queryKey: ['alerts-active'],
    queryFn: alertsApi.active,
    refetchInterval: live ? 30_000 : false,
  });

  const toggleSeries = (type: SensorType) =>
    setHidden((prev) => {
      const next = new Set(prev);
      if (next.has(type)) next.delete(type);
      else next.add(type);
      return next;
    });

  if (!enabled) {
    return (
      <div>
        <PageHead icon={Warehouse} title={t('Overview')} />
        <div className="card flex flex-col items-center gap-2 p-8 text-center">
          <Sprout size={26} className="mb-1 opacity-75" />
          <div className="text-[13px] font-semibold">{t('No greenhouses yet')}</div>
          <div className="max-w-[240px] text-xs text-muted">
            {t('Create your first location to start attaching sensors.')}
          </div>
          <Link
            to="/greenhouses"
            className="mt-2 inline-flex items-center gap-1.5 rounded-lg bg-accent px-3 py-1.5 text-[13px] font-medium text-white transition-colors hover:bg-accent-hover"
          >
            <Plus size={14} />
            {t('Add greenhouse')}
          </Link>
        </div>
      </div>
    );
  }

  const metrics = metricsQ.data?.metrics ?? [];
  const activeSensorCount =
    snapshotQ.data?.sensors.filter((s) => s.is_active).length ?? 0;

  const chartSeries: ChartSeries[] = (overviewQ.data?.series ?? [])
    .filter((s) => !hidden.has(s.sensor_type))
    .map((s) => ({
      key: s.sensor_type,
      label: t(sensorMeta(s.sensor_type).shortKey),
      color: sensorMeta(s.sensor_type).color,
      data: s.timeline.map((p) => ({ t: new Date(p.timestamp).getTime(), v: p.avg_value })),
      fmt: (v: number) => fmtVal(TYPE_UNITS[s.sensor_type] ?? 'not_specified', v),
    }));
  const allSeries = overviewQ.data?.series ?? [];

  const ghAlerts = (alertsQ.data?.alerts ?? [])
    .filter((a) => a.greenhouse_id === ghId)
    .sort((a, b) => (a.severity === 'critical' ? -1 : 1) - (b.severity === 'critical' ? -1 : 1));

  const readings = (snapshotQ.data?.sensors ?? [])
    .filter((s) => s.latest_measurement)
    .sort(
      (a, b) =>
        new Date(b.latest_measurement!.measurement_time).getTime() -
        new Date(a.latest_measurement!.measurement_time).getTime(),
    )
    .slice(0, 8);

  return (
    <div>
      <PageHead
        icon={Warehouse}
        title={t('Overview')}
        sub={
          greenhouse
            ? `${greenhouse.name} · ${greenhouse.latitude ?? '—'}, ${greenhouse.longitude ?? '—'} · ${t('{n} active sensors', { n: activeSensorCount })}`
            : undefined
        }
      />

      <div className="mb-3.5 grid grid-cols-1 gap-3.5 sm:grid-cols-2 xl:grid-cols-4">
        {metrics.map((m) => (
          <KpiCard key={m.sensor_type} metric={m} />
        ))}
        {!metricsQ.isLoading && metrics.length === 0 && (
          <div className="card col-span-full p-6 text-center text-[13px] text-muted">{t('No data yet')}</div>
        )}
      </div>

      <div className="mb-3.5 grid grid-cols-1 items-start gap-3.5 lg:grid-cols-[minmax(0,2fr)_minmax(280px,1fr)]">
        <div className="card overflow-hidden">
          <div className="flex items-center justify-between gap-2.5 border-b border-border px-4.5 py-3">
            <div className="flex items-center gap-2 text-[13.5px] font-semibold tracking-[-0.01em]">
              {t('Environment trend')}
              <span className="text-[11.5px] font-normal text-muted">{t('last 24 h')}</span>
            </div>
            <div className="flex flex-wrap gap-1.5">
              {allSeries.map((s) => {
                const m = sensorMeta(s.sensor_type);
                const off = hidden.has(s.sensor_type);
                return (
                  <button
                    key={s.sensor_type}
                    onClick={() => toggleSeries(s.sensor_type)}
                    aria-pressed={!off}
                    className={cn(
                      'inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[11.5px] font-medium transition-colors',
                      off
                        ? 'border-border bg-surface text-muted hover:border-border-strong'
                        : 'border-border-strong bg-surface text-fg',
                    )}
                  >
                    <span className="h-2 w-2 rounded-[3px]" style={{ background: m.color, opacity: off ? 0.35 : 1 }} />
                    {t(m.shortKey)}
                  </button>
                );
              })}
            </div>
          </div>
          <TrendChart
            series={chartSeries}
            height={256}
            tickFmt={(time) => fmtClock(time, lang)}
          />
          <div className="px-4.5 pb-3 text-[11px] text-muted">{t('Toggle metrics off to isolate one series.')}</div>
        </div>

        <div className="flex min-w-0 flex-col gap-3.5">
          <div className="card" data-testid="alerts-card">
            <div className="flex items-center justify-between gap-2.5 border-b border-border px-4.5 py-3">
              <div className="flex items-center gap-2 text-[13.5px] font-semibold tracking-[-0.01em]">
                <AlertTriangle size={15} strokeWidth={1.8} />
                {t('Attention')}
              </div>
              {ghAlerts.length > 0 ? (
                <span className="rounded-full bg-danger-soft px-2 py-0.5 text-[10.5px] font-semibold text-danger">
                  {t('{n} open', { n: ghAlerts.length })}
                </span>
              ) : (
                <span className="rounded-full bg-surface-alt px-2 py-0.5 text-[10.5px] font-semibold text-muted">0</span>
              )}
            </div>
            {ghAlerts.length === 0 ? (
              <div className="flex flex-col items-center gap-1.5 p-7 text-center">
                <Sprout size={26} className="mb-1 opacity-75" />
                <div className="text-[13px] font-semibold">{t('All clear')}</div>
                <div className="max-w-[240px] text-xs text-muted">
                  {t('Every active sensor is inside its optimal range.')}
                </div>
              </div>
            ) : (
              ghAlerts.map((a) => (
                <button
                  key={a.id}
                  onClick={() => navigate('/sensors')}
                  className="flex w-full items-start gap-2.5 border-t border-border px-4 py-3 text-left first:border-t-0 hover:bg-surface-alt"
                >
                  <TypePill type={a.sensor_type} />
                  <span className="min-w-0 flex-1">
                    <span className="block truncate text-[12.5px] font-medium">{a.message}</span>
                    <span className="mt-px block text-[11px] text-muted">
                      {fmtVal(a.unit, a.triggered_value)} · {relTime(a.created_at, lang)}
                    </span>
                  </span>
                  <StatusBadge status={mapApiStatus(a.severity)} text={undefined} />
                </button>
              ))
            )}
          </div>

          <div className="card">
            <div className="flex items-center justify-between border-b border-border px-4.5 py-3">
              <div className="text-[13.5px] font-semibold tracking-[-0.01em]">{t('Today so far')}</div>
              <div className="text-[11.5px] text-muted">{todayQ.data?.date ?? ''}</div>
            </div>
            <div className="px-4.5 pb-3 pt-2">
              {(todayQ.data?.metrics ?? []).map((m) => (
                <div
                  key={m.sensor_type}
                  className="flex items-center justify-between gap-2.5 border-t border-border py-2 text-[12.5px] first:border-t-0"
                >
                  <span className="text-muted">{t(sensorMeta(m.sensor_type).labelKey)}</span>
                  <span className="mono font-semibold">
                    {fmtNum(m.unit, m.min_value)}–{fmtNum(m.unit, m.max_value)} {fmtUnit(m.unit)}
                  </span>
                </div>
              ))}
              {(todayQ.data?.metrics ?? []).length === 0 && (
                <div className="py-4 text-center text-xs text-muted">—</div>
              )}
            </div>
          </div>
        </div>
      </div>

      <div className="card">
        <div className="flex items-center justify-between border-b border-border px-4.5 py-3">
          <div className="text-[13.5px] font-semibold tracking-[-0.01em]">{t('Latest readings')}</div>
          <div className="mono text-[11.5px] text-muted">{t('newest first')}</div>
        </div>
        <div>
          {readings.map((s) => (
            <div key={s.id} className="flex items-center gap-2.5 border-t border-border px-4.5 py-2.5 text-[12.5px] first:border-t-0">
              <TypePill type={s.sensor_type} />
              <div className="min-w-0 flex-1">
                <div className="truncate text-xs font-medium">{s.description || s.profile_name}</div>
                <div className="text-[10.5px] text-muted">#{s.id}</div>
              </div>
              <span className="mono font-semibold whitespace-nowrap">
                {fmtVal(s.unit, s.latest_measurement!.value)}
              </span>
              <span className="w-16 shrink-0 text-right text-[10.5px] text-muted">
                {relTime(s.latest_measurement!.measurement_time, lang)}
              </span>
            </div>
          ))}
          {readings.length === 0 && <div className="py-5 text-center text-xs text-muted">{t('No data yet')}</div>}
        </div>
      </div>
    </div>
  );
}

const TYPE_UNITS: Partial<Record<SensorType, SensorUnit>> = {
  air_temperature: 'celsius',
  soil_temperature: 'celsius',
  air_humidity: 'percent',
  soil_humidity: 'percent',
  co2: 'ppm',
  ph: 'ph',
  light_intensity: 'ppm',
};

function KpiCard({ metric }: { metric: MetricCard }) {
  const t = useT();
  const m = sensorMeta(metric.sensor_type);
  const status: StatusLevel | null =
    metric.status === 'optimal'
      ? 'ok'
      : metric.status === 'warning'
        ? 'watch'
        : metric.status === 'critical'
          ? 'crit'
          : null;
  const cur = metric.current_value;
  const delta = metric.delta_24h;
  const deltaUnit = metric.unit === 'celsius' ? '°' : metric.unit === 'percent' ? '%' : '';

  return (
    <div className="card flex min-w-0 flex-col gap-2.5 px-4 pt-3.5 pb-3">
      <div className="flex w-full items-center gap-2">
        <span
          className="grid h-[26px] w-[26px] shrink-0 place-items-center rounded-[7px]"
          style={{ background: `color-mix(in oklab, ${m.color} 10%, white)`, color: m.color }}
        >
          <m.icon size={14} />
        </span>
        <span className="truncate text-[11px] font-semibold tracking-[0.05em] uppercase text-muted">
          {t(m.labelKey)}
        </span>
        <span className="ml-auto">{status && <StatusBadge status={status} />}</span>
      </div>
      <div className="flex items-baseline gap-1.5">
        <span className="mono text-[29px] leading-none font-medium tracking-[-0.02em]">
          {cur == null ? '—' : fmtNum(metric.unit, cur)}
        </span>
        <span className="text-[12.5px] font-medium text-muted">{fmtUnit(metric.unit)}</span>
      </div>
      <div className="mono text-[11.5px] text-muted">
        {delta == null
          ? t('waiting for data')
          : `${delta >= 0 ? '▲' : '▼'} ${Math.abs(delta).toFixed(1)}${deltaUnit} ${t('vs 24 h ago')}`}
      </div>
      <Sparkline data={metric.sparkline} color={m.color} />
    </div>
  );
}
