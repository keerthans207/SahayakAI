import { api } from "./api";
import type {
  ApplicationCreate,
  ApplicationRead,
  ApplicationUpdate,
  ApplicationReadiness,
} from "@/types/api";

export const applicationsService = {
  create: (body: ApplicationCreate, signal?: AbortSignal) =>
    api.post<ApplicationRead>("/api/v1/applications", body, signal),

  list: (signal?: AbortSignal) =>
    api.get<ApplicationRead[]>("/api/v1/applications", signal),

  get: (applicationId: string, signal?: AbortSignal) =>
    api.get<ApplicationRead>(`/api/v1/applications/${applicationId}`, signal),

  update: (applicationId: string, body: ApplicationUpdate, signal?: AbortSignal) =>
    api.patch<ApplicationRead>(`/api/v1/applications/${applicationId}`, body, signal),

  readiness: (applicationId: string, signal?: AbortSignal) =>
    api.get<ApplicationReadiness>(
      `/api/v1/applications/${applicationId}/readiness`,
      signal
    ),
};
