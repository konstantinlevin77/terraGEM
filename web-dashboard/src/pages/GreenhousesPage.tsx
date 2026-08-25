import { useState, type FormEvent } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router';
import { Warehouse, Plus, Pencil, Trash2 } from 'lucide-react';
import { greenhouseApi } from '@/api/greenhouses';
import { metricsApi } from '@/api/metrics';
import { ApiError } from '@/api/client';
import { useGreenhouses } from '@/hooks/useGreenhouses';
import { useSensors } from '@/hooks/useSensors';
import { useScope } from '@/hooks/useScope';
import { useT, useLang } from '@/i18n';
import { fmtDay, relTime } from '@/lib/format';
import type { Greenhouse } from '@/types';
import { PageHead } from '@/components/ui/PageHead';
import { Button } from '@/components/ui/Button';
import { Modal } from '@/components/ui/Modal';
import { Field, inputClass } from '@/components/ui/Field';
import { useToast } from '@/components/toast';

interface FormState {
  name: string;
  description: string;
  latitude: string;
  longitude: string;
}

const BLANK: FormState = { name: '', description: '', latitude: '', longitude: '' };

export function GreenhousesPage() {
  const t = useT();
  const queryClient = useQueryClient();
  const toast = useToast();
  const navigate = useNavigate();
  const { setGhId } = useScope();
  const { data: greenhouses = [], isLoading } = useGreenhouses();
  const { data: sensors = [] } = useSensors();

  const [editing, setEditing] = useState<'new' | Greenhouse | null>(null);
  const [confirmingDelete, setConfirmingDelete] = useState<number | null>(null);

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ['greenhouses'] });

  const saveMut = useMutation({
    mutationFn: async ({ target, form }: { target: 'new' | Greenhouse; form: FormState }) => {
      const payload = {
        name: form.name.trim(),
        description: form.description.trim(),
        latitude: form.latitude.trim() === '' ? null : parseFloat(form.latitude),
        longitude: form.longitude.trim() === '' ? null : parseFloat(form.longitude),
      };
      if (target === 'new') return greenhouseApi.create(payload);
      return greenhouseApi.update(target.id, payload);
    },
    onSuccess: (gh, { target }) => {
      invalidate();
      setEditing(null);
      toast(
        target === 'new' ? t('Greenhouse created') : t('Greenhouse saved'),
        target === 'new' ? `POST /api/greenhouses/ · #${gh.id}` : `PATCH /api/greenhouses/${gh.id}/`,
      );
    },
    onError: (err) => toast(t('Save failed'), err instanceof ApiError ? err.message : String(err)),
  });

  const deleteMut = useMutation({
    mutationFn: (id: number) => greenhouseApi.remove(id),
    onSuccess: (_, id) => {
      setConfirmingDelete(null);
      invalidate();
      queryClient.invalidateQueries({ queryKey: ['sensors'] });
      toast(t('Greenhouse deleted'), `DELETE /api/greenhouses/${id}/ · ${t('sensors cascaded')}`);
    },
    onError: (err) => toast(t('Delete failed'), err instanceof ApiError ? err.message : String(err)),
  });

  return (
    <div>
      <PageHead
        icon={Warehouse}
        title={t('Greenhouses')}
        sub={t('{n} locations · {m} sensors total', { n: greenhouses.length, m: sensors.length })}
        actions={
          <Button variant="primary" onClick={() => setEditing('new')}>
            <Plus size={15} />
            {t('Add greenhouse')}
          </Button>
        }
      />

      {greenhouses.length === 0 ? (
        <div className="card flex flex-col items-center gap-1.5 p-7 text-center">
          <Warehouse size={26} className="mb-1 opacity-75" />
          <div className="text-[13px] font-semibold">{t('No greenhouses yet')}</div>
          <div className="max-w-[240px] text-xs text-muted">
            {t('Create your first location to start attaching sensors.')}
          </div>
          <Button variant="primary" className="mt-2" onClick={() => setEditing('new')}>
            <Plus size={14} />
            {t('Add greenhouse')}
          </Button>
        </div>
      ) : (
        <div className="grid grid-cols-[repeat(auto-fill,minmax(300px,1fr))] gap-3.5">
          {greenhouses.map((g) => (
            <GreenhouseCard
              key={g.id}
              greenhouse={g}
              sensorTotal={sensors.filter((s) => s.greenhouse === g.id).length}
              sensorActive={
                sensors.filter((s) => s.greenhouse === g.id && s.is_active).length
              }
              confirmingDelete={confirmingDelete === g.id}
              onAskDelete={() => setConfirmingDelete(g.id)}
              onCancelDelete={() => setConfirmingDelete(null)}
              onConfirmDelete={() => deleteMut.mutate(g.id)}
              onEdit={() => setEditing(g)}
              onOpenDashboard={() => {
                setGhId(g.id);
                navigate('/overview');
              }}
            />
          ))}
          {isLoading && <div className="card p-6 text-center text-[13px] text-muted">…</div>}
        </div>
      )}

      {editing && (
        <GreenhouseFormModal
          target={editing}
          pending={saveMut.isPending}
          onClose={() => setEditing(null)}
          onSubmit={(form) => saveMut.mutate({ target: editing, form })}
        />
      )}
    </div>
  );
}

