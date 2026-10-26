import type { Analysis } from "../types";
import { formatDate, metricLabel, modelSummary, statusLabel } from "../utils/format";
import { AnalysisStatus, Badge, Card } from "./ui";

export default function AnalysisView({ analysis: a }: { analysis: Analysis }) {
  const ok = a.analysis_status === "completed";
  return (
    <div className="space-y-4">
      <Card>
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex flex-wrap items-center gap-2"><AnalysisStatus status={a.analysis_status} /><Badge>{a.language ?? "Language unknown"}</Badge></div>
          <span className="text-xs text-slate-400">Run {a.analysis_id.slice(0, 8)} · {formatDate(a.created_at)}</span>
        </div>
        {a.message && <p className="mt-3 border-t border-white/10 pt-3 text-sm text-amber-100">{a.message}</p>}
      </Card>

      {ok && (
        <>
          <Card title="Syntax">
            {a.syntax_valid
              ? <p className="text-sm text-emerald-300">Valid syntax.</p>
              : <p className="text-sm text-red-300">Syntax error: {a.syntax_error ?? "unknown"}</p>}
          </Card>
          <Card title="Code metrics · descriptive only">
            <dl className="grid grid-cols-2 gap-3 sm:grid-cols-3">
              {Object.entries(a.code_metrics ?? {}).map(([k, v]) => (
                <div className="border-l-2 border-emerald-300/40 pl-3" key={k}><dt className="text-xs text-slate-400">{metricLabel(k)}</dt><dd className="mt-1 text-xl font-semibold tabular-nums">{String(v)}</dd></div>
              ))}
            </dl>
          </Card>
          <Card title="Structural observations">
            {a.structural_findings.length > 0 ? <ul className="space-y-2 text-sm">{a.structural_findings.map((f, i) => <li key={i} className="border-l-2 border-slate-500/40 pl-3">{f}</li>)}</ul> :
              <p className="text-sm text-slate-400">No structural observations were recorded for this source.</p>}
          </Card>
        </>
      )}

      <Card title="Evidence summary">
        <dl className="divide-y divide-white/10 text-sm">
          <div className="grid gap-2 py-3 sm:grid-cols-[190px_1fr]"><dt className="font-medium text-slate-300">Verified provenance</dt><dd className="text-slate-200">{a.provenance_summary} <span className="text-slate-400">Absence of provenance does not mean AI was not used.</span></dd></div>
          <div className="grid gap-2 py-3 sm:grid-cols-[190px_1fr]"><dt className="font-medium text-slate-300">Authorship model</dt><dd className="text-slate-200">{modelSummary(a)} <span className="text-xs text-slate-400">Status: {a.model_status}.</span></dd></div>
          <div className="grid gap-2 py-3 sm:grid-cols-[190px_1fr]"><dt className="font-medium text-slate-300">Code similarity</dt><dd className="text-slate-400">Not performed. Similarity comparison is not implemented.</dd></div>
          <div className="grid gap-2 py-3 sm:grid-cols-[190px_1fr]"><dt className="font-medium text-slate-300">Development history</dt><dd className="text-slate-400">Not analyzed. Git history is not connected.</dd></div>
          <div className="grid gap-2 py-3 sm:grid-cols-[190px_1fr]"><dt className="font-medium text-slate-300">Assessment</dt><dd><Badge>{a.authorship_assessment.toUpperCase()}</Badge><span className="ml-2 text-slate-400">A human review decision is separate.</span></dd></div>
        </dl>
      </Card>

      <Card title="Known limitations">
        <ul className="list-disc space-y-1 pl-5 text-sm text-slate-300">{a.limitations.map((l, i) => <li key={i}>{l}</li>)}</ul>
        <p className="mt-3 border-t border-white/10 pt-3 text-sm text-slate-300">Use this as decision support. Do not base an allegation of misconduct on this analysis alone.</p>
      </Card>
    </div>
  );
}
