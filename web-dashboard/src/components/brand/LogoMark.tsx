export function LogoMark({ size = 18 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path d="M12 21v-7" stroke="#fff" strokeWidth="1.8" strokeLinecap="round" />
      <path d="M12 14.2C7.2 14.2 4.8 11 4.8 5.6 9.6 5.6 12 8.8 12 14.2Z" fill="#fff" />
      <path d="M12 11.4c0-4 2.6-5.8 7.2-5.8 0 4.6-2.6 5.8-7.2 5.8Z" fill="#fff" opacity=".65" />
    </svg>
  );
}
