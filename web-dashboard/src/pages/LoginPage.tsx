import { useState, type FormEvent } from 'react';
import { useLocation, useNavigate } from 'react-router';
import { useAuth } from '@/hooks/useAuth';
import { useLang, useT } from '@/i18n';
import { ApiError } from '@/api/client';
import { LogoMark } from '@/components/brand/LogoMark';

export function LoginPage() {
  const { login } = useAuth();
  const t = useT();
  const { lang, setLang } = useLang();
  const navigate = useNavigate();
  const location = useLocation();

  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  const from = (location.state as { from?: string } | null)?.from ?? '/';

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!username.trim() || !password || pending) return;
    setError(null);
    setPending(true);
    try {
      await login(username.trim(), password);
      navigate(from, { replace: true });
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) {
        setError(t('Invalid username or password.'));
      } else {
        setError(t('Connection error. Is the API running?'));
      }
    } finally {
      setPending(false);
    }
  };

  return (
    <div className="flex min-h-full items-center justify-center bg-bg px-5">
      <div className="w-full max-w-sm">
        <div className="mb-6 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <span className="grid h-[30px] w-[30px] place-items-center rounded-lg bg-accent">
              <LogoMark size={19} />
            </span>
            <div className="leading-tight">
              <span className="font-display text-[17px] tracking-[-0.02em]">
                terra<b className="font-bold">GEM</b>
              </span>
              <span className="block text-[9.5px] uppercase tracking-[0.08em] text-muted">
                {t('Greenhouse Environment Management')}
              </span>
            </div>
          </div>
          <div className="flex gap-1" role="group" aria-label="Language">
            {(['en', 'tr'] as const).map((l) => (
              <button
                key={l}
                type="button"
                aria-pressed={lang === l}
                onClick={() => setLang(l)}
                className={`rounded-md border px-2 py-1 text-[11px] font-medium uppercase transition-colors ${
                  lang === l
                    ? 'border-accent bg-accent-soft text-accent'
                    : 'border-border text-muted hover:text-fg'
                }`}
              >
                {l}
              </button>
            ))}
          </div>
        </div>

        <form
          onSubmit={onSubmit}
          className="rounded-xl border border-border bg-surface p-6"
          aria-labelledby="login-title"
        >
          <h1 id="login-title" className="font-display text-[17px] font-semibold tracking-[-0.01em]">
            {t('Sign in')}
          </h1>
          <p className="mt-1 mb-5 text-[12.5px] text-muted">{t('Sign in to your greenhouse dashboard')}</p>

          <div className="mb-3.5 flex flex-col gap-1.5">
            <label htmlFor="login-username" className="text-xs font-semibold text-fg-subtle">
              {t('Username')}
            </label>
            <input
              id="login-username"
              className="w-full rounded-lg border border-border-strong bg-surface px-3 py-2 text-[13.5px] outline-none transition-colors focus:border-accent-ring focus:shadow-[0_0_0_3px_oklch(60%_0.11_152/0.18)]"
              autoComplete="username"
              autoFocus
              value={username}
              onChange={(e) => setUsername(e.target.value)}
            />
          </div>

          <div className="mb-4 flex flex-col gap-1.5">
            <label htmlFor="login-password" className="text-xs font-semibold text-fg-subtle">
              {t('Password')}
            </label>
            <input
              id="login-password"
              type="password"
              className="w-full rounded-lg border border-border-strong bg-surface px-3 py-2 text-[13.5px] outline-none transition-colors focus:border-accent-ring focus:shadow-[0_0_0_3px_oklch(60%_0.11_152/0.18)]"
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>

          {error && (
            <p role="alert" className="mb-4 text-[11.5px] text-danger">
              {error}
            </p>
          )}

          <button
            type="submit"
            disabled={pending || !username.trim() || !password}
            className="inline-flex w-full items-center justify-center gap-2 rounded-lg bg-accent px-3 py-2 text-[13px] font-medium text-white transition-colors hover:bg-accent-hover disabled:cursor-not-allowed disabled:opacity-50"
          >
            {pending ? `${t('Signing in…')}` : t('Sign in')}
          </button>
        </form>
      </div>
    </div>
  );
}
