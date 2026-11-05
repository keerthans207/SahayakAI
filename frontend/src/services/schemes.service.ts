import { api } from "./api";
import type { Page, SchemeRead, SchemeSummary, SchemeCategoryRead } from "@/types/api";

export interface SchemeListParams {
  category?: string;
  government_level?: string;
  state?: string;
  status?: string;
  page?: number;
  page_size?: number;
}

export const schemesService = {
  list: (params: SchemeListParams = {}, signal?: AbortSignal) => {
    const q = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => v !== undefined && q.set(k, String(v)));
    return api.get<Page<SchemeSummary>>(`/api/v1/schemes?${q}`, signal);
  },

  search: (query: string, params: SchemeListParams = {}, signal?: AbortSignal) => {
    const q = new URLSearchParams({ q: query });
    Object.entries(params).forEach(([k, v]) => v !== undefined && q.set(k, String(v)));
    return api.get<Page<SchemeSummary>>(`/api/v1/schemes/search?${q}`, signal);
  },

  get: (schemeId: string, signal?: AbortSignal) =>
    api.get<SchemeRead>(`/api/v1/schemes/${schemeId}`, signal),

  categories: (signal?: AbortSignal) =>
    api.get<SchemeCategoryRead[]>("/api/v1/schemes/categories", signal),
};
