import { request } from '@/api/client';
import type { SensorThreshold } from '@/types';

export interface ThresholdPayload {
  sensor: number;
  warning_min: number;
  warning_max: number;
  critical_min: number;
  critical_max: number;
  is_active?: boolean;
}

export const thresholdApi = {
  list(): Promise<SensorThreshold[]> {
    return request<SensorThreshold[]>('/thresholds/');
  },

  create(payload: ThresholdPayload): Promise<SensorThreshold> {
    return request<SensorThreshold>('/thresholds/', { method: 'POST', body: payload });
  },

  update(id: number, payload: Partial<ThresholdPayload>): Promise<SensorThreshold> {
    return request<SensorThreshold>(`/thresholds/${id}/`, { method: 'PATCH', body: payload });
  },
};
