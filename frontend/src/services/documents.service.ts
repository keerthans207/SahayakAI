import { api } from "./api";
import type { DocumentUploadAck, DocumentRead, DocumentAssessment } from "@/types/api";

export const documentsService = {
  upload: (file: File, schemeId?: string, signal?: AbortSignal) => {
    const fd = new FormData();
    fd.append("file", file);
    const path = schemeId
      ? `/api/v1/documents/upload?scheme_id=${encodeURIComponent(schemeId)}`
      : "/api/v1/documents/upload";
    return api.upload<DocumentUploadAck>(path, fd, signal);
  },

  get: (documentId: string, signal?: AbortSignal) =>
    api.get<DocumentRead>(`/api/v1/documents/${documentId}`, signal),

  getAssessment: (documentId: string, signal?: AbortSignal) =>
    api.get<DocumentAssessment>(`/api/v1/documents/${documentId}/assessment`, signal),

  delete: (documentId: string) =>
    api.delete<void>(`/api/v1/documents/${documentId}`),
};
