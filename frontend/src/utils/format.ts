export const STATUS_LABELS: Record<string, string> = {
  completed: "Analysis completed",
  unsupported_language: "Language not supported yet",
  rejected_empty: "Empty input",
  rejected_too_large: "File too large",
  failed: "Analysis failed",
};

export function statusLabel(status: string | null | undefined): string {
  if (!status) return "Not analyzed";
  return STATUS_LABELS[status] ?? status;
}

export function metricLabel(key: string): string {
  const s = key.replace(/_/g, " ");
  return s.charAt(0).toUpperCase() + s.slice(1);
}

export function formatBytes(bytes: number): string {
  if (bytes < 1_000) return `${bytes} B`;
  if (bytes < 1_000_000) return `${(bytes / 1_000).toFixed(1)} KB`;
  return `${(bytes / 1_000_000).toFixed(1)} MB`;
}

export function formatDate(iso: string | null | undefined): string {
  if (!iso) return "—";
  const d = new Date(iso.endsWith("Z") || /[+-]\d\d:\d\d$/.test(iso) ? iso : iso + "Z");
  return Number.isNaN(d.getTime()) ? iso : d.toLocaleString();
}

/** The UI never shows a probability unless the backend returned a validated model's number. */
export function modelSummary(a: { model_status: string; probability: number | null; authorship_assessment: string }): string {
  if (a.model_status !== "available" || a.probability === null) {
    return "No validated model is configured. No authorship prediction was made.";
  }
  return `Model output: ${a.authorship_assessment} (see model card for evaluation context).`;
}
