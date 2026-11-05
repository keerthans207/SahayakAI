import type { ApplicationStatus } from "@/types/api";
import type { EligibilityOutcome } from "@/types/api";

export function applicationStatusColor(status: ApplicationStatus): string {
  switch (status) {
    case "approved": return "badge-active";
    case "rejected": case "closed": return "badge-error";
    case "ready_for_user_submission": case "ready_for_review": return "badge-info";
    case "submitted_by_user": case "under_verification": return "badge-warning";
    default: return "badge-info";
  }
}

export function eligibilityColor(outcome: EligibilityOutcome): string {
  switch (outcome) {
    case "likely_eligible": return "#16a34a";
    case "potentially_eligible": return "#2563eb";
    case "not_eligible": return "#dc2626";
    case "insufficient_information": return "#d97706";
    case "requires_official_verification": return "#7c3aed";
  }
}

export function eligibilityBg(outcome: EligibilityOutcome): string {
  switch (outcome) {
    case "likely_eligible": return "#f0fdf4";
    case "potentially_eligible": return "#eff6ff";
    case "not_eligible": return "#fef2f2";
    case "insufficient_information": return "#fffbeb";
    case "requires_official_verification": return "#f5f3ff";
  }
}

export function schemeStatusBadge(status: string): string {
  switch (status) {
    case "active": return "badge-active";
    case "inactive": case "closed": return "badge-error";
    default: return "badge-warning";
  }
}
