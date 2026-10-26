export type Role = "student" | "professor" | "admin";
export interface User { id: number; email: string; role: Role }
export interface Language { id: string; name: string; extensions: string[]; status: string; analysis: string | null }

export interface Analysis {
  analysis_id: string;
  submission_id: number | null;
  analysis_status: string;
  language: string | null;
  syntax_valid: boolean | null;
  syntax_error: string | null;
  code_metrics: Record<string, unknown> | null;
  structural_findings: string[];
  evidence_category: string;
  model_status: string;
  model_version: string | null;
  authorship_assessment: string;
  probability: number | null;
  model_reason: string | null;
  provenance_summary: string;
  limitations: string[];
  message: string | null;
  created_at: string | null;
  completed_at: string | null;
}

export interface PublicSample {
  sample_id: string; name: string; language: string; category: string; source: string;
  license: string; authoring_process: string; authorship_label: string; label_verified: boolean;
  origin_verified: boolean; collection_date: string | null; code: string;
}
export interface PublicSimilarity {
  comparison_status: string; similarity_percent: number | null; structural_similarity_percent: number | null;
  method: string; shared_tokens: string[]; matching_regions: { code_a_lines: [number, number]; code_b_lines: [number, number]; matching_tokens: number; code_a_excerpt: string; code_b_excerpt: string }[];
  reference_sample: Omit<PublicSample, "code"> & { provenance_status: string } | null;
  provenance_status_a: string; provenance_status_b: string; explanation: string;
}
export interface PublicAnalysisResult {
  analysis_id: string; language: string | null; analysis_status: string; created_at: string;
  syntax_valid: boolean | null; syntax_error: string | null; metrics: Record<string, unknown> | null;
  structural_findings: string[]; similarity_results: PublicSimilarity[]; samples_compared: number;
  provenance: { status: string; evidence: string[]; explanation: string };
  authorship_assessment: { result: string; ai_likelihood_percent: number | null; model_status: string;
    probability_calibrated: boolean; model_version: string | null; explanation: string };
  explanation: string; limitations: string[]; message: string | null;
  language_detection: { detected_language: string | null; confidence: string; candidates: string[];
    selection_status: "detected" | "manual" | "matches" | "mismatch" | "unconfirmed" | "ambiguous" | "unknown" };
  syntax: { status: "valid" | "invalid" | "unable_to_validate"; message: string | null;
    errors: { line?: number | null; column?: number | null; message: string }[]; validation: "complete" | "partial" | "unavailable" };
  structure: { status: string; summary: string; metrics: Record<string, number> | null };
  similarity: { status: "available" | "unavailable"; score: number | null; reference_id: string | null;
    ngram_similarity_percent: number | null; reference_title: string | null; method: string | null;
    matched_fragments: PublicSimilarity["matching_regions"] };
}
export interface PublicCompareResult extends Partial<PublicSimilarity> {
  comparison_status: string; similarity_percent: number | null; ngram_similarity_percent?: number | null;
  explanation: string; language?: string;
}

export interface Assignment {
  id: number; professor_id: number; title: string; description: string; instructions: string;
  allowed_languages: string[]; due_date: string | null; created_at: string; updated_at: string;
  submission_count: number | null;
}

export interface SubmissionSummary {
  id: number; assignment_id: number; assignment_title: string; student_id: number;
  student_email: string | null; original_filename: string; language: string;
  submission_status: string; submitted_at: string;
  latest_analysis_id: string | null; latest_analysis_status: string | null;
  review_status: "needs_review" | "reviewed" | null; reviewed_at: string | null;
}
export interface SubmissionDetail extends SubmissionSummary { source: string | null; analyses: Analysis[] }
export interface ReviewNote {
  id: number; submission_id: number; author_email: string; body: string;
  created_at: string; updated_at: string;
}
export interface Page<T> { items: T[]; total: number; page: number; page_size: number }

export interface Stats {
  total_assignments: number; total_submissions: number; completed_analyses: number;
  needs_review?: number;
  recent_submissions: { id: number; filename: string; language: string; submitted_at: string }[];
}
