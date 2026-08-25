import { cn } from '@/lib/utils';
import type { ButtonHTMLAttributes } from 'react';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'default' | 'primary' | 'danger';
  size?: 'md' | 'sm' | 'icon' | 'iconSm';
}

const BASE =
  'inline-flex items-center justify-center gap-1.5 rounded-lg border font-medium whitespace-nowrap transition-colors disabled:cursor-not-allowed disabled:opacity-50';

const VARIANTS = {
  default:
    'border-border bg-surface text-fg-subtle hover:bg-surface-alt hover:border-border-strong hover:text-fg',
  primary: 'border-accent bg-accent text-white hover:bg-accent-hover hover:border-accent-hover',
  danger: 'border-[oklch(88%_0.04_25)] bg-surface text-danger hover:bg-danger-soft',
} as const;

const SIZES = {
  md: 'px-3 py-1.5 text-[13px]',
  sm: 'px-2.5 py-1 text-[12.5px]',
  icon: 'p-1.5 rounded-[7px]',
  iconSm: 'p-1 rounded-[7px]',
} as const;

export function Button({ variant = 'default', size = 'md', className, type, ...props }: ButtonProps) {
  return (
    <button
      type={type ?? 'button'}
      className={cn(BASE, VARIANTS[variant], SIZES[size], className)}
      {...props}
    />
  );
}
