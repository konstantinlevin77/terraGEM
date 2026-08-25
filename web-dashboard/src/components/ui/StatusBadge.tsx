import { Check } from 'lucide-react';
import { useT } from '@/i18n';

export type StatusLevel = 'ok' | 'watch' | 'crit' | 'neutral';

const CLASSES: Record<StatusLevel, string> = {
  ok: 'bg-ok-soft text-ok',
  watch: 'bg-warn-soft text-warn',
  crit: 'bg-danger-soft text-danger',
  neutral: 'bg-surface-alt text-muted',
};

const LABEL_KEYS: Record<StatusLevel, string> = {
  ok: 'Optimal',
  watch: 'Watch',
  crit: 'Critical',
  neutral: '—',
};

export function StatusBadge({ status, text }: { status: StatusLevel; text?: string }) {
  const t = useT();
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10.5px] font-semibold tracking-[0.03em] whitespace-nowrap ${CLASSES[status]}`}
    >
      {status === 'ok' && <Check size={10} strokeWidth={2.6} />}
      {text ?? t(LABEL_KEYS[status])}
    </span>
  );
}
