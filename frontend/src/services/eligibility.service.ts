import { api } from "./api";
import type { EligibilityEvaluationRequest, EligibilityRead } from "@/types/api";

export const eligibilityService = {
  evaluate: (body: EligibilityEvaluationRequest, signal?: AbortSignal) =>
    api.post<EligibilityRead>("/api/v1/eligibility/evaluate", body, signal),

  get: (assessmentId: string, signal?: AbortSignal) =>
    api.get<EligibilityRead>(`/api/v1/eligibility/${assessmentId}`, signal),
};
