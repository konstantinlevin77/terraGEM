import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from 'react';
import { en } from '@/i18n/dictionaries/en';
import { tr } from '@/i18n/dictionaries/tr';

export type Lang = 'en' | 'tr';

const LANG_KEY = 'tg.lang';
const DICTS: Record<Lang, Record<string, string>> = { en, tr };

interface I18nContextValue {
  lang: Lang;
  setLang: (lang: Lang) => void;
  t: (key: string, vars?: Record<string, string | number>) => string;
}

const I18nContext = createContext<I18nContextValue | null>(null);

function initialLang(): Lang {
  const stored = localStorage.getItem(LANG_KEY);
  return stored === 'tr' ? 'tr' : 'en';
}

export function I18nProvider({ children }: { children: ReactNode }) {
  const [lang, setLangRaw] = useState<Lang>(initialLang);

  const setLang = useCallback((next: Lang) => {
    setLangRaw(next);
    localStorage.setItem(LANG_KEY, next);
  }, []);

  useEffect(() => {
    document.documentElement.lang = lang;
  }, [lang]);

  const t = useCallback(
    (key: string, vars?: Record<string, string | number>) => {
      let out = DICTS[lang][key] ?? en[key as keyof typeof en] ?? key;
      if (vars) {
        for (const [k, v] of Object.entries(vars)) {
          out = out.split(`{${k}}`).join(String(v));
        }
      }
      return out;
    },
    [lang],
  );

  const value = useMemo(() => ({ lang, setLang, t }), [lang, setLang, t]);

  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}

export function useT(): I18nContextValue['t'] {
  const ctx = useContext(I18nContext);
  if (!ctx) throw new Error('useT must be used within I18nProvider');
  return ctx.t;
}

export function useLang(): Pick<I18nContextValue, 'lang' | 'setLang'> {
  const ctx = useContext(I18nContext);
  if (!ctx) throw new Error('useLang must be used within I18nProvider');
  return { lang: ctx.lang, setLang: ctx.setLang };
}
