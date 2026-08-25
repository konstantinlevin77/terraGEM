import { useQuery } from '@tanstack/react-query';
import { sensorApi } from '@/api/sensors';

export function useSensors() {
  return useQuery({
    queryKey: ['sensors'],
    queryFn: sensorApi.list,
  });
}
