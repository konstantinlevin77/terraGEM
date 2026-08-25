export const en = {
  'terraGEM — Greenhouse Environment Management': 'terraGEM — Greenhouse Environment Management',
  'Greenhouse Environment Management': 'Greenhouse Environment Management',
  'Sign in': 'Sign in',
  'Sign out': 'Sign out',
  'Sign in to your greenhouse dashboard': 'Sign in to your greenhouse dashboard',
  Username: 'Username',
  Password: 'Password',
  'Signing in…': 'Signing in…',
  'Invalid username or password.': 'Invalid username or password.',
  'Connection error. Is the API running?': 'Connection error. Is the API running?',
  Welcome: 'Welcome',
} as const;

export type Dict = Record<keyof typeof en, string>;
