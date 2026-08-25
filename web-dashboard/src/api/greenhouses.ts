import { request } from '@/api/client';
import type { Greenhouse, GreenhousePayload } from '@/types';

export const greenhouseApi = {
  list(): Promise<Greenhouse[]> {
    return request<Greenhouse[]>('/greenhouses/');
  },

  create(payload: GreenhousePayload): Promise<Greenhouse> {
    return request<Greenhouse>('/greenhouses/', { method: 'POST', body: payload });
  },

  update(id: number, payload: Partial<GreenhousePayload>): Promise<Greenhouse> {
    return request<Greenhouse>(`/greenhouses/${id}/`, { method: 'PATCH', body: payload });
  },

  remove(id: number): Promise<void> {
    return request<void>(`/greenhouses/${id}/`, { method: 'DELETE' });
  },
};
