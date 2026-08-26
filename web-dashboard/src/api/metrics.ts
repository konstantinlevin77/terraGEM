import { request } from '@/api/client';
import type {
  DayOverviewResponse,
  GreenhouseLatestResponse,
  LatestMetricsResponse,
  TodaySummaryResponse,
} from '@/types';

export const metricsApi = {
  latestMetrics(greenhouseId: number): Promise<LatestMetricsResponse> {
    return request<LatestMetricsResponse>(`/greenhouses/${greenhouseId}/latest-metrics/`);
  },

  dayOverview(greenhouseId: number): Promise<DayOverviewResponse> {
    return request<DayOverviewResponse>(`/greenhouses/${greenhouseId}/day_overview/`);
  },

  todaySummary(greenhouseId: number): Promise<TodaySummaryResponse> {
    return request<TodaySummaryResponse>(`/greenhouses/${greenhouseId}/today_summary/`);
  },

  latestSnapshot(greenhouseId: number): Promise<GreenhouseLatestResponse> {
    return request<GreenhouseLatestResponse>(`/greenhouses/${greenhouseId}/latest/`);
  },
};
