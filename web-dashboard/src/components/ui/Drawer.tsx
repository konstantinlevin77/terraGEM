import { useEffect, type ReactNode } from 'react';

interface DrawerProps {
  onClose: () => void;
  label: string;
  children: ReactNode;
}

export function Drawer({ onClose, label, children }: DrawerProps) {
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, [onClose]);

  return (
    <div className="fixed inset-0 z-60">
      <div
        className="absolute inset-0 bg-[oklch(20%_0.02_255/0.32)]"
        onMouseDown={onClose}
      />
      <aside
        role="dialog"
        aria-modal="true"
        aria-label={label}
        className="absolute top-0 right-0 bottom-0 w-[min(430px,94vw)] overflow-y-auto border-l border-border bg-surface shadow-[var(--shadow-pop)]"
      >
        {children}
      </aside>
    </div>
  );
}
