import { request } from '@/api/client';
import type { User } from '@/types';

export interface TokenPair {
  refresh: string;
  access: string;
}

export interface RegisterPayload {
  username: string;
  email: string;
  password: string;
  password_confirm: string;
  first_name?: string;
  last_name?: string;
}

export const authApi = {
  login(username: string, password: string): Promise<TokenPair> {
    return request<TokenPair>('/auth/token/', { method: 'POST', body: { username, password } });
  },

  me(): Promise<User> {
    return request<User>('/auth/me/');
  },

  register(payload: RegisterPayload): Promise<User> {
    return request<User>('/auth/register/', { method: 'POST', body: payload });
  },
};
