import { request } from '@/api/client';
import type { Greenhouse } from '@/types';

export const greenhouseApi = {
  list(): Promise<Greenhouse[]> {
    return request<Greenhouse[]>('/greenhouses/');
  },
};
