import type { ReactNode } from 'react';

interface FieldProps {
  label: string;
  required?: boolean;
  hint?: string;
  error?: string;
  htmlFor?: string;
  children: ReactNode;
}

export function Field({ label, required, hint, error, htmlFor, children }: FieldProps) {
  return (
    <div className="mb-3.5 flex flex-col gap-1.5">
      <label htmlFor={htmlFor} className="text-xs font-semibold text-fg-subtle">
        {label}
        {required && <span className="text-danger"> *</span>}
      </label>
      {children}
      {error ? (
        <span className="text-[11.5px] text-danger">{error}</span>
      ) : hint ? (
        <span className="text-[11px] text-muted">{hint}</span>
      ) : null}
    </div>
  );
}

export const inputClass = (error?: string) =>
  `w-full rounded-lg border bg-surface px-3 py-2 text-[13.5px] outline-none transition-colors focus:border-accent-ring focus:shadow-[0_0_0_3px_oklch(60%_0.11_152/0.18)] ${
    error ? 'border-danger' : 'border-border-strong'
  }`;
