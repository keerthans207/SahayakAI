import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { 
  ClipboardList, 
  Plus, 
  CheckCircle, 
  Clock, 
  AlertTriangle,
  ChevronRight,
  FileText,
  CheckSquare
} from 'lucide-react';
import { applicationsService } from '../services/applications.service';
import { schemesService } from '../services/schemes.service';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { EmptyState } from '../components/ui/EmptyState';
import { Badge } from '../components/ui/Badge';
import type { ApplicationRead } from '../types/api';

export const ApplicationsPage: React.FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [showCreateModal, setShowCreateModal] = useState(false);

  // Fetch applications
  const { data: applications, isLoading } = useQuery({
    queryKey: ['applications'],
    queryFn: ({ signal }) => applicationsService.list(signal),
  });

  // Fetch schemes for modal
  const { data: schemesData } = useQuery({
    queryKey: ['schemes', 'list'],
    queryFn: ({ signal }) => schemesService.list({ page: 1, page_size: 20 }, signal),
    enabled: showCreateModal,
  });

  const createApplicationMutation = useMutation({
    mutationFn: (schemeId: string) =>
      applicationsService.create({ scheme_id: schemeId }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['applications'] });
      setShowCreateModal(false);
    },
  });

  const getStatusBadge = (status: string) => {
    const variants: Record<string, { variant: any; icon: any }> = {
      discovered: { variant: 'info', icon: Clock },
      eligibility_pending: { variant: 'warning', icon: Clock },
      eligible_pending_documents: { variant: 'warning', icon: AlertTriangle },
      documents_incomplete: { variant: 'error', icon: AlertTriangle },
      ready_for_review: { variant: 'success', icon: CheckCircle },
      ready_for_user_submission: { variant: 'success', icon: CheckCircle },
      submitted_by_user: { variant: 'info', icon: CheckCircle },
      approved: { variant: 'success', icon: CheckCircle },
      rejected: { variant: 'error', icon: AlertTriangle },
    };
    
    const config = variants[status] || variants.discovered;
    const Icon = config.icon;
    
    return (
      <Badge variant={config.variant} className="flex items-center gap-1">
        <Icon className="h-3 w-3" />
        {t(`applications.status.${status}`, { defaultValue: status })}
      </Badge>
    );
  };

  if (isLoading) {
    return (
      <div className="max-w-6xl mx-auto space-y-6">
        <div className="h-8 bg-gray-200 rounded w-1/3 animate-pulse"></div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[1, 2].map((i) => (
            <Card key={i} className="p-6">
              <div className="space-y-3">
                <div className="h-4 bg-gray-200 rounded w-3/4 animate-pulse"></div>
                <div className="h-3 bg-gray-200 rounded w-1/2 animate-pulse"></div>
              </div>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">{t('applications.title')}</h1>
          <p className="text-gray-600">
            {t('applications.description', { 
              defaultValue: 'Track and manage your scheme application preparations.' 
            })}
          </p>
        </div>
        <Button onClick={() => setShowCreateModal(true)} className="gap-2">
          <Plus className="h-4 w-4" />
          {t('applications.new', { defaultValue: 'New Application' })}
        </Button>
      </div>

      {/* Applications List */}
      {applications && applications.length > 0 ? (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {applications.map((app) => (
              <Card 
                key={app.id}
                className="p-6 hover:shadow-lg transition-shadow cursor-pointer group"
                onClick={() => navigate(`/applications/${app.id}`)}
              >
                <div className="flex items-start justify-between mb-4">
                  <div className="flex-1">
                    <h3 className="font-semibold text-gray-900 mb-2 group-hover:text-indigo-600 transition-colors">
                      {app.scheme_id}
                    </h3>
                    {getStatusBadge(app.status)}
                  </div>
                  <ChevronRight className="h-5 w-5 text-gray-400 group-hover:text-indigo-600 transition-colors" />
                </div>

                <div className="space-y-2 text-sm">
                  <div className="flex items-center gap-2 text-gray-600">
                    <FileText className="h-4 w-4" />
                    <span>
                      {app.required_documents.length} {t('applications.documents', { defaultValue: 'documents' })}
                    </span>
                  </div>
                  
                  {app.notes && (
                    <p className="text-gray-600 text-xs line-clamp-2 mt-2">
                      {app.notes}
                    </p>
                  )}
                  
                  <div className="pt-3 mt-3 border-t border-gray-100">
                    <p className="text-xs text-gray-500">
                      {t('applications.created', { defaultValue: 'Created' })}: {' '}
                      {new Date(app.created_at).toLocaleDateString()}
                    </p>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        </div>
      ) : (
        <Card className="p-8">
          <EmptyState
            icon={ClipboardList}
            title={t('applications.noApplications', { defaultValue: 'No applications yet' })}
            description={t('applications.noApplicationsDesc', { 
              defaultValue: 'Start preparing an application for a government scheme.' 
            })}
            action={
              <Button onClick={() => setShowCreateModal(true)} className="gap-2">
                <Plus className="h-4 w-4" />
                {t('applications.startNew', { defaultValue: 'Start New Application' })}
              </Button>
            }
          />
        </Card>
      )}

      {/* Info Card */}
      <Card className="bg-indigo-50 border-indigo-200 p-4">
        <div className="flex gap-3">
          <CheckSquare className="h-5 w-5 text-indigo-600 flex-shrink-0 mt-0.5" />
          <div className="text-sm">
            <p className="font-medium text-indigo-900 mb-1">
              {t('applications.infoTitle', { defaultValue: 'Application Preparation' })}
            </p>
            <p className="text-indigo-700">
              {t('applications.infoDesc', { 
                defaultValue: 'We help you prepare applications by organizing documents and checking eligibility. You\'ll submit directly to the government portal.' 
              })}
            </p>
          </div>
        </div>
      </Card>

      {/* Create Application Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <Card className="max-w-2xl w-full max-h-[80vh] overflow-y-auto">
            <div className="p-6 border-b border-gray-200">
              <h2 className="text-xl font-bold text-gray-900">
                {t('applications.selectScheme', { defaultValue: 'Select a Scheme' })}
              </h2>
              <p className="text-sm text-gray-600 mt-1">
                {t('applications.selectSchemeDesc', { 
                  defaultValue: 'Choose which scheme you want to prepare an application for.' 
                })}
              </p>
            </div>

            <div className="p-6 space-y-3">
              {schemesData?.items.map((scheme) => (
                <button
                  key={scheme.scheme_id}
                  onClick={() => createApplicationMutation.mutate(scheme.scheme_id)}
                  disabled={createApplicationMutation.isPending}
                  className="w-full text-left p-4 border border-gray-200 rounded-lg hover:border-indigo-300 hover:bg-indigo-50 transition-colors disabled:opacity-50"
                >
                  <p className="font-medium text-gray-900">{scheme.official_name}</p>
                  <p className="text-sm text-gray-600 mt-1">
                    {scheme.category} • {scheme.government_level}
                  </p>
                </button>
              ))}
              
              {!schemesData?.items.length && (
                <p className="text-center text-gray-500 py-8">
                  {t('applications.noSchemes', { defaultValue: 'No schemes available' })}
                </p>
              )}
            </div>

            <div className="p-6 border-t border-gray-200 flex justify-end gap-3">
              <Button 
                variant="outline" 
                onClick={() => setShowCreateModal(false)}
                disabled={createApplicationMutation.isPending}
              >
                {t('common.cancel', { defaultValue: 'Cancel' })}
              </Button>
            </div>
          </Card>
        </div>
      )}
    </div>
  );
};
