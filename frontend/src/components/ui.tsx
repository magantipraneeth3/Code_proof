import { ReactNode } from "react";
import { AlertCircle, CircleHelp, LoaderCircle } from "lucide-react";
import { statusLabel } from "../utils/format";

export const btn = "inline-flex items-center justify-center gap-2 rounded-md bg-emerald-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-emerald-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-emerald-300 disabled:cursor-not-allowed disabled:opacity-50";
export const btnGhost = "inline-flex items-center justify-center gap-2 rounded-md border border-white/15 px-4 py-2 text-sm font-medium text-slate-100 transition hover:bg-white/5 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-emerald-300 disabled:cursor-not-allowed disabled:opacity-50";
export const btnDanger = "inline-flex items-center justify-center gap-2 rounded-md border border-red-300/30 px-4 py-2 text-sm font-medium text-red-200 transition hover:bg-red-400/10 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-red-300 disabled:cursor-not-allowed disabled:opacity-50";
export const input = "w-full rounded-md border border-white/15 bg-[#111a15] px-3 py-2 text-sm text-slate-100 placeholder:text-slate-500 focus:border-emerald-400 focus:outline-none focus:ring-2 focus:ring-emerald-400/20";

export function Card({ title, children, className = "" }: { title?: string; children: ReactNode; className?: string }) {
  return (
    <section className={`rounded-md border border-white/10 bg-navy-800 p-5 shadow-[0_12px_36px_rgba(0,0,0,0.12)] ${className}`}>
      {title && <h2 className="mb-4 text-sm font-semibold tracking-wide text-slate-100">{title}</h2>}
      {children}
    </section>
  );
}

export function ErrorBox({ message, onRetry }: { message: string | null; onRetry?: () => void }) {
  return message ? (
    <div role="alert" className="flex flex-wrap items-center justify-between gap-3 rounded-md border border-red-300/30 bg-red-950/40 p-3 text-sm text-red-100">
      <span className="flex items-center gap-2"><AlertCircle size={16} aria-hidden="true" />{message}</span>
      {onRetry && <button className={btnGhost} onClick={onRetry}>Try again</button>}
    </div>
  ) : null;
}

export function Loading({ label = "Loading…" }: { label?: string }) {
  return <p className="flex items-center gap-2 py-2 text-sm text-slate-300" role="status"><LoaderCircle size={16} className="animate-spin text-emerald-300" aria-hidden="true" />{label}</p>;
}

export function Empty({ children }: { children: ReactNode }) {
  return <div className="flex min-h-28 flex-col items-center justify-center gap-2 rounded-md border border-dashed border-white/15 px-5 py-6 text-center text-sm text-slate-300"><CircleHelp size={18} className="text-slate-400" aria-hidden="true" />{children}</div>;
}

export function Badge({ children, tone = "slate" }: { children: ReactNode; tone?: "slate" | "green" | "amber" | "red" }) {
  const tones = { slate: "border-white/15 bg-white/5 text-slate-200", green: "border-emerald-300/20 bg-emerald-400/10 text-emerald-200",
                  amber: "border-amber-300/20 bg-amber-400/10 text-amber-100", red: "border-red-300/20 bg-red-400/10 text-red-100" };
  return <span className={`inline-flex items-center rounded border px-2 py-1 text-xs font-medium ${tones[tone]}`}>{children}</span>;
}

export function AnalysisStatus({ status }: { status: string | null | undefined }) {
  const tone = status === "completed" ? "green" : status === "failed" ? "red" : status ? "amber" : "slate";
  return <Badge tone={tone}>{statusLabel(status)}</Badge>;
}

export function ReviewStatus({ status }: { status: string | null | undefined }) {
  return <Badge tone={status === "reviewed" ? "green" : "amber"}>{status === "reviewed" ? "Reviewed" : "Needs review"}</Badge>;
}
