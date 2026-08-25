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
  sensor_type: SensorType;
  sensor_brand: string;
  unit: SensorUnit;
  is_active: boolean;
  description: string;
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