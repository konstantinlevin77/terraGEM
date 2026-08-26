import type { ButtonHTMLAttributes } from 'react';

interface SwitchProps extends Omit<ButtonHTMLAttributes<HTMLButtonElement>, 'onChange'> {
  checked: boolean;
  onChange: (checked: boolean) => void;
  label: string;
}

export function Switch({ checked, onChange, label, ...props }: SwitchProps) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      aria-label={label}
      onClick={() => onChange(!checked)}
      className={`relative h-5 w-[34px] shrink-0 rounded-full border-none p-0 transition-colors duration-150 ${
        checked ? 'bg-accent' : 'bg-[oklch(87%_0.006_250)]'
      }`}
      {...props}
    >
      <span
        className={`absolute top-0.5 left-0.5 h-4 w-4 rounded-full bg-white shadow-[0_1px_2px_oklch(20%_0.02_255/0.3)] transition-transform duration-150 ${
          checked ? 'translate-x-3.5' : ''
        }`}
      />
    </button>
  );
}
