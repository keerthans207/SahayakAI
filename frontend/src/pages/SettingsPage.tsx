import React from 'react';
import { useTranslation } from 'react-i18next';

export const SettingsPage: React.FC = () => {
  const { t } = useTranslation();

  return (
    <div>
      <h1 className="text-3xl font-bold mb-6">{t('settings.title')}</h1>
      <div className="bg-card rounded-lg p-6">
        <p className="text-muted-foreground">{t('settings.placeholder')}</p>
      </div>
    </div>
  );
};
