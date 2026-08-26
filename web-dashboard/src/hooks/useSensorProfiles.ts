import { useQuery } from '@tanstack/react-query';
import { sensorProfileApi } from '@/api/sensorProfiles';

export function useSensorProfiles() {
  return useQuery({
    queryKey: ['sensor-profiles'],
    queryFn: sensorProfileApi.list,
    staleTime: 5 * 60_000,
  });
}
