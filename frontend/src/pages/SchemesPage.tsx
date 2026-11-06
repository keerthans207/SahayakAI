import React, { useState, useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import { useQuery } from '@tanstack/react-query';
import { Search, Filter, X } from 'lucide-react';
import { schemesService, type SchemeListParams } from '../services/schemes.service';
import { SchemeCard } from '../components/schemes/SchemeCard';
import { EmptyState } from '../components/ui/EmptyState';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { FileText } from 'lucide-react';

export const SchemesPage: React.FC = () => {
  const { t } = useTranslation();
  const [searchQuery, setSearchQuery] = useState('');
  const [filters, setFilters] = useState<SchemeListParams>({
    page: 1,
    page_size: 12,
  });
  const [showFilters, setShowFilters] = useState(false);

  // Fetch schemes
  const { data, isLoading, error } = useQuery({
    queryKey: ['schemes', filters, searchQuery],
    queryFn: ({ signal }) =>
      searchQuery
        ? schemesService.search(searchQuery, filters, signal)
        : schemesService.list(filters, signal),
  });

  // Fetch categories
  const { data: categories } = useQuery({
    queryKey: ['scheme-categories'],
    queryFn: ({ signal }) => schemesService.categories(signal),
  });

  const handleFilterChange = (key: keyof SchemeListParams, value: string | undefined) => {
    setFilters((prev) => ({
      ...prev,
      [key]: value,
      page: 1, // Reset to first page when filters change
    }));
  };

  const clearFilters = () => {
    setFilters({
      page: 1,
      page_size: 12,
    });
    setSearchQuery('');
  };

  const activeFiltersCount = useMemo(() => {
    let count = 0;
    if (filters.category) count++;
    if (filters.government_level) count++;
    if (filters.state) count++;
    if (filters.status) count++;
    return count;
  }, [filters]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    // Query automatically refetches due to dependency
  };

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900 mb-2">{t('schemes.title')}</h1>
        <p className="text-gray-600">{t('schemes.description')}</p>
      </div>

      {/* Search and Filter Bar */}
      <Card className="p-4">
        <div className="space-y-4">
          {/* Search */}
          <form onSubmit={handleSearch} className="flex gap-2">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
              <Input
                type="text"
                placeholder={t('schemes.searchPlaceholder')}
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10"
              />
            </div>
            <Button
              type="button"
              variant="outline"
              onClick={() => setShowFilters(!showFilters)}
              className="gap-2"
            >
              <Filter className="h-4 w-4" />
              {t('common.filters')}
              {activeFiltersCount > 0 && (
                <span className="ml-1 bg-indigo-600 text-white rounded-full w-5 h-5 text-xs flex items-center justify-center">
                  {activeFiltersCount}
                </span>
              )}
            </Button>
          </form>

          {/* Filters Panel */}
          {showFilters && (
            <div className="pt-4 border-t space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {/* Category Filter */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    {t('schemes.category')}
                  </label>
                  <select
                    value={filters.category || ''}
                    onChange={(e) =>
                      handleFilterChange('category', e.target.value || undefined)
                    }
                    className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                  >
                    <option value="">{t('common.all')}</option>
                    {categories?.map((cat) => (
                      <option key={cat.category} value={cat.category}>
                        {t(`schemes.categories.${cat.category}`, {
                          defaultValue: cat.category,
                        })}{' '}
                        ({cat.count})
                      </option>
                    ))}
                  </select>
                </div>

                {/* Government Level Filter */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    {t('schemes.governmentLevel')}
                  </label>
                  <select
                    value={filters.government_level || ''}
                    onChange={(e) =>
                      handleFilterChange('government_level', e.target.value || undefined)
                    }
                    className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                  >
                    <option value="">{t('common.all')}</option>
                    <option value="central">{t('schemes.central')}</option>
                    <option value="state">{t('schemes.state')}</option>
                  </select>
                </div>

                {/* State Filter */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    {t('schemes.stateLabel')}
                  </label>
                  <select
                    value={filters.state || ''}
                    onChange={(e) => handleFilterChange('state', e.target.value || undefined)}
                    className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                  >
                    <option value="">{t('common.all')}</option>
                    <option value="Karnataka">Karnataka</option>
                  </select>
                </div>

                {/* Status Filter */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    {t('schemes.statusLabel')}
                  </label>
                  <select
                    value={filters.status || ''}
                    onChange={(e) => handleFilterChange('status', e.target.value || undefined)}
                    className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                  >
                    <option value="">{t('common.all')}</option>
                    <option value="active">{t('schemes.active')}</option>
                    <option value="inactive">{t('schemes.inactive')}</option>
                  </select>
                </div>
              </div>

              {/* Clear Filters */}
              {activeFiltersCount > 0 && (
                <div className="flex justify-end">
                  <Button variant="ghost" size="sm" onClick={clearFilters} className="gap-2">
                    <X className="h-4 w-4" />
                    {t('common.clearFilters')}
                  </Button>
                </div>
              )}
            </div>
          )}
        </div>
      </Card>

      {/* Results Count */}
      {data && (
        <div className="flex items-center justify-between">
          <p className="text-sm text-gray-600">
            {t('schemes.resultsCount', { count: data.total, defaultValue: `${data.total} schemes found` })}
          </p>
        </div>
      )}

      {/* Schemes Grid */}
      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <Card key={i} className="p-6 animate-pulse">
              <div className="h-4 bg-gray-200 rounded w-3/4 mb-3"></div>
              <div className="h-3 bg-gray-200 rounded w-1/2 mb-4"></div>
              <div className="h-8 bg-gray-200 rounded"></div>
            </Card>
          ))}
        </div>
      ) : error ? (
        <Card className="p-8">
          <EmptyState
            icon={FileText}
            title={t('common.error')}
            description={t('schemes.errorLoading')}
          />
        </Card>
      ) : data && data.items.length > 0 ? (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {data.items.map((scheme) => (
              <SchemeCard key={scheme.scheme_id} scheme={scheme} />
            ))}
          </div>

          {/* Pagination */}
          {data.total > filters.page_size! && (
            <div className="flex justify-center gap-2 mt-8">
              <Button
                variant="outline"
                disabled={filters.page === 1}
                onClick={() => setFilters((prev) => ({ ...prev, page: prev.page! - 1 }))}
              >
                {t('common.previous')}
              </Button>
              <div className="flex items-center gap-2 px-4">
                <span className="text-sm text-gray-600">
                  {t('common.page')} {filters.page} {t('common.of')}{' '}
                  {Math.ceil(data.total / filters.page_size!)}
                </span>
              </div>
              <Button
                variant="outline"
                disabled={filters.page! >= Math.ceil(data.total / filters.page_size!)}
                onClick={() => setFilters((prev) => ({ ...prev, page: prev.page! + 1 }))}
              >
                {t('common.next')}
              </Button>
            </div>
          )}
        </>
      ) : (
        <Card className="p-8">
          <EmptyState
            icon={FileText}
            title={t('schemes.noResults')}
            description={t('schemes.noResultsDesc')}
            action={
              activeFiltersCount > 0 || searchQuery ? (
                <Button onClick={clearFilters}>{t('common.clearFilters')}</Button>
              ) : undefined
            }
          />
        </Card>
      )}
    </div>
  );
};
