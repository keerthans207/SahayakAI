import React from 'react';
import { useParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';

export const SchemeDetailsPage: React.FC = () => {
  const { id } = useParams();
  const { t } = useTranslation();

  return (
    <div>
      <h1 className="text-3xl font-bold mb-6">{t('schemes.details')}</h1>
      <div className="bg-card rounded-lg p-6">
        <p className="text-muted-foreground">Scheme ID: {id}</p>
      </div>
    </div>
  );
};