function GreenhouseCard({
  greenhouse: g,
  sensorTotal,
  sensorActive,
  confirmingDelete,
  onAskDelete,
  onCancelDelete,
  onConfirmDelete,
  onEdit,
  onOpenDashboard,
}: {
  greenhouse: Greenhouse;
  sensorTotal: number;
  sensorActive: number;
  confirmingDelete: boolean;
  onAskDelete: () => void;
  onCancelDelete: () => void;
  onConfirmDelete: () => void;
  onEdit: () => void;
  onOpenDashboard: () => void;
}) {
  const t = useT();
  const { lang } = useLang();
  const lastQEnabled = sensorActive > 0 || sensorTotal > 0;

  return (
    <div className="card flex flex-col" data-testid={`gh-card-${g.id}`}>
      <div className="flex items-center justify-between gap-2.5 px-4.5 pt-3.5 pb-1">
        <div className="text-[14.5px] font-semibold tracking-[-0.01em]">{g.name}</div>
        <div className="flex gap-1">
          <Button size="iconSm" aria-label={`${t('Edit')} ${g.name}`} onClick={onEdit}>
            <Pencil size={14} />
          </Button>
          {confirmingDelete ? (
            <>
              <Button variant="danger" size="sm" disabled={false} onClick={onConfirmDelete}>
                {t('Confirm')}
              </Button>
              <Button size="sm" onClick={onCancelDelete}>
                {t('Cancel')}
              </Button>
            </>
          ) : (
            <Button size="iconSm" aria-label={`${t('Delete')} ${g.name}`} onClick={onAskDelete}>
              <Trash2 size={14} />
            </Button>
          )}
        </div>
      </div>

      <div className="px-4.5 pb-4">
        <div className="mb-2.5 min-h-[17px] text-[11px] text-muted">
          {g.description || t('No description')}
        </div>

        <StatRow label={t('Location')} value={fmtCoord(g.latitude, g.longitude)} mono />
        <StatRow label={t('Sensors')} value={`${sensorActive}/${sensorTotal} ${t('active')}`} mono />
        {lastQEnabled && <LastReadingRow ghId={g.id} lang={lang} />}
        <StatRow label={t('Created')} value={fmtDay(g.created_at, lang)} mono />

        <div className="mt-3 flex gap-2">
          <Button variant="primary" size="sm" onClick={onOpenDashboard}>
            {t('Open dashboard')}
          </Button>
        </div>
      </div>
    </div>
  );
}

function StatRow({ label, value, mono }: { label: string; value: string; mono?: boolean }) {
  return (
    <div className="flex items-center justify-between gap-2.5 border-t border-border py-2 text-[12.5px] first:border-t-0 first:pt-0">
      <span className="text-muted">{label}</span>
      <span className={mono ? 'mono font-semibold' : 'font-semibold'}>{value}</span>
    </div>
  );
}

