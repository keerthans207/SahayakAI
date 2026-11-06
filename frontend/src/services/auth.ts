import { api } from './api';

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterData {
  email: string;
  password: string;
  full_name: string;
  phone_number?: string;
  preferred_language: string;
}

export interface User {
  id: string;
  email: string;
  full_name: string;
  phone_number?: string;
  date_of_birth?: string;
  gender?: string;
  state?: string;
  preferred_language: string;
  created_at: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export const authService = {
  async login(credentials: LoginCredentials): Promise<AuthResponse> {
    const formData = new FormData();
    formData.append('username', credentials.email);
    formData.append('password', credentials.password);
    
    return api.post<AuthResponse>('/auth/login', formData);
  },

  async register(data: RegisterData): Promise<AuthResponse> {
    return api.post<AuthResponse>('/auth/register', data);
  },

  async getCurrentUser(): Promise<User> {
    return api.get<User>('/auth/me');
  },

  async logout(): Promise<void> {
    // Clear token from local storage and auth store
    localStorage.removeItem('token');
  },
};
