import React, { useEffect, useState } from 'react';
import { useAuthStore } from '../stores/authStore';
import { authService } from '../services/auth';

interface AuthProviderProps {
  children: React.ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [isInitialized, setIsInitialized] = useState(false);
  const { setToken, setUser, clearAuth } = useAuthStore();

  useEffect(() => {
    const initAuth = async () => {
      const token = localStorage.getItem('token');
      
      if (token) {
        setToken(token);
        
        try {
          const user = await authService.getCurrentUser();
          setUser(user);
        } catch (error) {
          console.error('Failed to fetch user:', error);
          clearAuth();
        }
      }
      
      setIsInitialized(true);
    };

    initAuth();
  }, [setToken, setUser, clearAuth]);

  if (!isInitialized) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
    );
  }

  return <>{children}</>;
};
