import { Navigate } from 'react-router-dom';
import { useAuthStore } from '../../stores/authStore';
import { MainLayout } from '../layout/MainLayout';

interface ProtectedRouteProps {
  children: React.ReactNode;
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children }) => {
  const { token } = useAuthStore();

  if (!token) {
    return <Navigate to="/" replace />;
  }

  return <MainLayout>{children}</MainLayout>;
};
