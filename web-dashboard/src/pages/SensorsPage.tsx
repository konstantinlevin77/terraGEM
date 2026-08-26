import { useMemo, useState, type FormEvent } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { Cpu, Plus, X } from 'lucide-react';
import { sensorApi } from '@/api/sensors';
import { thresholdApi } from '@/api/thresholds';
import { ApiError } from '@/api/client';
import { useSensors } from '@/hooks/useSensors';
import { useGreenhouses } from '@/hooks/useGreenhouses';
import { useSensorProfiles } from '@/hooks/useSensorProfiles';
import { useThresholds } from '@/hooks/useThresholds';
import { useLatestBySensor } from '@/hooks/useLatestBySensor';
import { useT, useLang } from '@/i18n';
import { fmtUnit, fmtVal, relTime } from '@/lib/format';
import { sensorMeta } from '@/lib/sensorMeta';
import { statusOf } from '@/lib/statusOf';
import type { Sensor, SensorThreshold } from '@/types';
import { PageHead } from '@/components/ui/PageHead';
import { Button } from '@/components/ui/Button';
import { Modal } from '@/components/ui/Modal';
import { Field, inputClass } from '@/components/ui/Field';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { TypePill } from '@/components/ui/TypePill';
import { Switch } from '@/components/ui/Switch';
import { Drawer } from '@/components/ui/Drawer';
import { useToast } from '@/components/toast';

const TYPE_OPTIONS = [
  'air_temperature',
  'soil_temperature',
  'air_humidity',
  'soil_humidity',
  'co2',
  'ph',
  'light_intensity',
  'not_specified',
] as const;

