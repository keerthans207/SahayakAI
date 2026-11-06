import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import {
  LayoutDashboard,
  MessageSquare,
  FileText,
  Upload,
  ClipboardList,
  User,
  Settings,
} from 'lucide-react';

export const SideNav: React.FC = () => {
  const { t } = useTranslation();
  const location = useLocation();

  const navigation = [
    {
      name: t('nav.dashboard'),
      href: '/dashboard',
      icon: LayoutDashboard,
    },
    {
      name: t('nav.assistant'),
      href: '/assistant',
      icon: MessageSquare,
    },
    {
      name: t('nav.schemes'),
      href: '/schemes',
      icon: FileText,
    },
    {
      name: t('nav.documents'),
      href: '/documents',
      icon: Upload,
    },
    {
      name: t('nav.applications'),
      href: '/applications',
      icon: ClipboardList,
    },
    {
      name: t('nav.profile'),
      href: '/profile',
      icon: User,
    },
    {
      name: t('nav.settings'),
      href: '/settings',
      icon: Settings,
    },
  ];

  return (
    <nav className="w-64 h-screen bg-card border-r fixed left-0 top-16 flex flex-col">
      <div className="flex-1 overflow-y-auto p-4">
        <ul className="space-y-2">
          {navigation.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.href;

            return (
              <li key={item.name}>
                <Link
                  to={item.href}
                  className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
                    isActive
                      ? 'bg-primary text-primary-foreground'
                      : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
                  }`}
                >
                  <Icon className="w-5 h-5" />
                  <span className="font-medium">{item.name}</span>
                </Link>
              </li>
            );
          })}
        </ul>
      </div>
    </nav>
  );
};
