import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from 'react';

const GH_KEY = 'tg.gh';
const LIVE_KEY = 'tg.live';

interface ScopeContextValue {
  ghId: number;
  setGhId: (id: number) => void;
  live: boolean;
  setLive: (on: boolean) => void;
}

const ScopeContext = createContext<ScopeContextValue | null>(null);

function initialGh(): number {
  const v = localStorage.getItem(GH_KEY);
  return v ? Number(v) || 0 : 0;
}

function initialLive(): boolean {
  return localStorage.getItem(LIVE_KEY) !== 'false';
}

export function ScopeProvider({ children }: { children: ReactNode }) {
  const [ghId, setGhIdRaw] = useState(initialGh);
  const [live, setLiveRaw] = useState(initialLive);

  useEffect(() => {
    localStorage.setItem(GH_KEY, String(ghId));
  }, [ghId]);

  useEffect(() => {
    localStorage.setItem(LIVE_KEY, String(live));
  }, [live]);

  const setGhId = useCallback((id: number) => setGhIdRaw(id), []);
  const setLive = useCallback((on: boolean) => setLiveRaw(on), []);

  const value = useMemo(() => ({ ghId, setGhId, live, setLive }), [ghId, setGhId, live, setLive]);

  return <ScopeContext.Provider value={value}>{children}</ScopeContext.Provider>;
}

export function useScope(): ScopeContextValue {
  const ctx = useContext(ScopeContext);
  if (!ctx) throw new Error('useScope must be used within ScopeProvider');
  return ctx;
}
