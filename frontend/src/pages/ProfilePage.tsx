import React from 'react';
import { useTranslation } from 'react-i18next';
import { useAuthStore } from '../stores/authStore';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/Card';

export const ProfilePage: React.FC = () => {
  const { t } = useTranslation();
  const { user } = useAuthStore();

  return (
    <div>
      <h1 className="text-3xl font-bold mb-6">{t('profile.title')}</h1>
      <Card>
        <CardHeader>
          <CardTitle>{t('profile.information')}</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div>
              <p className="text-sm font-medium text-muted-foreground">{t('auth.fullName')}</p>
              <p className="text-lg">{user?.full_name}</p>
            </div>
            <div>
              <p className="text-sm font-medium text-muted-foreground">{t('auth.email')}</p>
              <p className="text-lg">{user?.email}</p>
            </div>
            {user?.phone_number && (
              <div>
                <p className="text-sm font-medium text-muted-foreground">{t('auth.phone')}</p>
                <p className="text-lg">{user.phone_number}</p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
