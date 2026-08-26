import { request } from '@/api/client';
import type { SensorProfileFull } from '@/types';

export const sensorProfileApi = {
  list(): Promise<SensorProfileFull[]> {
    return request<SensorProfileFull[]>('/sensor-profiles/');
  },
};
