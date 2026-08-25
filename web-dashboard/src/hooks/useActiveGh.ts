import { useGreenhouses } from '@/hooks/useGreenhouses';
import { useScope } from '@/hooks/useScope';
import type { Greenhouse } from '@/types';

interface ActiveGh {
  ghId: number | null;
  greenhouse: Greenhouse | undefined;
}

export function useActiveGh(): ActiveGh & { setGhId: (id: number) => void } {
  const { ghId, setGhId } = useScope();
  const { data: greenhouses = [] } = useGreenhouses();
  const active = greenhouses.find((g) => g.id === ghId) ?? greenhouses[0];
  return { ghId: active?.id ?? null, greenhouse: active, setGhId };
}
