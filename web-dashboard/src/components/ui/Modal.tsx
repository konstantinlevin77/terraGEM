import { useEffect, type ReactNode } from 'react';
import { X } from 'lucide-react';
import { Button } from '@/components/ui/Button';

interface ModalProps {
  title: string;
  onClose: () => void;
  footer?: ReactNode;
  children: ReactNode;
}

export function Modal({ title, onClose, footer, children }: ModalProps) {
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, [onClose]);

  return (
    <div
      className="fixed inset-0 z-60 flex items-start justify-center bg-[oklch(20%_0.02_255/0.42)] px-5 pt-[9vh] pb-5 backdrop-blur-[2px]"
      onMouseDown={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-label={title}
        className="max-h-[82vh] w-full max-w-[470px] overflow-y-auto rounded-2xl border border-border bg-surface shadow-[var(--shadow-pop)]"
      >
        <div className="flex items-center justify-between border-b border-border px-5 py-3.5">
          <div className="text-[15px] font-semibold tracking-[-0.01em]">{title}</div>
          <Button variant="default" size="icon" aria-label="Close dialog" onClick={onClose}>
            <X size={15} />
          </Button>
        </div>
        <div className="px-5 pt-4.5 pb-2">{children}</div>
        <div className="flex justify-end gap-2 border-t border-border px-5 py-3.5">{footer}</div>
      </div>
    </div>
  );
}
