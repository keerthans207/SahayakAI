import React from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { 
  Search, 
  CheckCircle, 
  Upload, 
  ClipboardList,
  MessageSquare,
  Sparkles,
  FileText,
  ChevronRight,
  Info
} from 'lucide-react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { schemesService } from '../services/schemes.service';
import { applicationsService } from '../services/applications.service';
import { SchemeCard } from '../components/schemes/SchemeCard';
import { EmptyState } from '../components/ui/EmptyState';
import { useAuthStore } from '../stores/authStore';

export const DashboardPage: React.FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { user } = useAuthStore();

  // Fetch recommended schemes
  const { data: schemesData, isLoading: schemesLoading } = useQuery({
    queryKey: ['schemes', 'recommended'],
    queryFn: ({ signal }) => schemesService.list({ page: 1, page_size: 6 }, signal),
  });

  // Fetch user applications
  const { data: applications, isLoading: applicationsLoading } = useQuery({
    queryKey: ['applications'],
    queryFn: ({ signal }) => applicationsService.list(signal),
  });

  const quickActions = [
    {
      title: t('dashboard.quickActions.discoverSchemes'),
      description: t('dashboard.quickActions.discoverSchemesDesc'),
      icon: Search,
      color: 'bg-indigo-50 text-indigo-600',
      onClick: () => navigate('/schemes'),
    },
    {
      title: t('dashboard.quickActions.checkEligibility'),
      description: t('dashboard.quickActions.checkEligibilityDesc'),
      icon: CheckCircle,
      color: 'bg-green-50 text-green-600',
      onClick: () => navigate('/eligibility'),
    },
    {
      title: t('dashboard.quickActions.uploadDocuments'),
      description: t('dashboard.quickActions.uploadDocumentsDesc'),
      icon: Upload,
      color: 'bg-blue-50 text-blue-600',
      onClick: () => navigate('/documents'),
    },
    {
      title: t('dashboard.quickActions.trackApplications'),
      description: t('dashboard.quickActions.trackApplicationsDesc'),
      icon: ClipboardList,
      color: 'bg-purple-50 text-purple-600',
      onClick: () => navigate('/applications'),
    },
  ];

  const suggestedPrompts = [
    "Find scholarships for students with disabilities.",
    "How do I obtain a UDID card?",
    "What documents do I need?",
    "Find Karnataka government schemes.",
  ];

  const handlePromptClick = (prompt: string) => {
    navigate('/assistant', { state: { initialPrompt: prompt } });
  };

  return (
    <div className="max-w-7xl mx-auto space-y-8">
      {/* Welcome Hero */}
      <section className="bg-gradient-to-br from-indigo-50 via-white to-violet-50 rounded-2xl p-8 border border-indigo-100 shadow-sm">
        <div className="max-w-3xl">
          <h1 className="text-3xl font-bold text-gray-900 mb-3">
            {user ? t('dashboard.welcome', { name: user.full_name?.split(' ')[0] || 'there' }) : 'Welcome to Sahayak AI'}
          </h1>
          <p className="text-lg text-gray-600 mb-6">
            {t('dashboard.welcomeMessage')}
          </p>
          <div className="flex flex-wrap gap-3">
            <Button 
              size="lg" 
              onClick={() => navigate('/assistant')}
              className="gap-2 bg-gradient-to-r from-violet-600 to-indigo-600 hover:from-violet-700 hover:to-indigo-700"
            >
              <MessageSquare className="h-5 w-5" />
              {t('dashboard.talkToSahayak', { defaultValue: 'Talk to Sahayak' })}
            </Button>
            <Button 
              size="lg" 
              variant="outline"
              onClick={() => navigate('/schemes')}
              className="gap-2"
            >
              <Search className="h-5 w-5" />
              {t('dashboard.exploreSchemes', { defaultValue: 'Explore Schemes' })}
            </Button>
          </div>
        </div>
      </section>

      {/* Quick Actions */}
      <section>
        <h2 className="text-xl font-semibold text-gray-900 mb-4">
          {t('dashboard.quickActionsTitle')}
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {quickActions.map((action) => {
            const Icon = action.icon;
            return (
              <Card
                key={action.title}
                className="cursor-pointer transition-all hover:shadow-md hover:border-indigo-200 group"
                onClick={action.onClick}
              >
                <CardContent className="p-6">
                  <div className={`w-12 h-12 rounded-lg ${action.color} flex items-center justify-center mb-4 group-hover:scale-110 transition-transform`}>
                    <Icon className="h-6 w-6" />
                  </div>
                  <h3 className="font-semibold text-gray-900 mb-1 flex items-center justify-between">
                    {action.title}
                    <ChevronRight className="h-4 w-4 text-gray-400 opacity-0 group-hover:opacity-100 transition-opacity" />
                  </h3>
                  <p className="text-sm text-gray-600">{action.description}</p>
                </CardContent>
              </Card>
            );
          })}
        </div>
      </section>

      {/* Recommended Schemes */}
      <section>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-gray-900">
            {t('dashboard.recommendedSchemes')}
          </h2>
          <Button variant="ghost" size="sm" onClick={() => navigate('/schemes')}>
            {t('common.viewAll')}
            <ChevronRight className="h-4 w-4 ml-1" />
          </Button>
        </div>
        {schemesLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {[1, 2, 3].map((i) => (
              <Card key={i} className="p-6 animate-pulse">
                <div className="h-4 bg-gray-200 rounded w-3/4 mb-3"></div>
                <div className="h-3 bg-gray-200 rounded w-1/2 mb-4"></div>
                <div className="h-8 bg-gray-200 rounded"></div>
              </Card>
            ))}
          </div>
        ) : schemesData && schemesData.items.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {schemesData.items.slice(0, 6).map((scheme) => (
              <SchemeCard key={scheme.scheme_id} scheme={scheme} />
            ))}
          </div>
        ) : (
          <Card>
            <CardContent className="p-8">
              <EmptyState
                icon={FileText}
                title={t('dashboard.noSchemes')}
                description={t('dashboard.noSchemesDesc')}
                action={
                  <Button onClick={() => navigate('/schemes')}>
                    {t('dashboard.browseSchemes')}
                  </Button>
                }
              />
            </CardContent>
          </Card>
        )}
      </section>

      {/* Applications Overview & AI Assistant */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Applications Overview */}
        <section>
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <ClipboardList className="h-5 w-5" />
                {t('dashboard.applicationsOverview')}
              </CardTitle>
            </CardHeader>
            <CardContent>
              {applicationsLoading ? (
                <div className="space-y-3">
                  {[1, 2].map((i) => (
                    <div key={i} className="h-16 bg-gray-100 rounded animate-pulse"></div>
                  ))}
                </div>
              ) : applications && applications.length > 0 ? (
                <div className="space-y-3">
                  {applications.slice(0, 3).map((app) => (
                    <div
                      key={app.id}
                      className="p-4 border rounded-lg hover:bg-gray-50 cursor-pointer transition-colors"
                      onClick={() => navigate(`/applications/${app.id}`)}
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1 min-w-0">
                          <p className="font-medium text-sm text-gray-900 truncate">
                            {app.scheme_id}
                          </p>
                          <p className="text-xs text-gray-500 mt-1">
                            {t(`applications.status.${app.status}`, { defaultValue: app.status })}
                          </p>
                        </div>
                        <ChevronRight className="h-4 w-4 text-gray-400 ml-2 flex-shrink-0" />
                      </div>
                    </div>
                  ))}
                  {applications.length > 3 && (
                    <Button
                      variant="ghost"
                      size="sm"
                      className="w-full"
                      onClick={() => navigate('/applications')}
                    >
                      {t('dashboard.viewAllApplications', { count: applications.length })}
                    </Button>
                  )}
                </div>
              ) : (
                <EmptyState
                  icon={ClipboardList}
                  title={t('dashboard.noApplications')}
                  description={t('dashboard.noApplicationsDesc')}
                  action={
                    <Button size="sm" onClick={() => navigate('/schemes')}>
                      {t('dashboard.startApplication')}
                    </Button>
                  }
                />
              )}
            </CardContent>
          </Card>
        </section>

        {/* AI Assistant */}
        <section>
          <Card className="bg-gradient-to-br from-violet-50 to-indigo-50 border-violet-200">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Sparkles className="h-5 w-5 text-violet-600" />
                {t('dashboard.aiAssistant')}
              </CardTitle>
              <CardDescription>
                {t('dashboard.aiAssistantDesc')}
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="space-y-2">
                {suggestedPrompts.map((prompt, index) => (
                  <button
                    key={index}
                    onClick={() => handlePromptClick(prompt)}
                    className="w-full text-left p-3 bg-white border border-violet-200 rounded-lg text-sm hover:border-violet-300 hover:shadow-sm transition-all group"
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-gray-700">{prompt}</span>
                      <ChevronRight className="h-4 w-4 text-gray-400 opacity-0 group-hover:opacity-100 transition-opacity" />
                    </div>
                  </button>
                ))}
              </div>
              <Button
                className="w-full gap-2"
                onClick={() => navigate('/assistant')}
              >
                <MessageSquare className="h-4 w-4" />
                {t('dashboard.startConversation')}
              </Button>
            </CardContent>
          </Card>
        </section>
      </div>

      {/* Info Banner */}
      <section>
        <Card className="bg-blue-50 border-blue-200">
          <CardContent className="p-6">
            <div className="flex gap-4">
              <div className="flex-shrink-0">
                <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
                  <Info className="h-5 w-5 text-blue-600" />
                </div>
              </div>
              <div>
                <h3 className="font-semibold text-gray-900 mb-1">
                  {t('dashboard.infoTitle')}
                </h3>
                <p className="text-sm text-gray-700">
                  {t('dashboard.infoMessage')}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </section>
    </div>
  );
};
