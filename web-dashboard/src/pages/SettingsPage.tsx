import { useQuery } from '@tanstack/react-query';
import { Settings as SettingsIcon, LogOut } from 'lucide-react';
import { authApi } from '@/api/auth';
import { useAuth } from '@/hooks/useAuth';
import { useLang, useT } from '@/i18n';
import { PageHead } from '@/components/ui/PageHead';
import { Button } from '@/components/ui/Button';
import { Field, inputClass } from '@/components/ui/Field';
import { cn } from '@/lib/utils';

export function SettingsPage() {
  const t = useT();
  const { user, logout } = useAuth();

  const meQ = useQuery({
    queryKey: ['me'],
    queryFn: authApi.me,
    staleTime: 5 * 60_000,
    initialData: user ?? undefined,
  });
  const profile = meQ.data ?? user;

  return (
    <div>
      <PageHead icon={SettingsIcon} title={t('Settings')} sub={t('Profile, language and session')} />

      <div className="mb-3.5 grid grid-cols-1 items-start gap-3.5 lg:grid-cols-2">
        <div className="card">
          <div className="flex items-center justify-between border-b border-border px-4.5 py-3">
            <div className="text-[13.5px] font-semibold tracking-[-0.01em]">{t('Profile')}</div>
            <div className="mono text-[11.5px] text-muted">GET /api/auth/me/</div>
          </div>
          <div className="p-4.5 pb-1">
            <Field label={t('Username')} htmlFor="set-username">
              <input id="set-username" className={cn(inputClass(), 'mono bg-surface-alt')} readOnly value={profile?.username ?? ''} />
            </Field>
            <Field label={t('Email')} htmlFor="set-email">
              <input id="set-email" className={cn(inputClass(), 'mono bg-surface-alt')} readOnly value={profile?.email ?? ''} />
            </Field>
            <div className="flex gap-2.5">
              <div className="flex-1">
                <Field label={t('First name')} htmlFor="set-fname">
                  <input id="set-fname" className={cn(inputClass(), 'bg-surface-alt')} readOnly value={profile?.first_name ?? ''} />
                </Field>
              </div>
              <div className="flex-1">
                <Field label={t('Last name')} htmlFor="set-lname">
                  <input id="set-lname" className={cn(inputClass(), 'bg-surface-alt')} readOnly value={profile?.last_name ?? ''} />
                </Field>
              </div>
            </div>
            <Field label={t('Company')} htmlFor="set-company">
              <input id="set-company" className={cn(inputClass(), 'bg-surface-alt')} readOnly value={profile?.company ?? ''} />
            </Field>
            <Field label={t('Phone')} htmlFor="set-phone" hint={t('Editable profile fields will map to PATCH /api/auth/me/ later.')}>
              <input id="set-phone" className={cn(inputClass(), 'mono bg-surface-alt')} readOnly value={profile?.phone_number ?? ''} />
            </Field>
          </div>
        </div>

        <div className="flex flex-col gap-3.5">
          <div className="card">
            <div className="flex items-center justify-between border-b border-border px-4.5 py-3">
              <div className="text-[13.5px] font-semibold tracking-[-0.01em]">{t('Language')}</div>
              <div className="text-[11.5px] text-muted">{t('Applies instantly · stored in this browser')}</div>
            </div>
            <div className="flex gap-2 p-4.5 pt-4">
              <LangButton lang="en" />
              <LangButton lang="tr" />
            </div>
          </div>

          <div className="card">
            <div className="flex items-center justify-between border-b border-border px-4.5 py-3">
              <div className="text-[13.5px] font-semibold tracking-[-0.01em]">{t('Session')}</div>
              <div className="mono text-[11.5px] text-muted">JWT · Bearer</div>
            </div>
            <div className="p-4.5">
              <div className="flex items-center justify-between border-t border-border py-2 text-[12.5px] first:border-t-0 first:pt-0">
                <span className="text-muted">{t('Signed in as')}</span>
                <span className="mono font-semibold">{user?.username}</span>
              </div>
              <div className="flex items-center justify-between border-t border-border py-2 text-[12.5px]">
                <span className="text-muted">{t('Token storage')}</span>
                <span>{t('This browser (localStorage)')}</span>
              </div>
              <Button
                variant="danger"
                className="mt-3"
                onClick={logout}
              >
                <LogOut size={14} />
                {t('Sign out')}
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function LangButton({ lang: target }: { lang: 'en' | 'tr' }) {
  const { lang, setLang } = useLang();
  return (
    <button
      type="button"
      aria-pressed={lang === target}
      onClick={() => setLang(target)}
      className={cn(
        'inline-flex items-center gap-1.5 rounded-lg border px-3 py-1.5 text-[13px] font-medium transition-colors',
        lang === target
          ? 'border-accent bg-accent text-white'
          : 'border-border bg-surface text-fg-subtle hover:bg-surface-alt hover:text-fg',
      )}
    >
      {target === 'en' ? 'English' : 'Türkçe'}
    </button>
  );
}
