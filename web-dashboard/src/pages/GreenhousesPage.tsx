import { useT } from '@/i18n';
import { PageHead } from '@/components/ui/PageHead';
import { Warehouse, Plus } from 'lucide-react';
import { useGreenhouses } from '@/hooks/useGreenhouses';

export function GreenhousesPage() {
  const t = useT();
  const { data: greenhouses = [] } = useGreenhouses();

  return (
    <div>
      <PageHead
        icon={Warehouse}
        title={t('Greenhouses')}
        sub={`${greenhouses.length}`}
        actions={
          <button
            type="button"
            className="inline-flex items-center gap-1.5 rounded-lg border border-accent bg-accent px-3 py-1.5 text-[13px] font-medium text-white transition-colors hover:bg-accent-hover"
          >
            <Plus size={15} />
            {t('Add greenhouse')}
          </button>
        }
      />
      <div className="rounded-xl border border-border bg-surface p-8 text-center text-[13px] text-muted">
        Cycle 4: greenhouse grid, create/edit modal, delete confirmation.
      </div>
    </div>
  );
}
