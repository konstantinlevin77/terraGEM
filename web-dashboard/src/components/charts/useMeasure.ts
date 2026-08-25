import { useEffect, useRef, useState } from 'react';

export function useMeasure(fallback = 600): [React.RefObject<HTMLDivElement | null>, number] {
  const ref = useRef<HTMLDivElement>(null);
  const [width, setWidth] = useState(fallback);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    setWidth(el.getBoundingClientRect().width || fallback);
    const ro = new ResizeObserver((entries) => {
      for (const e of entries) setWidth(Math.max(80, e.contentRect.width));
    });
    ro.observe(el);
    return () => ro.disconnect();
  }, [fallback]);

  return [ref, width];
}
