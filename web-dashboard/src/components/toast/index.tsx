import { createContext, useCallback, useContext, useState, type ReactNode } from 'react';
import { Check } from 'lucide-react';

interface Toast {
  id: number;
  title: string;
  sub?: string;
}

type PushToast = (title: string, sub?: string) => void;

const ToastContext = createContext<PushToast>(() => {});

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const push = useCallback<PushToast>((title, sub) => {
    const id = Date.now() + Math.random();
    setToasts((ts) => [...ts, { id, title, sub }]);
    setTimeout(() => {
      setToasts((ts) => ts.filter((t) => t.id !== id));
    }, 4200);
  }, []);

  return (
    <ToastContext.Provider value={push}>
      {children}
      <div className="fixed right-5 bottom-5 z-90 flex w-[min(340px,calc(100vw-40px))] flex-col gap-2" aria-live="polite">
        {toasts.map((t) => (
          <div
            key={t.id}
            className="flex items-start gap-2.5 rounded-xl bg-fg px-3.5 py-3 text-ok-soft shadow-[var(--shadow-pop)]"
          >
            <Check size={15} strokeWidth={2.2} className="mt-0.5 shrink-0 opacity-90" />
            <div className="min-w-0">
              <div className="text-[13px] leading-snug font-semibold">{t.title}</div>
              {t.sub && <div className="mono mt-0.5 text-[11px] opacity-70">{t.sub}</div>}
            </div>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast(): PushToast {
  return useContext(ToastContext);
}