function LastReadingRow({ ghId, lang }: { ghId: number; lang: string }) {
  const t = useT();
  const { data } = useQuery({
    queryKey: ['gh-latest', ghId],
    queryFn: () => metricsApi.latestSnapshot(ghId),
    staleTime: 30_000,
  });
  let last: string | null = null;
  for (const s of data?.sensors ?? []) {
    if (s.latest_measurement) {
      const time = new Date(s.latest_measurement.measurement_time).getTime();
      if (!last || time > new Date(last).getTime()) last = s.latest_measurement.measurement_time;
    }
  }
  return <StatRow label={t('Last reading')} value={last ? relTime(last, lang) : '—'} mono />;
}

function fmtCoord(la: number | null, lo: number | null): string {
  return la == null || lo == null ? '—' : `${la.toFixed(4)}, ${lo.toFixed(4)}`;
}

function GreenhouseFormModal({
  target,
  pending,
  onClose,
  onSubmit,
}: {
  target: 'new' | Greenhouse;
  pending: boolean;
  onClose: () => void;
  onSubmit: (form: FormState) => void;
}) {
  const t = useT();
  const isEdit = target !== 'new';
  const [form, setForm] = useState<FormState>(
    isEdit
      ? {
          name: target.name,
          description: target.description ?? '',
          latitude: target.latitude == null ? '' : String(target.latitude),
          longitude: target.longitude == null ? '' : String(target.longitude),
        }
      : BLANK,
  );
  const [errors, setErrors] = useState<Partial<Record<keyof FormState, string>>>({});

  const numOrNaN = (v: string) => (v.trim() === '' ? NaN : parseFloat(v));

  const submit = (e: FormEvent) => {
    e.preventDefault();
    const errs: Partial<Record<keyof FormState, string>> = {};
    if (!form.name.trim()) errs.name = t('Name is required.');
    if (isNaN(numOrNaN(form.latitude))) errs.latitude = t('Must be a number.');
    if (isNaN(numOrNaN(form.longitude))) errs.longitude = t('Must be a number.');
    setErrors(errs);
    if (Object.keys(errs).length) return;
    onSubmit(form);
  };

  return (
    <Modal
      title={isEdit ? t('Edit greenhouse') : t('Add greenhouse')}
      onClose={onClose}
      footer={
        <>
          <Button onClick={onClose}>{t('Cancel')}</Button>
          <Button variant="primary" disabled={pending} onClick={submit}>
            {isEdit ? t('Save changes') : t('Create greenhouse')}
          </Button>
        </>
      }
    >
      <form onSubmit={submit}>
        <Field label={t('Name')} required error={errors.name} htmlFor="gh-name">
          <input
            id="gh-name"
            className={inputClass(errors.name)}
            autoFocus
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
            placeholder={t('North Tunnel')}
          />
        </Field>
        <Field label={t('Description')} hint={t('Up to 300 characters')} htmlFor="gh-desc">
          <input
            id="gh-desc"
            className={inputClass()}
            value={form.description}
            onChange={(e) => setForm({ ...form, description: e.target.value })}
            placeholder={t('What grows here?')}
          />
        </Field>
        <div className="flex gap-2.5">
          <div className="flex-1">
            <Field label={t('Latitude')} error={errors.latitude} htmlFor="gh-lat">
              <input
                id="gh-lat"
                className={inputClass(errors.latitude)}
                value={form.latitude}
                onChange={(e) => setForm({ ...form, latitude: e.target.value })}
                placeholder="52.0928"
                inputMode="decimal"
              />
            </Field>
          </div>
          <div className="flex-1">
            <Field label={t('Longitude')} error={errors.longitude} htmlFor="gh-lng">
              <input
                id="gh-lng"
                className={inputClass(errors.longitude)}
                value={form.longitude}
                onChange={(e) => setForm({ ...form, longitude: e.target.value })}
                placeholder="5.1044"
                inputMode="decimal"
              />
            </Field>
          </div>
        </div>
        <button type="submit" hidden />
      </form>
    </Modal>
  );
}
