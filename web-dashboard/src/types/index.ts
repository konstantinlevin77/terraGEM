export type SensorType =
  | 'air_temperature'
  | 'soil_temperature'
  | 'air_humidity'
  | 'soil_humidity'
  | 'co2'
  | 'ph'
  | 'light_intensity'
  | 'not_specified';

export type SensorUnit = 'celsius' | 'percent' | 'ppm' | 'ph' | 'not_specified';

export type StatusLevel = 'ok' | 'watch' | 'crit' | 'neutral';

export interface User {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  company?: string;
  phone_number?: string;
}

export interface Greenhouse {
  id: number;
  name: string;
  description: string;
  latitude: number | null;
  longitude: number | null;
  created_at: string;
  updated_at: string;
}

export interface SensorProfile {
  id: number;
  name: string;
  sensor_type: SensorType;
  unit: SensorUnit;
  period: number;
  description: string;
}

export interface Sensor {
  id: number;
  greenhouse: number;
  profile: number;
  sensor_type: SensorType;
  sensor_brand: string;
  unit: SensorUnit;
  is_active: boolean;
  description: string;
  profile_name?: string;
  created_at: string;
  updated_at: string;
}

export interface MeasurementPoint {
  t: number; // Unix timestamp ms or ISO string
  v: number; // Metric reading value
}

export interface MetricSummary {
  sensor_type: SensorType;
  current_value: number | null;
  unit: SensorUnit;
  status: StatusLevel;
  delta_24h?: number;
  sparkline: number[];
}

export interface ActiveAlert {
  id: number;
  sensor: number;
  sensor_type: SensorType;
  sensor_description: string;
  greenhouse_id: number;
  greenhouse_name: string;
  triggered_value: number;
  unit: SensorUnit;
  severity: 'warning' | 'critical';
  status: 'active' | 'acknowledged' | 'resolved';
  message: string;
  created_at: string;
}

export type ActiveTab = 'overview' | 'greenhouses' | 'sensors' | 'history' | 'settings';
export type TimeRange = '24h' | '7d' | '30d';
export interface MetricCard {
  sensor_type: SensorType;
  sensor_type_display: string;
  current_value: number | null;
  unit: SensorUnit;
  status: 'optimal' | 'warning' | 'critical';
  status_display: string;
  delta_24h: number | null;
  sparkline: number[];
}

export interface LatestMetricsResponse {
  greenhouse_id: number;
  greenhouse_name: string;
  metrics: MetricCard[];
}

export interface TimelinePoint {
  timestamp: string;
  avg_value: number;
  min_value: number;
  max_value: number;
  reading_count: number;
}

export interface DaySeries {
  sensor_type: SensorType;
  timeline: TimelinePoint[];
}

export interface DayOverviewResponse {
  greenhouse_id: number;
  greenhouse_name: string;
  series: DaySeries[];
}

export interface TodayMetric {
  sensor_type: SensorType;
  unit: SensorUnit;
  min_value: number;
  max_value: number;
  avg_value: number;
  reading_count: number;
}

export interface TodaySummaryResponse {
  greenhouse_id: number;
  date: string;
  metrics: TodayMetric[];
}

export interface SensorWithLatest {
  id: number;
  profile: number;
  profile_name: string;
  sensor_type: SensorType;
  unit: SensorUnit;
  is_active: boolean;
  description: string;
  latest_measurement: {
    id: number;
    value: number;
    measurement_time: string;
  } | null;
}

export interface GreenhouseLatestResponse extends Greenhouse {
  sensors: SensorWithLatest[];
}

export interface ActiveAlertsResponse {
  total_active: number;
  alerts: ActiveAlert[];
}

export interface GreenhousePayload {
  name: string;
  description: string;
  latitude: number | null;
  longitude: number | null;
}

export interface SensorProfileFull extends SensorProfile {
  sensor_type_display?: string;
  unit_display?: string;
}

export interface SensorThreshold {
  id: number;
  sensor: number;
  warning_min: number;
  warning_max: number;
  critical_min: number;
  critical_max: number;
  is_active: boolean;
}
