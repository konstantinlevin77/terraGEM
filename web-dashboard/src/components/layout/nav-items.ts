import { LayoutDashboard, Warehouse, Cpu, History, Settings, type LucideIcon } from 'lucide-react';

export interface NavItem {
  key: string;
  path: string;
  labelKey: string;
  icon: LucideIcon;
}

export const NAV_ITEMS: NavItem[] = [
  { key: 'overview', path: '/overview', labelKey: 'Overview', icon: LayoutDashboard },
  { key: 'greenhouses', path: '/greenhouses', labelKey: 'Greenhouses', icon: Warehouse },
  { key: 'sensors', path: '/sensors', labelKey: 'Sensors', icon: Cpu },
  { key: 'history', path: '/history', labelKey: 'History', icon: History },
  { key: 'settings', path: '/settings', labelKey: 'Settings', icon: Settings },
];
