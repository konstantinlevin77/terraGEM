import { request } from '@/api/client';
import type { ActiveAlertsResponse } from '@/types';

export const alertsApi = {
  active(): Promise<ActiveAlertsResponse> {
    return request<ActiveAlertsResponse>('/alerts/active/');
  },

  acknowledge(alertId: number): Promise<{ id: number; status: string; status_display: string }> {
    return request(`/alerts/${alertId}/acknowledge/`, { method: 'POST' });
  },
};
