import { api } from '../lib/api';
import { User } from './auth';

export interface UpdateProfileData {
  full_name?: string;
  phone_number?: string;
  date_of_birth?: string;
  gender?: string;
  state?: string;
  preferred_language?: string;
}

export const usersService = {
  async getProfile(): Promise<User> {
    const response = await api.get<User>('/users/me');
    return response.data;
  },

  async updateProfile(data: UpdateProfileData): Promise<User> {
    const response = await api.put<User>('/users/me', data);
    return response.data;
  },
};
