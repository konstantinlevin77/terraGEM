import { useT } from '@/i18n';
import { PageHead } from '@/components/ui/PageHead';
import { History as HistoryIcon } from 'lucide-react';

export function HistoryPage() {
  const t = useT();

  return (
    <div>
      <PageHead icon={HistoryIcon} title={t('History')} />
      <div className="rounded-xl border border-border bg-surface p-8 text-center text-[13px] text-muted">
        Cycle 6: measurement explorer, chart, paginated table, CSV export.
      </div>
    </div>
  );
}
