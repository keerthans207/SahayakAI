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

const DEV_AUTH = import.meta.env.VITE_DEV_AUTH === 'true';

function developmentUser(
  email = 'developer@sahayak.local',
  name = 'Sahayak Development User'
): User {
  return {
    id: 'dev-user',
    email,
    full_name: name,
    preferred_language: 'en',
    created_at: new Date().toISOString(),
  };
}

function developmentResponse(email?: string, name?: string): AuthResponse {
  return {
    access_token: 'dev-session',
    token_type: 'bearer',
    user: developmentUser(email, name),
  };
}

export const authService = {
  async login(credentials: LoginCredentials): Promise<AuthResponse> {
    if (DEV_AUTH) {
      return developmentResponse();
    }

    const formData = new FormData();
    formData.append('username', credentials.email);
    formData.append('password', credentials.password);

    return api.upload<AuthResponse>('/auth/login', formData);
  },

  async register(data: RegisterData): Promise<AuthResponse> {
    if (DEV_AUTH) {
      return developmentResponse(data.email, data.full_name);
    }

    return api.post<AuthResponse>('/auth/register', data);
  },

  async getCurrentUser(): Promise<User> {
    if (DEV_AUTH) {
      return developmentUser();
    }

    return api.get<User>('/auth/me');
  },

  async logout(): Promise<void> {
    localStorage.removeItem('token');
    localStorage.removeItem('sahayak-dev-user-email');
  },
};
