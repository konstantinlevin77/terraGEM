import { useMemo } from 'react';
import { useQueries } from '@tanstack/react-query';
import { metricsApi } from '@/api/metrics';

export interface LatestReading {
  value: number;
  time: string;
}

export function useLatestBySensor(greenhouseIds: number[]): Map<number, LatestReading> {
  const queries = useQueries({
    queries: greenhouseIds.map((id) => ({
      queryKey: ['gh-latest', id],
      queryFn: () => metricsApi.latestSnapshot(id),
      staleTime: 30_000,
    })),
  });

  return useMemo(() => {
    const map = new Map<number, LatestReading>();
    for (const q of queries) {
      for (const s of q.data?.sensors ?? []) {
        if (s.latest_measurement) {
          map.set(s.id, {
            value: s.latest_measurement.value,
            time: s.latest_measurement.measurement_time,
          });
        }
      }
    }
    return map;
  }, [queries]);
}
