// ============================================================
// API types — derived directly from backend Pydantic schemas.
// Do not add fields that do not exist in the backend contracts.
// ============================================================

// ---- Common ----
export interface Page<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

export interface ApiError {
  error: string;
  detail?: string | unknown;
  request_id?: string;
}

// ---- Health ----
export interface HealthResponse {
  status: string;
  app: string;
  version: string;
}

export interface ReadyResponse {
  status: string;
  database: boolean;
  llm_provider: string;
  vector_store: string;
  search_provider: string;
  speech_provider: string;
  details: Record<string, string>;
}

// ---- Chat ----
export interface ChatSessionCreate {
  title?: string;
  preferred_language?: string;
}

export interface ChatSessionRead {
  id: string;
  title?: string;
  language?: string;
  created_at: string;
  updated_at: string;
}

export interface ChatTurnCreate {
  content: string;
  language?: string;
}

export interface ChatTurnResponse {
  message_id: string;
  role: "assistant";
  content: string;
  language?: string;
  detected_language?: string;
  intent?: string;
  selected_scheme?: string;
  eligibility_outcome?: string;
  missing_requirements: string[];
  official_sources: OfficialSource[];
  request_id?: string;
}

export interface ChatMessageRead {
  id: string;
  role: "user" | "assistant" | "tool";
  content: string;
  language?: string;
  created_at: string;
}

export interface OfficialSource {
  title?: string;
  url?: string;
  publisher?: string;
  page_number?: number;
  retrieved_at?: string;
  source_status?: string;
  is_stale?: boolean;
}

// ---- Schemes ----
export interface SchemeSummary {
  scheme_id: string;
  official_name: string;
  category: string;
  government_level: string;
  applicable_state?: string;
  benefit_amount?: string;
  scheme_status: string;
  confidence_status: string;
}

export interface SchemeRead extends SchemeSummary {
  description: string;
  department?: string;
  applicable_district?: string;
  target_beneficiaries: string[];
  benefit_description?: string;
  benefit_frequency?: string;
  required_documents: string[];
  prerequisite_services: string[];
  application_start_date?: string;
  application_deadline?: string;
  application_url?: string;
  official_contact?: string;
  source_publication_date?: string;
  last_verified_at?: string;
}

export interface SchemeCategoryRead {
  category: string;
  count: number;
}

// ---- Eligibility ----
export type EligibilityOutcome =
  | "likely_eligible"
  | "potentially_eligible"
  | "not_eligible"
  | "insufficient_information"
  | "requires_official_verification";

export type RequirementStatus = "satisfied" | "not_satisfied" | "unknown";

export interface RequirementResult {
  rule_type: string;
  description?: string;
  status: RequirementStatus;
  detail?: string;
}

export interface EligibilityEvaluationRequest {
  scheme_id: string;
  user_id?: string;
  profile: UserProfileSnapshot;
}

export interface EligibilityRead {
  id: string;
  user_id?: string;
  scheme_id: string;
  outcome: EligibilityOutcome;
  requirements_satisfied: RequirementResult[];
  requirements_not_satisfied: RequirementResult[];
  unknown_requirements: RequirementResult[];
  missing_information: string[];
  supporting_evidence: string[];
  next_steps: string[];
}

// ---- Documents ----
export interface DocumentUploadAck {
  document_id: string;
  document_type: string;
  original_filename: string;
  size_bytes: number;
}

export interface DocumentAssessment {
  document_type?: string;
  extracted_fields: Record<string, unknown>;
  missing_fields: string[];
  dates_to_check: string[];
  notes: string[];
  is_genuine: null;
  redacted: boolean;
}

export interface DocumentRead {
  id: string;
  user_id: string;
  document_type: string;
  original_filename: string;
  mime_type?: string;
  size_bytes: number;
  created_at: string;
  assessment: DocumentAssessment;
}

// ---- Applications ----
export type ApplicationStatus =
  | "discovered"
  | "eligibility_pending"
  | "eligible_pending_documents"
  | "documents_incomplete"
  | "ready_for_review"
  | "ready_for_user_submission"
  | "submitted_by_user"
  | "under_verification"
  | "approved"
  | "rejected"
  | "closed";

export interface ApplicationCreate {
  scheme_id: string;
  required_documents?: string[];
  prerequisites?: string[];
}

export interface ApplicationUpdate {
  status?: ApplicationStatus;
  completed_fields?: Record<string, unknown>;
  notes?: string;
}

export interface ApplicationRead {
  id: string;
  user_id: string;
  scheme_id: string;
  status: ApplicationStatus;
  required_documents: string[];
  completed_fields: Record<string, unknown>;
  prerequisites: string[];
  notes?: string;
  created_at: string;
  updated_at: string;
}

export interface ApplicationReadiness {
  application_id: string;
  scheme_id: string;
  status: ApplicationStatus;
  required_documents: string[];
  uploaded_documents: string[];
  missing_documents: string[];
  completed_fields: Record<string, unknown>;
  missing_fields: string[];
  prerequisites_met: boolean;
  prerequisites: string[];
  ready: boolean;
  report: string;
}

// ---- Profile ----
export interface UserProfileSnapshot {
  age?: number;
  disability_percentage?: number;
  disability_category?: string;
  income_amount?: number;
  income_range?: string;
  education_level?: string;
  course?: string;
  institution_type?: string;
  state?: string;
  district?: string;
  social_category?: string;
  employment_status?: string;
  udid_status?: string;
  otr_status?: string;
  has_aadhaar?: boolean;
  available_documents?: string[];
}

export interface ProfileUpdate extends UserProfileSnapshot {
  preferred_language?: string;
}

export interface UserProfileRead extends ProfileUpdate {
  user_id: string;
}

// ---- Speech ----
export interface TranscribeResponse {
  text: string;
  detected_language?: string;
}

export interface SynthesizeRequest {
  text: string;
  language?: string;
  voice?: string;
}

export interface SynthesizeResponse {
  audio_base64?: string;
  content_type: string;
  available: boolean;
  message?: string;
}
