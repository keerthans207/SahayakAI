import React from 'react';
import { useTranslation } from 'react-i18next';

export const EligibilityPage: React.FC = () => {
  const { t } = useTranslation();

  return (
    <div>
      <h1 className="text-3xl font-bold mb-6">{t('eligibility.title')}</h1>
      <div className="bg-card rounded-lg p-6">
        <p className="text-muted-foreground">{t('eligibility.placeholder')}</p>
      </div>
    </div>
  );
};
