import { useT } from '@/i18n';
import { PageHead } from '@/components/ui/PageHead';
import { Settings as SettingsIcon } from 'lucide-react';

export function SettingsPage() {
  const t = useT();

  return (
    <div>
      <PageHead icon={SettingsIcon} title={t('Settings')} />
      <div className="rounded-xl border border-border bg-surface p-8 text-center text-[13px] text-muted">
        Cycle 7: profile, alert thresholds, language.
      </div>
    </div>
  );
}
