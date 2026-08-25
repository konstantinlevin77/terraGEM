import { useGreenhouses } from '@/hooks/useGreenhouses';
import { useScope } from '@/hooks/useScope';
import { useT } from '@/i18n';
import { PageHead } from '@/components/ui/PageHead';
import { LayoutDashboard } from 'lucide-react';

export function OverviewPage() {
  const t = useT();
  const { ghId } = useScope();
  const { data: greenhouses = [] } = useGreenhouses();
  const gh = greenhouses.find((g) => g.id === ghId);

  return (
    <div>
      <PageHead
        icon={LayoutDashboard}
        title={t('Overview')}
        sub={gh ? `${gh.name} · ${gh.latitude ?? '—'}, ${gh.longitude ?? '—'}` : t('All greenhouses · portfolio average')}
      />
      <div className="rounded-xl border border-border bg-surface p-8 text-center text-[13px] text-muted">
        Cycle 3: KPI cards, trend chart, alerts, today summary, latest readings.
      </div>
    </div>
  );
}
