import { api } from './api';
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
    return api.get<User>('/users/me');
  },

  async updateProfile(data: UpdateProfileData): Promise<User> {
    return api.patch<User>('/users/me', data);
  },
};
