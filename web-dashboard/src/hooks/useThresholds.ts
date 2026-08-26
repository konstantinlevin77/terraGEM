import { useQuery } from '@tanstack/react-query';
import { thresholdApi } from '@/api/thresholds';

export function useThresholds() {
  return useQuery({
    queryKey: ['thresholds'],
    queryFn: thresholdApi.list,
  });
}
