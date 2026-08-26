import { useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Download, History as HistoryIcon } from 'lucide-react';
import { metricsApi } from '@/api/metrics';
import { useActiveGh } from '@/hooks/useActiveGh';
import { useGreenhouses } from '@/hooks/useGreenhouses';
import { useT, useLang } from '@/i18n';
import { fmtClock, fmtDateTime, fmtDay, fmtNum, fmtUnit, fmtVal } from '@/lib/format';
import { sensorMeta } from '@/lib/sensorMeta';
import type { SensorType, SensorUnit } from '@/types';
import { PageHead } from '@/components/ui/PageHead';
import { Button } from '@/components/ui/Button';
import { TrendChart, type ChartSeries } from '@/components/charts/TrendChart';

const PAGE_SIZE = 14;

const TYPE_UNITS: Partial<Record<SensorType, SensorUnit>> = {
  air_temperature: 'celsius',
  soil_temperature: 'celsius',
  air_humidity: 'percent',
  soil_humidity: 'percent',
  co2: 'ppm',
  ph: 'ph',
  light_intensity: 'ppm',
};

interface Bucket {
  timestamp: string;
  t: number;
  avg_value: number;
  min_value: number;
  max_value: number;
  reading_count: number;
}

export function HistoryPage() {
  const t = useT();
  const { lang } = useLang();
  const { ghId, setGhId } = useActiveGh();
  const { data: greenhouses = [] } = useGreenhouses();
  const [type, setType] = useState<SensorType | ''>('');
  const [page, setPage] = useState(0);

  const overviewQ = useQuery({
    queryKey: ['day-overview', ghId],
    queryFn: () => metricsApi.dayOverview(ghId!),
    enabled: ghId != null,
  });

  const series = useMemo(() => overviewQ.data?.series ?? [], [overviewQ.data]);

  const effectiveType: SensorType | '' =
    type && series.some((s) => s.sensor_type === type) ? type : (series[0]?.sensor_type ?? '');

  const selected = series.find((s) => s.sensor_type === effectiveType) ?? null;
  const unit: SensorUnit = effectiveType ? (TYPE_UNITS[effectiveType] ?? 'not_specified') : 'not_specified';
  const m = effectiveType ? sensorMeta(effectiveType) : null;

  const rowsDesc = useMemo<Bucket[]>(
    () =>
      selected
        ? [...selected.timeline]
            .map((p) => ({ ...p, t: new Date(p.timestamp).getTime() }))
            .sort((a, b) => b.t - a.t)
        : [],
    [selected],
  );
  const pages = Math.max(1, Math.ceil(rowsDesc.length / PAGE_SIZE));
  const pg = Math.min(page, pages - 1);

  const exportCsv = () => {
    if (!rowsDesc.length || !effectiveType) return;
    const header = 'measurement_time,avg,min,max,readings';
    const lines = [...rowsDesc]
      .reverse()
      .map((r) =>
        [new Date(r.timestamp).toISOString(), r.avg_value, r.min_value, r.max_value, r.reading_count].join(','),
      );
    const blob = new Blob([`${header}\n${lines.join('\n')}\n`], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `terragem-${ghId}-${effectiveType}-24h.csv`;
    a.click();
    setTimeout(() => URL.revokeObjectURL(url), 500);
  };

  const chartSeries: ChartSeries[] | null =
    selected && rowsDesc.length >= 2
      ? [
          {
            key: 'min',
            label: t('Min'),
            color: `color-mix(in oklab, ${m!.color} 45%, transparent)`,
            data: rowsDesc.map((r) => ({ t: r.t, v: r.min_value })),
            fmt: (v) => fmtVal(unit, v),
          },
          {
            key: 'max',
            label: t('Max'),
            color: `color-mix(in oklab, ${m!.color} 45%, transparent)`,
            data: rowsDesc.map((r) => ({ t: r.t, v: r.max_value })),
            fmt: (v) => fmtVal(unit, v),
          },
          {
            key: 'avg',
            label: t(m!.shortKey),
            color: m!.color,
            data: rowsDesc.map((r) => ({ t: r.t, v: r.avg_value })),
            fmt: (v) => fmtVal(unit, v),
          },
        ]
      : null;

  const tickFmt = (time: number) =>
    fmtDay(time, lang) === fmtDay(Date.now(), lang) ? fmtClock(time, lang) : fmtDay(time, lang);

  return (
    <div>
      <PageHead
        icon={HistoryIcon}
        title={t('History')}
        sub={t('Measurement explorer · last 24 hours in 10-minute intervals')}
      />

      <div className="mb-3.5 flex flex-wrap items-center gap-2">
        <select
          className="w-auto rounded-lg border border-border-strong bg-surface px-2.5 py-2 text-[13px] outline-none focus:border-accent-ring"
          aria-label={t('Greenhouse')}
          value={ghId ?? 0}
          onChange={(e) => {
            setGhId(Number(e.target.value));
            setType('');
            setPage(0);
          }}
        >
          {greenhouses.map((g) => (
            <option key={g.id} value={g.id}>
              {g.name}
            </option>
          ))}
        </select>
        <select
          className="min-w-[200px] rounded-lg border border-border-strong bg-surface px-2.5 py-2 text-[13px] outline-none focus:border-accent-ring"
          aria-label={t('Metric')}
          value={effectiveType}
          onChange={(e) => {
            setType(e.target.value as SensorType);
            setPage(0);
          }}
        >
          {series.length === 0 && <option value="">{t('Choose a metric…')}</option>}
          {series.map((s) => (
            <option key={s.sensor_type} value={s.sensor_type}>
              {t(sensorMeta(s.sensor_type).labelKey)}
            </option>
          ))}
        </select>
        {selected && (
          <span className="text-[11.5px] text-muted">
            {t('{n} intervals in window', { n: rowsDesc.length.toLocaleString() })}
          </span>
        )}
        <Button className="ml-auto" onClick={exportCsv} disabled={!selected || rowsDesc.length === 0}>
          <Download size={14} />
          {t('Export CSV')}
        </Button>
      </div>

      {!selected ? (
        <div className="card flex flex-col items-center gap-1.5 p-7 text-center">
          <HistoryIcon size={26} className="mb-1 opacity-75" />
          <div className="text-[13px] font-semibold">{t('Pick a metric')}</div>
          <div className="max-w-[260px] text-xs text-muted">
            {t('Select a greenhouse and metric above to explore its aggregated history.')}
          </div>
        </div>
      ) : (
        <>
          <div className="card mb-3.5 overflow-hidden">
            {chartSeries ? (
              <TrendChart series={chartSeries} height={250} tickFmt={tickFmt} />
            ) : (
              <div className="h-[250px]" />
            )}
          </div>

          <div className="card overflow-x-auto">
            <table className="w-full min-w-[420px] border-collapse text-[13px]">
              <thead>
                <tr>
                  {[t('Interval start'), `Avg (${fmtUnit(unit)})`, `Min / Max`, t('Readings')].map((h, i) => (
                    <th
                      key={i}
                      className={`border-b border-border px-3.5 py-2.5 text-left text-[10.5px] font-semibold tracking-[0.06em] uppercase whitespace-nowrap text-muted ${
                        i >= 1 ? 'text-right' : ''
                      }`}
                    >
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {rowsDesc.slice(pg * PAGE_SIZE, (pg + 1) * PAGE_SIZE).map((r) => (
                  <tr key={r.timestamp}>
                    <td className="mono border-b border-border px-3.5 py-2.5 align-middle whitespace-nowrap text-[12.5px]">
                      {fmtDateTime(r.t, lang)}
                    </td>
                    <td className="mono border-b border-border px-3.5 py-2.5 text-right align-middle font-semibold whitespace-nowrap">
                      {fmtNum(unit, r.avg_value)}
                    </td>
                    <td className="mono border-b border-border px-3.5 py-2.5 text-right align-middle whitespace-nowrap text-muted">
                      {fmtNum(unit, r.min_value)} / {fmtNum(unit, r.max_value)}
                    </td>
                    <td className="border-b border-border px-3.5 py-2.5 text-right align-middle whitespace-nowrap">
                      {r.reading_count}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            <div className="flex items-center justify-between px-3.5 py-2.5 text-xs text-muted">
              <span>
                {rowsDesc.length
                  ? t('{a}–{b} of {n}', {
                      a: pg * PAGE_SIZE + 1,
                      b: Math.min(rowsDesc.length, (pg + 1) * PAGE_SIZE),
                      n: rowsDesc.length.toLocaleString(),
                    })
                  : 0}
              </span>
              <div className="flex gap-1.5">
                <Button size="sm" disabled={pg === 0} onClick={() => setPage(pg - 1)}>
                  {t('Previous')}
                </Button>
                <Button size="sm" disabled={pg >= pages - 1} onClick={() => setPage(pg + 1)}>
                  {t('Next')}
                </Button>
              </div>
            </div>
          </div>

          <p className="mt-3 text-[11px] text-muted">
            {t('Aggregated data comes from the 24-hour overview endpoint.')}
          </p>
        </>
      )}
    </div>
  );
}
