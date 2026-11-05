import React from 'react';
import { useTranslation } from 'react-i18next';
import { Bell, Globe } from 'lucide-react';
import { useAuthStore } from '../../stores/authStore';

interface Props {
  title?: string;
}

export function TopBar({ title }: Props) {
  const { t, i18n } = useTranslation();
  const { user } = useAuthStore();

  const toggleLanguage = () => {
    const newLang = i18n.language === 'en' ? 'hi' : 'en';
    i18n.changeLanguage(newLang);
  };

  return (
    <header className="flex h-16 items-center gap-4 border-b px-6 bg-card">
      {title && (
        <h1 className="text-base font-semibold">
          {title}
        </h1>
      )}
      <div className="flex-1" />
      
      {/* Language Switcher */}
      <button
        onClick={toggleLanguage}
        className="flex items-center gap-2 px-3 py-2 rounded-md hover:bg-accent transition-colors"
        aria-label="Switch language"
      >
        <Globe className="h-4 w-4" />
        <span className="text-sm font-medium uppercase">{i18n.language}</span>
      </button>

      {/* User Info */}
      {user && (
        <div className="flex items-center gap-2">
          <span className="text-sm text-muted-foreground">{user.full_name}</span>
        </div>
      )}

      {/* Notifications */}
      <button
        className="flex h-8 w-8 items-center justify-center rounded-full hover:bg-accent transition-colors"
        aria-label="Notifications"
      >
        <Bell className="h-4 w-4" />
      </button>
    </header>
  );
}
