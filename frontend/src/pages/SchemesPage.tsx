import React from 'react';
import { useTranslation } from 'react-i18next';

export const SchemesPage: React.FC = () => {
  const { t } = useTranslation();

  return (
    <div>
      <h1 className="text-3xl font-bold mb-6">{t('schemes.title')}</h1>
      <div className="bg-card rounded-lg p-6">
        <p className="text-muted-foreground">{t('schemes.placeholder')}</p>
      </div>
    </div>
  );
};
