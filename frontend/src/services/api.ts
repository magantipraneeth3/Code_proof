import { createClient } from "./client";
import type { Analysis, Assignment, Language, Page, PublicAnalysisResult, PublicCompareResult, PublicSample, ReviewNote, Stats, SubmissionDetail, SubmissionSummary, User } from "../types";

export { ApiError } from "./client";

const BASE = (import.meta as any).env?.VITE_API_BASE_URL ?? "http://localhost:8000/api/v1";
const TOKEN_KEY = "codeproof.token"; // sessionStorage: cleared when the tab closes

export const tokenStore = {
  get: () => sessionStorage.getItem(TOKEN_KEY),
  set: (t: string) => sessionStorage.setItem(TOKEN_KEY, t),
  clear: () => sessionStorage.removeItem(TOKEN_KEY),
};

let unauthorizedHandler: () => void = () => {};
export const setUnauthorizedHandler = (fn: () => void) => { unauthorizedHandler = fn; };

const http = createClient({ baseUrl: BASE, getToken: tokenStore.get, onUnauthorized: () => unauthorizedHandler() });
const publicHttp = createClient({ baseUrl: BASE, getToken: () => null });

export interface AssignmentInput {
  title: string; description?: string; instructions?: string; allowed_languages?: string[]; due_date?: string | null;
}

export const api = {
  health: () => http.get<{ status: string; version: string; database: string }>("/health"),
  publicHealth: () => publicHttp.get<{ status: string; syntax_structure_analysis: string; authorship_model: string;
    syntax_and_structure_languages: string[]; similarity_languages: string[]; max_source_bytes: number }>("/public/health"),
  publicSamples: () => publicHttp.get<{ items: PublicSample[] }>("/public/samples"),
  publicAnalyze: (code: string, language: string | null, compare_samples = true) =>
    publicHttp.post<PublicAnalysisResult>("/public/analyze", { code, language, compare_samples }),
  publicCompare: (code_a: string, language_a: string, code_b: string, language_b: string) =>
    publicHttp.post<PublicCompareResult>("/public/compare", { code_a, language_a, code_b, language_b }),
  languages: () => http.get<{ languages: Language[] }>("/languages"),

  register: (email: string, password: string, role: "student" | "professor") =>
    http.post<{ access_token: string; user: User }>("/auth/register", { email, password, role }),
  login: (email: string, password: string) =>
    http.post<{ access_token: string; user: User }>("/auth/login", { email, password }),
  logout: () => http.post<void>("/auth/logout"),
  me: () => http.get<User>("/auth/me"),

  stats: () => http.get<Stats>("/dashboard/stats"),

  assignments: () => http.get<{ items: Assignment[] }>("/assignments"),
  assignment: (id: number) => http.get<Assignment>(`/assignments/${id}`),
  createAssignment: (body: AssignmentInput) => http.post<Assignment>("/assignments", body),
  deleteAssignment: (id: number) => http.del(`/assignments/${id}`),

  submissions: (params: Record<string, string | number | undefined>) => {
    const qs = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => v !== undefined && v !== "" && qs.set(k, String(v)));
    return http.get<Page<SubmissionSummary>>(`/submissions?${qs}`);
  },
  submission: (id: number) => http.get<SubmissionDetail>(`/submissions/${id}`),
  createSubmission: (assignment_id: number, filename: string, source: string, language?: string) =>
    http.post<SubmissionSummary>("/submissions", { assignment_id, filename, source, language: language || null }),
  uploadSubmission: (assignment_id: number, file: File, language?: string) => {
    const f = new FormData();
    f.set("assignment_id", String(assignment_id));
    if (language) f.set("language", language);
    f.set("file", file);
    return http.post<SubmissionSummary>("/submissions/upload", f);
  },
  deleteSubmission: (id: number) => http.del(`/submissions/${id}`),
  reviewNotes: (submission_id: number) => http.get<{ items: ReviewNote[] }>(`/submissions/${submission_id}/notes`),
  setReviewStatus: (submission_id: number, status: "needs_review" | "reviewed") =>
    http.patch<{ submission_id: number; review_status: "needs_review" | "reviewed"; reviewed_at: string | null }>(
      `/submissions/${submission_id}/review-status`, { status }),
  createReviewNote: (submission_id: number, body: string) =>
    http.post<ReviewNote>(`/submissions/${submission_id}/notes`, { body }),
  updateReviewNote: (submission_id: number, note_id: number, body: string) =>
    http.patch<ReviewNote>(`/submissions/${submission_id}/notes/${note_id}`, { body }),
  deleteReviewNote: (submission_id: number, note_id: number) =>
    http.del(`/submissions/${submission_id}/notes/${note_id}`),

  preview: (source: string, language?: string, filename?: string) =>
    http.post<Analysis>("/analysis/preview", { source, language: language || null, filename: filename || null }),
  rerun: (submission_id: number) => http.post<Analysis>("/analysis", { submission_id }),
  retry: (analysis_id: string) => http.post<Analysis>(`/analysis/${analysis_id}/retry`),

  createReport: (analysis_id: string) => http.post<{ report_id: string; download_url: string }>("/reports", { analysis_id }),
  downloadReport: (report_id: string) => http.blob(`/reports/${report_id}/download`),
};
