import { useLocation } from 'react-router';
import { Pause, Play } from 'lucide-react';
import { useScope } from '@/hooks/useScope';
import { useT } from '@/i18n';
import { GhSwitcher } from '@/components/layout/GhSwitcher';
import { NAV_ITEMS } from '@/components/layout/nav-items';

function useCurrentTitle(): string {
  const { pathname } = useLocation();
  const t = useT();
  const item = NAV_ITEMS.find((n) => pathname.startsWith(n.path));
  return t(item ? item.labelKey : 'Overview');
}

export function Topbar() {
  const t = useT();
  const { live, setLive } = useScope();
  const title = useCurrentTitle();

  return (
    <header className="sticky top-0 z-30 flex flex-wrap items-center gap-3 border-b border-border bg-bg/85 px-4 py-2.5 backdrop-blur-xl md:px-7">
      <span className="text-[13px] font-semibold tracking-[-0.01em]">{title}</span>
      <div className="ml-auto flex flex-wrap items-center gap-2.5">
        <button
          type="button"
          aria-pressed={live}
          onClick={() => setLive(!live)}
          className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[11px] font-semibold transition-colors ${
            live
              ? 'border-border text-fg-subtle hover:bg-surface-alt'
              : 'border-border bg-surface-alt text-muted'
          }`}
        >
          <span className={`h-[7px] w-[7px] rounded-full ${live ? 'animate-pulse bg-ok' : 'bg-muted'}`} />
          {t(live ? 'Live feed' : 'Paused')}
          {live ? <Pause size={11} strokeWidth={2} /> : <Play size={11} strokeWidth={2} />}
        </button>
        <GhSwitcher />
      </div>
    </header>
  );
}
