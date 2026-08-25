import { useT } from '@/i18n';
import { sensorMeta } from '@/lib/sensorMeta';
import type { SensorType } from '@/types';

export function TypePill({ type }: { type: SensorType }) {
  const t = useT();
  const m = sensorMeta(type);
  return (
    <span
      className="inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[11px] font-medium whitespace-nowrap"
      style={{
        background: `color-mix(in oklab, ${m.color} 9%, white)`,
        color: m.color,
        border: `1px solid color-mix(in oklab, ${m.color} 22%, white)`,
      }}
    >
      {t(m.shortKey)}
    </span>
  );
}
