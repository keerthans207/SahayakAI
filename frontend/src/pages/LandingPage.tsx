import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuthStore } from '../stores/authStore';
import { authService } from '../services/auth';
import { useToast } from '../providers/ToastProvider';

export const LandingPage: React.FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { setToken, setUser } = useAuthStore();
  const { showToast } = useToast();
  const [isLogin, setIsLogin] = useState(true);
  const [isLoading, setIsLoading] = useState(false);

  const [loginForm, setLoginForm] = useState({
    email: '',
    password: '',
  });

  const [registerForm, setRegisterForm] = useState({
    email: '',
    password: '',
    full_name: '',
    phone_number: '',
    preferred_language: 'en',
  });

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);

    try {
      const response = await authService.login(loginForm);
      setToken(response.access_token);
      setUser(response.user);
      localStorage.setItem('token', response.access_token);
      showToast('success', t('auth.loginSuccess'));
      navigate('/dashboard');
    } catch (error: any) {
      showToast('error', error.response?.data?.detail || t('auth.loginError'));
    } finally {
      setIsLoading(false);
    }
  };

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);

    try {
      const response = await authService.register(registerForm);
      setToken(response.access_token);
      setUser(response.user);
      localStorage.setItem('token', response.access_token);
      showToast('success', t('auth.registerSuccess'));
      navigate('/dashboard');
    } catch (error: any) {
      showToast('error', error.response?.data?.detail || t('auth.registerError'));
    } finally {
      setIsLoading(false);
    }
  };

  const containerStyle: React.CSSProperties = {
    minHeight: '100vh',
    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    padding: '2rem',
  };

  const gridStyle: React.CSSProperties = {
    maxWidth: '1200px',
    width: '100%',
    display: 'grid',
    gridTemplateColumns: window.innerWidth > 768 ? '1fr 1fr' : '1fr',
    gap: '3rem',
    alignItems: 'center',
  };

  const heroStyle: React.CSSProperties = {
    color: 'white',
  };

  const cardStyle: React.CSSProperties = {
    background: 'white',
    borderRadius: '1rem',
    padding: '2.5rem',
    boxShadow: '0 20px 60px rgba(0,0,0,0.3)',
  };

  const inputStyle: React.CSSProperties = {
    width: '100%',
    padding: '0.75rem',
    border: '2px solid #e5e7eb',
    borderRadius: '0.5rem',
    fontSize: '1rem',
    marginTop: '0.25rem',
  };

  const buttonStyle: React.CSSProperties = {
    width: '100%',
    padding: '0.875rem',
    background: '#667eea',
    color: 'white',
    border: 'none',
    borderRadius: '0.5rem',
    fontSize: '1rem',
    fontWeight: '600',
    cursor: 'pointer',
    transition: 'all 0.3s',
  };

  const labelStyle: React.CSSProperties = {
    display: 'block',
    fontSize: '0.875rem',
    fontWeight: '500',
    marginBottom: '0.5rem',
    color: '#374151',
  };

  return (
    <div style={containerStyle}>
      <div style={gridStyle}>
        {/* Hero Section */}
        <div style={heroStyle}>
          <h1 style={{ fontSize: '3rem', fontWeight: 'bold', marginBottom: '1rem' }}>
            {t('landing.title')}
          </h1>
          <p style={{ fontSize: '1.25rem', marginBottom: '2rem', opacity: 0.9 }}>
            {t('landing.subtitle')}
          </p>
          <ul style={{ listStyle: 'none', padding: 0 }}>
            <li style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
              <span style={{ fontSize: '1.5rem' }}>✓</span>
              <span style={{ fontSize: '1.125rem' }}>{t('landing.feature1')}</span>
            </li>
            <li style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
              <span style={{ fontSize: '1.5rem' }}>✓</span>
              <span style={{ fontSize: '1.125rem' }}>{t('landing.feature2')}</span>
            </li>
            <li style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
              <span style={{ fontSize: '1.5rem' }}>✓</span>
              <span style={{ fontSize: '1.125rem' }}>{t('landing.feature3')}</span>
            </li>
          </ul>
        </div>

        {/* Auth Card */}
        <div style={cardStyle}>
          <h2 style={{ fontSize: '1.875rem', fontWeight: 'bold', marginBottom: '0.5rem' }}>
            {isLogin ? t('auth.login') : t('auth.register')}
          </h2>
          <p style={{ color: '#6b7280', marginBottom: '2rem' }}>
            {isLogin ? t('auth.loginDescription') : t('auth.registerDescription')}
          </p>

          {isLogin ? (
            <form onSubmit={handleLogin} style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
              <div>
                <label htmlFor="email" style={labelStyle}>
                  {t('auth.email')}
                </label>
                <input
                  id="email"
                  type="email"
                  value={loginForm.email}
                  onChange={(e) => setLoginForm({ ...loginForm, email: e.target.value })}
                  style={inputStyle}
                  required
                />
              </div>
              <div>
                <label htmlFor="password" style={labelStyle}>
                  {t('auth.password')}
                </label>
                <input
                  id="password"
                  type="password"
                  value={loginForm.password}
                  onChange={(e) => setLoginForm({ ...loginForm, password: e.target.value })}
                  style={inputStyle}
                  required
                />
              </div>
              <button 
                type="submit" 
                style={buttonStyle}
                disabled={isLoading}
                onMouseOver={(e) => e.currentTarget.style.background = '#5568d3'}
                onMouseOut={(e) => e.currentTarget.style.background = '#667eea'}
              >
                {isLoading ? t('common.loading') : t('auth.login')}
              </button>
              <p style={{ textAlign: 'center', fontSize: '0.875rem', color: '#6b7280' }}>
                {t('auth.noAccount')}{' '}
                <button
                  type="button"
                  onClick={() => setIsLogin(false)}
                  style={{ color: '#667eea', background: 'none', border: 'none', cursor: 'pointer', textDecoration: 'underline' }}
                >
                  {t('auth.register')}
                </button>
              </p>
            </form>
          ) : (
            <form onSubmit={handleRegister} style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
              <div>
                <label htmlFor="full_name" style={labelStyle}>
                  {t('auth.fullName')}
                </label>
                <input
                  id="full_name"
                  value={registerForm.full_name}
                  onChange={(e) => setRegisterForm({ ...registerForm, full_name: e.target.value })}
                  style={inputStyle}
                  required
                />
              </div>
              <div>
                <label htmlFor="register_email" style={labelStyle}>
                  {t('auth.email')}
                </label>
                <input
                  id="register_email"
                  type="email"
                  value={registerForm.email}
                  onChange={(e) => setRegisterForm({ ...registerForm, email: e.target.value })}
                  style={inputStyle}
                  required
                />
              </div>
              <div>
                <label htmlFor="register_password" style={labelStyle}>
                  {t('auth.password')}
                </label>
                <input
                  id="register_password"
                  type="password"
                  value={registerForm.password}
                  onChange={(e) => setRegisterForm({ ...registerForm, password: e.target.value })}
                  style={inputStyle}
                  required
                />
              </div>
              <div>
                <label htmlFor="phone" style={labelStyle}>
                  {t('auth.phone')}
                </label>
                <input
                  id="phone"
                  type="tel"
                  value={registerForm.phone_number}
                  onChange={(e) => setRegisterForm({ ...registerForm, phone_number: e.target.value })}
                  style={inputStyle}
                />
              </div>
              <button 
                type="submit" 
                style={buttonStyle}
                disabled={isLoading}
                onMouseOver={(e) => e.currentTarget.style.background = '#5568d3'}
                onMouseOut={(e) => e.currentTarget.style.background = '#667eea'}
              >
                {isLoading ? t('common.loading') : t('auth.register')}
              </button>
              <p style={{ textAlign: 'center', fontSize: '0.875rem', color: '#6b7280' }}>
                {t('auth.hasAccount')}{' '}
                <button
                  type="button"
                  onClick={() => setIsLogin(true)}
                  style={{ color: '#667eea', background: 'none', border: 'none', cursor: 'pointer', textDecoration: 'underline' }}
                >
                  {t('auth.login')}
                </button>
              </p>
            </form>
          )}
        </div>
      </div>
    </div>
  );
};
