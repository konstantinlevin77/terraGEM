import { request } from '@/api/client';
import type { Sensor } from '@/types';

export interface SensorPayload {
  greenhouse: number;
  profile: number;
  description: string;
  is_active?: boolean;
}

export const sensorApi = {
  list(): Promise<Sensor[]> {
    return request<Sensor[]>('/sensors/');
  },

  create(payload: SensorPayload): Promise<Sensor> {
    return request<Sensor>('/sensors/', { method: 'POST', body: payload });
  },

  update(id: number, payload: Partial<SensorPayload>): Promise<Sensor> {
    return request<Sensor>(`/sensors/${id}/`, { method: 'PATCH', body: payload });
  },
};
