import { useAuth } from '@/hooks/useAuth';
import { useT } from '@/i18n';

export function DashboardPlaceholder() {
  const { user, logout } = useAuth();
  const t = useT();

  return (
    <div className="flex min-h-full flex-col items-center justify-center gap-3 bg-bg px-5">
      <h1 className="font-display text-xl font-semibold tracking-[-0.02em]">
        {t('Welcome')}, {user?.first_name || user?.username}
      </h1>
      <p className="text-[13px] text-muted">App shell arrives in cycle 2.</p>
      <button
        type="button"
        onClick={logout}
        className="rounded-lg border border-border bg-surface px-3 py-1.5 text-[13px] font-medium text-fg-subtle transition-colors hover:bg-surface-alt hover:text-fg"
      >
        {t('Sign out')}
      </button>
    </div>
  );
}
