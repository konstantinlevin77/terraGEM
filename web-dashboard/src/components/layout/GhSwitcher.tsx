import { useEffect, useRef, useState } from 'react';
import { useGreenhouses } from '@/hooks/useGreenhouses';
import { useActiveGh } from '@/hooks/useActiveGh';
import { useT } from '@/i18n';
import { Warehouse, ChevronDown, Check } from 'lucide-react';

export function GhSwitcher() {
  const { ghId, greenhouse, setGhId } = useActiveGh();
  const { data: greenhouses = [] } = useGreenhouses();
  const t = useT();
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const onDown = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setOpen(false);
    };
    document.addEventListener('mousedown', onDown);
    document.addEventListener('keydown', onKey);
    return () => {
      document.removeEventListener('mousedown', onDown);
      document.removeEventListener('keydown', onKey);
    };
  }, [open]);

  return (
    <div className="relative" ref={ref}>
      <button
        type="button"
        aria-haspopup="listbox"
        aria-expanded={open}
        onClick={() => setOpen((o) => !o)}
        className="inline-flex items-center gap-1.5 rounded-lg border border-border bg-surface px-3 py-1.5 text-[13px] font-medium whitespace-nowrap text-fg-subtle transition-colors hover:bg-surface-alt hover:text-fg"
      >
        <Warehouse size={15} strokeWidth={1.6} />
        <span className="max-w-[150px] truncate">
          {greenhouse ? greenhouse.name : t('Choose greenhouse')}
        </span>
        <ChevronDown size={13} strokeWidth={2} />
      </button>

      {open && (
        <div
          role="listbox"
          aria-label={t('Choose greenhouse')}
          className="absolute top-full left-0 z-50 mt-1.5 min-w-[236px] rounded-[10px] border border-border-strong bg-surface p-1.5 shadow-[var(--shadow-pop)]"
        >
          {greenhouses.map((g) => (
            <button
              key={g.id}
              role="option"
              aria-selected={g.id === ghId}
              onClick={() => {
                setGhId(g.id);
                setOpen(false);
              }}
              className={`flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-left text-[13px] transition-colors ${
                g.id === ghId ? 'font-medium text-accent' : 'text-fg hover:bg-surface-alt'
              }`}
            >
              <span className="grid w-4 shrink-0 place-items-center">
                {g.id === ghId && <Check size={14} strokeWidth={2.2} />}
              </span>
              <span className="truncate">{g.name}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
