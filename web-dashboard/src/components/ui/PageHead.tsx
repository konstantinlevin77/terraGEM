import type { LucideIcon } from 'lucide-react';

interface PageHeadProps {
  icon: LucideIcon;
  title: string;
  sub?: string;
  actions?: React.ReactNode;
}

export function PageHead({ icon: Icon, title, sub, actions }: PageHeadProps) {
  return (
    <div className="mb-5 flex flex-wrap items-end justify-between gap-4">
      <div>
        <h1 className="font-display text-[21px] font-semibold tracking-[-0.02em]">{title}</h1>
        <div className="mt-0.5 flex flex-wrap items-center gap-1.5 text-[13px] text-muted">
          {Icon && <Icon size={13} strokeWidth={1.6} />}
          {sub && <span>{sub}</span>}
        </div>
      </div>
      {actions && <div className="flex flex-wrap items-center gap-2">{actions}</div>}
    </div>
  );
}
