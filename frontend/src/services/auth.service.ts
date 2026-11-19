import api from '@/lib/api';
import type { AuthTokens, User } from '@/types';

export const authService = {
  async login(email: string, password: string): Promise<AuthTokens> {
    const form = new FormData();
    form.append('username', email);
    form.append('password', password);
    const { data } = await api.post<AuthTokens>('/auth/login', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return data;
  },

  async register(payload: { email: string; username: string; full_name: string; password: string }): Promise<User> {
    const { data } = await api.post<User>('/auth/register', payload);
    return data;
  },

  async getMe(): Promise<User> {
    const { data } = await api.get<User>('/auth/me');
    return data;
  },

  async logout() {
    await api.post('/auth/logout');
  },
};
