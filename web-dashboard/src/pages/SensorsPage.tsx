import { useT } from '@/i18n';
import { PageHead } from '@/components/ui/PageHead';
import { Cpu, Plus } from 'lucide-react';

export function SensorsPage() {
  const t = useT();

  return (
    <div>
      <PageHead
        icon={Cpu}
        title={t('Sensors')}
        actions={
          <button
            type="button"
            className="inline-flex items-center gap-1.5 rounded-lg border border-accent bg-accent px-3 py-1.5 text-[13px] font-medium text-white transition-colors hover:bg-accent-hover"
          >
            <Plus size={15} />
            {t('Add sensor')}
          </button>
        }
      />
      <div className="rounded-xl border border-border bg-surface p-8 text-center text-[13px] text-muted">
        Cycle 5: sensor table, filters, add modal, detail drawer.
      </div>
    </div>
  );
}
