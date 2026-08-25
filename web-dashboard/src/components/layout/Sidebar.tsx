import { NavLink } from 'react-router';
import { LogOut } from 'lucide-react';
import { useAuth } from '@/hooks/useAuth';
import { useT } from '@/i18n';
import { LogoMark } from '@/components/brand/LogoMark';
import { NAV_ITEMS } from '@/components/layout/nav-items';

function initials(user: { username: string; first_name: string; last_name: string }): string {
  const first = user.first_name || user.username;
  return (first[0] + (user.last_name ? user.last_name[0] : '')).toUpperCase();
}

export function Sidebar() {
  const { user, logout } = useAuth();
  const t = useT();
  if (!user) return null;

  return (
    <aside className="flex w-[230px] shrink-0 flex-row items-center gap-0.5 overflow-x-auto border-b border-border px-3.5 py-2.5 md:h-full md:flex-col md:border-r md:border-b-0 md:px-3 md:py-4">
      <NavLink
        to="/overview"
        className="flex shrink-0 items-center gap-2.5 rounded-lg px-2 py-1.5 md:mb-3.5"
        aria-label="terraGEM home"
      >
        <span className="grid h-[30px] w-[30px] place-items-center rounded-lg bg-accent">
          <LogoMark size={19} />
        </span>
        <span className="hidden text-left leading-tight md:block">
          <span className="font-display block text-[17px] tracking-[-0.02em]">
            terra<b className="font-bold">GEM</b>
          </span>
          <span className="mt-0.5 block max-w-[150px] text-[9.5px] leading-[1.3] tracking-[0.08em] uppercase text-muted">
            {t('Greenhouse Environment Management')}
          </span>
        </span>
      </NavLink>

      <nav className="flex flex-row gap-0.5 md:flex-1 md:flex-col" aria-label={t('Primary')}>
        {NAV_ITEMS.map((item) => (
          <NavLink
            key={item.key}
            to={item.path}
            className={({ isActive }) =>
              `flex items-center gap-2.5 rounded-lg px-2.5 py-2 text-[13px] font-medium whitespace-nowrap transition-colors ${
                isActive ? 'bg-accent-soft text-accent' : 'text-fg-subtle hover:bg-surface-alt hover:text-fg'
              }`
            }
          >
            <item.icon size={17} strokeWidth={1.6} className="shrink-0" />
            <span className="hidden md:inline">{t(item.labelKey)}</span>
          </NavLink>
        ))}
      </nav>

      <div className="hidden w-full items-center gap-2.5 border-t border-border px-2 pt-3 pb-1.5 mt-auto md:flex">
        <span className="grid h-7 w-7 shrink-0 place-items-center rounded-full border border-border bg-accent-soft text-[11px] font-semibold text-accent">
          {initials(user)}
        </span>
        <div className="min-w-0 flex-1">
          <div className="text-[12.5px] leading-tight font-semibold">{user.first_name || user.username}</div>
          <div className="truncate text-[10.5px] text-muted">{user.email}</div>
        </div>
        <button
          type="button"
          onClick={logout}
          aria-label={t('Sign out')}
          title={t('Sign out')}
          className="rounded-md p-1.5 text-muted transition-colors hover:bg-surface-alt hover:text-danger"
        >
          <LogOut size={14} strokeWidth={1.8} />
        </button>
      </div>
    </aside>
  );
}