export function SensorsPage() {
  const t = useT();
  const { lang } = useLang();
  const toast = useToast();
  const queryClient = useQueryClient();
  const { data: sensors = [] } = useSensors();
  const { data: greenhouses = [] } = useGreenhouses();

  const [fGh, setFGh] = useState(0);
  const [fType, setFType] = useState('all');
  const [fSt, setFSt] = useState('all');
  const [adding, setAdding] = useState(false);
  const [selectedId, setSelectedId] = useState<number | null>(null);

  const ghIds = useMemo(
    () => (fGh ? [fGh] : [...new Set(sensors.map((s) => s.greenhouse))]),
    [fGh, sensors],
  );
  const latestMap = useLatestBySensor(ghIds);
  const { data: thresholds = [] } = useThresholds();
  const thrBySensor = useMemo(() => {
    const m = new Map<number, SensorThreshold>();
    for (const th of thresholds) m.set(th.sensor, th);
    return m;
  }, [thresholds]);

  const rows = sensors.filter((s) => {
    if (fGh && s.greenhouse !== fGh) return false;
    if (fType !== 'all' && s.sensor_type !== fType) return false;
    if (fSt !== 'all' && (fSt === 'active') !== s.is_active) return false;
    return true;
  });

  const invalidateSensors = () => {
    queryClient.invalidateQueries({ queryKey: ['sensors'] });
    queryClient.invalidateQueries({ queryKey: ['gh-latest'] });
  };

  const toggleMut = useMutation({
    mutationFn: ({ id, is_active }: { id: number; is_active: boolean }) =>
      sensorApi.update(id, { is_active }),
    onSuccess: (_d, { id, is_active }) => {
      invalidateSensors();
      toast(is_active ? t('Sensor activated') : t('Sensor deactivated'), `PATCH /api/sensors/${id}/`);
    },
    onError: (err) => toast(t('Save failed'), err instanceof ApiError ? err.message : String(err)),
  });

  const selected = selectedId != null ? (sensors.find((s) => s.id === selectedId) ?? null) : null;

  const ghName = (id: number) => greenhouses.find((g) => g.id === id)?.name ?? `#${id}`;

  return (
    <div>
      <PageHead
        icon={Cpu}
        title={t('Sensors')}
        sub={t('{n} shown · {m} total', { n: rows.length, m: sensors.length })}
        actions={
          <Button variant="primary" onClick={() => setAdding(true)}>
            <Plus size={15} />
            {t('Add sensor')}
          </Button>
        }
      />

      <div className="mb-3.5 flex flex-wrap items-center gap-2">
        <select
          className="w-auto rounded-lg border border-border-strong bg-surface px-2.5 py-2 text-[13px] outline-none focus:border-accent-ring"
          aria-label={t('Filter by greenhouse')}
          value={fGh}
          onChange={(e) => setFGh(Number(e.target.value))}
        >
          <option value={0}>{t('All greenhouses')}</option>
          {greenhouses.map((g) => (
            <option key={g.id} value={g.id}>
              {g.name}
            </option>
          ))}
        </select>
        <select
          className="w-auto rounded-lg border border-border-strong bg-surface px-2.5 py-2 text-[13px] outline-none focus:border-accent-ring"
          aria-label={t('Filter by type')}
          value={fType}
          onChange={(e) => setFType(e.target.value)}
        >
          <option value="all">{t('All types')}</option>
          {TYPE_OPTIONS.map((ty) => (
            <option key={ty} value={ty}>
              {t(sensorMeta(ty).labelKey)}
            </option>
          ))}
        </select>
        <select
          className="w-auto rounded-lg border border-border-strong bg-surface px-2.5 py-2 text-[13px] outline-none focus:border-accent-ring"
          aria-label={t('Filter by status')}
          value={fSt}
          onChange={(e) => setFSt(e.target.value)}
        >
          <option value="all">{t('Any status')}</option>
          <option value="active">{t('Active only')}</option>
          <option value="inactive">{t('Inactive only')}</option>
        </select>
      </div>

      {rows.length === 0 ? (
        <div className="card flex flex-col items-center gap-1.5 p-7 text-center">
          <Cpu size={26} className="mb-1 opacity-75" />
          <div className="text-[13px] font-semibold">{t('No sensors match')}</div>
          <div className="max-w-[260px] text-xs text-muted">
            {t('Adjust the filters, or attach a new sensor to a greenhouse.')}
          </div>
        </div>
      ) : (
        <div className="card overflow-x-auto">
          <table className="w-full min-w-[680px] border-collapse text-[13px]">
            <thead>
              <tr>
                {[t('Sensor'), t('Greenhouse'), t('Type'), t('Profile'), t('Unit'), t('Latest'), t('Status'), t('Active')].map(
                  (h, i) => (
                    <th
                      key={i}
                      className={`border-b border-border px-3.5 py-2.5 text-left text-[10.5px] font-semibold tracking-[0.06em] uppercase whitespace-nowrap text-muted ${
                        i === 7 ? 'text-right' : ''
                      }`}
                    >
                      {h}
                    </th>
                  ),
                )}
              </tr>
            </thead>
            <tbody>
              {rows.map((s) => {
                const latest = latestMap.get(s.id);
                const band = thrBySensor.get(s.id);
                return (
                  <tr
                    key={s.id}
                    onClick={() => setSelectedId(s.id)}
                    className="cursor-pointer transition-colors hover:bg-surface-alt"
                  >
                    <td className="border-b border-border px-3.5 py-2.5 align-middle whitespace-nowrap">
                      <div className="font-medium">{s.description || t(sensorMeta(s.sensor_type).labelKey)}</div>
                      <div className="mt-px text-[11px] text-muted">#{s.id}</div>
                    </td>
                    <td className="border-b border-border px-3.5 py-2.5 align-middle whitespace-nowrap">{ghName(s.greenhouse)}</td>
                    <td className="border-b border-border px-3.5 py-2.5 align-middle whitespace-nowrap">
                      <TypePill type={s.sensor_type} />
                    </td>
                    <td className="mono border-b border-border px-3.5 py-2.5 align-middle text-xs whitespace-nowrap">
                      {s.profile_name ?? `#${s.profile}`}
                    </td>
                    <td className="border-b border-border px-3.5 py-2.5 align-middle whitespace-nowrap">{fmtUnit(s.unit)}</td>
                    <td className="border-b border-border px-3.5 py-2.5 align-middle whitespace-nowrap">
                      {latest ? (
                        <>
                          <div className="mono font-semibold">{fmtVal(s.unit, latest.value)}</div>
                          <div className="text-[10.5px] text-muted">{relTime(latest.time, lang)}</div>
                        </>
                      ) : (
                        '—'
                      )}
                    </td>
                    <td className="border-b border-border px-3.5 py-2.5 align-middle whitespace-nowrap">
                      {latest && band ? (
                        <StatusBadge status={statusOf(latest.value, band)} />
                      ) : (
                        <span className="rounded-full bg-surface-alt px-2 py-0.5 text-[10.5px] font-semibold text-muted">—</span>
                      )}
                    </td>
                    <td className="border-b border-border px-3.5 py-2.5 text-right align-middle" onClick={(e) => e.stopPropagation()}>
                      <Switch
                        checked={s.is_active}
                        label={`${t('Toggle sensor')} ${s.id}`}
                        onChange={(v) => toggleMut.mutate({ id: s.id, is_active: v })}
                      />
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {adding && (
        <AddSensorModal
          onClose={() => setAdding(false)}
          onCreated={(s) => {
            setAdding(false);
            invalidateSensors();
            setSelectedId(s.id);
            toast(t('Sensor added'), `POST /api/sensors/ · #${s.id}`);
          }}
        />
      )}

      {selected && (
        <SensorDrawer
          sensor={selected}
          greenhouseName={ghName(selected.greenhouse)}
          threshold={thrBySensor.get(selected.id)}
          latest={latestMap.get(selected.id)}
          onToggleActive={(v) => toggleMut.mutate({ id: selected.id, is_active: v })}
          onThresholdSaved={() => queryClient.invalidateQueries({ queryKey: ['thresholds'] })}
          onClose={() => setSelectedId(null)}
        />
      )}
    </div>
  );
}

function AddSensorModal({
  onClose,
  onCreated,
}: {
  onClose: () => void;
  onCreated: (s: Sensor) => void;
}) {
  const t = useT();
  const { data: greenhouses = [] } = useGreenhouses();
  const { data: profiles = [] } = useSensorProfiles();
  const [greenhouse, setGreenhouse] = useState(greenhouses[0]?.id ?? 0);
  const [profile, setProfile] = useState(0);
  const [description, setDescription] = useState('');
  const [error, setError] = useState<string | null>(null);
  const profileValue = profile || profiles[0]?.id || 0;

  const createMut = useMutation({
    mutationFn: () =>
      sensorApi.create({ greenhouse, profile: profileValue, description: description.trim() }),
    onSuccess: onCreated,
    onError: (err) => setError(err instanceof ApiError ? err.message : String(err)),
  });

  const submit = (e: FormEvent) => {
    e.preventDefault();
    if (!greenhouse || !profileValue) return;
    setError(null);
    createMut.mutate();
  };

  return (
    <Modal
      title={t('Add sensor')}
      onClose={onClose}
      footer={
        <>
          <Button onClick={onClose}>{t('Cancel')}</Button>
          <Button variant="primary" disabled={!greenhouse || !profile || createMut.isPending} onClick={submit}>
            {t('Create sensor')}
          </Button>
        </>
      }
    >
      <form onSubmit={submit}>
        <Field label={t('Greenhouse')} required htmlFor="sensor-gh">
          <select
            id="sensor-gh"
            className={inputClass()}
            autoFocus
            value={greenhouse}
            onChange={(e) => setGreenhouse(Number(e.target.value))}
          >
            {greenhouses.map((g) => (
              <option key={g.id} value={g.id}>
                {g.name}
              </option>
            ))}
          </select>
        </Field>
        <Field label={t('Sensor profile')} required hint={t('Determines type and unit')} htmlFor="sensor-profile">
          <select
            id="sensor-profile"
            className={inputClass()}
            value={profileValue}
            onChange={(e) => setProfile(Number(e.target.value))}
          >
            {profiles.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name} — {t(sensorMeta(p.sensor_type).labelKey)} ({fmtUnit(p.unit)})
              </option>
            ))}
          </select>
        </Field>
        <Field label={t('Description')} hint={t('Where is it placed? e.g. “Bed 2, 10 cm depth”')} htmlFor="sensor-desc">
          <input
            id="sensor-desc"
            className={inputClass()}
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder={t('Optional placement note')}
          />
        </Field>
        {error && (
          <p role="alert" className="mb-3 text-[11.5px] text-danger">
            {error}
          </p>
        )}
        <button type="submit" hidden />
      </form>
    </Modal>
  );
}

function SensorDrawer({
  sensor,
  greenhouseName,
  threshold,
  latest,
  onToggleActive,
  onThresholdSaved,
  onClose,
}: {
  sensor: Sensor;
  greenhouseName: string;
  threshold: SensorThreshold | undefined;
  latest: { value: number; time: string } | undefined;
  onToggleActive: (v: boolean) => void;
  onThresholdSaved: () => void;
  onClose: () => void;
}) {
  const t = useT();
  const { lang } = useLang();
  const m = sensorMeta(sensor.sensor_type);

  return (
    <Drawer label={t('Sensor details')} onClose={onClose}>
      <div className="sticky top-0 z-2 flex items-center justify-between gap-2.5 border-b border-border bg-surface px-5 py-3.5">
        <div className="min-w-0">
          <div className="truncate text-[15px] font-semibold tracking-[-0.01em]">
            {sensor.description || t(m.labelKey)}
          </div>
          <div className="text-[11px] text-muted">
            #{sensor.id} · {greenhouseName}
          </div>
        </div>
        <Button size="icon" aria-label={t('Close panel')} onClick={onClose}>
          <X size={15} />
        </Button>
      </div>

      <div className="mx-5 my-4 grid grid-cols-2 gap-px overflow-hidden rounded-[10px] border border-border bg-border">
        <MetaCell k={t('Type')}>
          <TypePill type={sensor.sensor_type} />
        </MetaCell>
        <MetaCell k={t('Profile')}>{sensor.profile_name ?? `#${sensor.profile}`}</MetaCell>
        <MetaCell k={t('Unit')}>{fmtUnit(sensor.unit)}</MetaCell>
        <MetaCell k={t('Installed')}>{new Date(sensor.created_at).toLocaleDateString(lang === 'tr' ? 'tr-TR' : undefined, { year: 'numeric', month: 'short', day: 'numeric' })}</MetaCell>
        <MetaCell k={t('Latest')}>
          {latest ? (
            <span className="mono">
              {fmtVal(sensor.unit, latest.value)}{' '}
              <span className="text-[11px] font-normal text-muted">· {relTime(latest.time, lang)}</span>
            </span>
          ) : (
            '—'
          )}
        </MetaCell>
        <MetaCell k={t('Active')}>
          <Switch checked={sensor.is_active} label={t('Toggle active')} onChange={onToggleActive} />
        </MetaCell>
      </div>

      <ThresholdEditor sensor={sensor} existing={threshold} latestValue={latest?.value} onSaved={onThresholdSaved} />
    </Drawer>
  );
}

function MetaCell({ k, children }: { k: string; children: React.ReactNode }) {
  return (
    <div className="min-w-0 bg-surface px-3 py-2.5">
      <div className="mb-0.5 text-[10px] tracking-[0.06em] uppercase text-muted">{k}</div>
      <div className="truncate text-[13px] font-medium">{children}</div>
    </div>
  );
}

function ThresholdEditor({
  sensor,
  existing,
  latestValue,
  onSaved,
}: {
  sensor: Sensor;
  existing: SensorThreshold | undefined;
  latestValue: number | undefined;
  onSaved: () => void;
}) {
  const t = useT();
  const toast = useToast();
  const unit = fmtUnit(sensor.unit);

  const blank = { warning_min: '', warning_max: '', critical_min: '', critical_max: '' };
  const initial = existing
    ? {
        warning_min: String(existing.warning_min),
        warning_max: String(existing.warning_max),
        critical_min: String(existing.critical_min),
        critical_max: String(existing.critical_max),
      }
    : blank;
  const [form, setForm] = useState(initial);
  const [errors, setErrors] = useState<Partial<Record<keyof typeof blank, string>>>({});

  const saveMut = useMutation({
    mutationFn: (payload: Parameters<typeof thresholdApi.create>[0]) =>
      existing ? thresholdApi.update(existing.id, payload) : thresholdApi.create(payload),
    onSuccess: () => {
      onSaved();
      toast(t('Thresholds saved'), `${existing ? 'PATCH' : 'POST'} /api/thresholds/${existing ? existing.id + '/' : ''}`);
    },
    onError: (err) => toast(t('Save failed'), err instanceof ApiError ? err.message : String(err)),
  });

  const submit = (e: FormEvent) => {
    e.preventDefault();
    const errs: Partial<Record<keyof typeof blank, string>> = {};
    const num = (v: string) => parseFloat(v);
    for (const k of Object.keys(blank) as (keyof typeof blank)[]) {
      if (isNaN(num(form[k]))) errs[k] = t('Must be a number.');
    }
    if (!errs.warning_min && !errs.warning_max && num(form.warning_min) > num(form.warning_max)) {
      errs.warning_max = t('Must be greater than minimum.');
    }
    if (!errs.critical_min && !errs.critical_max && num(form.critical_min) > num(form.critical_max)) {
      errs.critical_max = t('Must be greater than minimum.');
    }
    setErrors(errs);
    if (Object.keys(errs).length) return;
    saveMut.mutate({
      sensor: sensor.id,
      warning_min: num(form.warning_min),
      warning_max: num(form.warning_max),
      critical_min: num(form.critical_min),
      critical_max: num(form.critical_max),
      is_active: true,
    });
  };

  return (
    <div className="pb-6">
      <div className="px-5 pt-1 pb-1.5 text-[11px] font-semibold tracking-[0.07em] uppercase text-muted">
        {t('Alert thresholds')}
      </div>
      {latestValue != null && (
        <div className="mx-5 mb-3 flex items-center justify-between rounded-lg bg-surface-alt px-3 py-2 text-xs">
          <span className="text-muted">{t('Current status')}</span>
          <StatusBadge status={statusOf(latestValue, existing)} />
        </div>
      )}
      <form onSubmit={submit} className="px-5">
        <div className="grid grid-cols-2 gap-x-2.5">
          <Field label={`${t('Warning min')} (${unit})`} error={errors.warning_min} htmlFor="th-wmin">
            <input
              id="th-wmin"
              className={inputClass(errors.warning_min)}
              inputMode="decimal"
              value={form.warning_min}
              onChange={(e) => setForm({ ...form, warning_min: e.target.value })}
            />
          </Field>
          <Field label={`${t('Warning max')} (${unit})`} error={errors.warning_max} htmlFor="th-wmax">
            <input
              id="th-wmax"
              className={inputClass(errors.warning_max)}
              inputMode="decimal"
              value={form.warning_max}
              onChange={(e) => setForm({ ...form, warning_max: e.target.value })}
            />
          </Field>
          <Field label={`${t('Critical min')} (${unit})`} error={errors.critical_min} htmlFor="th-cmin">
            <input
              id="th-cmin"
              className={inputClass(errors.critical_min)}
              inputMode="decimal"
              value={form.critical_min}
              onChange={(e) => setForm({ ...form, critical_min: e.target.value })}
            />
          </Field>
          <Field label={`${t('Critical max')} (${unit})`} error={errors.critical_max} htmlFor="th-cmax">
            <input
              id="th-cmax"
              className={inputClass(errors.critical_max)}
              inputMode="decimal"
              value={form.critical_max}
              onChange={(e) => setForm({ ...form, critical_max: e.target.value })}
            />
          </Field>
        </div>
        <Button variant="primary" type="submit" disabled={saveMut.isPending}>
          {t('Save thresholds')}
        </Button>
      </form>
    </div>
  );
}
