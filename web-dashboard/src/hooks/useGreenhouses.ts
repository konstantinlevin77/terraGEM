import { useQuery } from '@tanstack/react-query';
import { greenhouseApi } from '@/api/greenhouses';

export function useGreenhouses() {
  return useQuery({
    queryKey: ['greenhouses'],
    queryFn: greenhouseApi.list,
  });
}
