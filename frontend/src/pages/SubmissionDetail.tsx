import { useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import AnalysisView from "../components/AnalysisView";
import ReviewNotes from "../components/ReviewNotes";
import { useAsync } from "../hooks/useAsync";
import { api, ApiError } from "../services/api";
import { AnalysisStatus, btn, btnDanger, btnGhost, Card, ErrorBox, Loading, ReviewStatus } from "../components/ui";
import { formatDate } from "../utils/format";

export default function SubmissionDetail() {
  const id = Number(useParams().id);
  const { user } = useAuth();
  const nav = useNavigate();
  const s = useAsync(() => api.submission(id), [id]);
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [selected, setSelected] = useState<number | null>(null);

  async function act(name: string, fn: () => Promise<unknown>) {
    setBusy(name); setError(null);
    try { await fn(); } catch (e) { setError(e instanceof ApiError ? e.message : "Action failed."); }
    finally { setBusy(null); }
  }

  if (s.loading) return <Loading />;
  if (s.error || !s.data) return <ErrorBox message={s.error} />;
  const sub = s.data;
  const idx = selected ?? sub.analyses.length - 1;
  const analysis = sub.analyses[idx];

  const makeReport = () => act("report", async () => {
    const r = await api.createReport(analysis.analysis_id);
    const blob = await api.downloadReport(r.report_id);
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url; link.download = `codeproof-report-${r.report_id}.pdf`; link.click();
    window.setTimeout(() => URL.revokeObjectURL(url), 1000);
    setNotice("Evidence report generated and downloaded.");
  });

  const changeReview = () => act("review", async () => {
    await api.setReviewStatus(sub.id, sub.review_status === "reviewed" ? "needs_review" : "reviewed");
    s.reload();
    setNotice(sub.review_status === "reviewed" ? "Submission returned to the review queue." : "Submission marked reviewed.");
  });

  return (
    <div className="space-y-6">
      <header className="flex flex-wrap items-start justify-between gap-4">
        <div><p className="text-xs font-semibold uppercase tracking-[0.14em] text-emerald-200">Submission detail</p>
          <h1 className="mt-2 break-all text-2xl font-semibold tracking-tight">{sub.original_filename}</h1></div>
        <div className="flex flex-wrap gap-2">{analysis && <AnalysisStatus status={analysis.analysis_status} />}
          {user?.role === "professor" && <ReviewStatus status={sub.review_status} />}</div>
      </header>
      <Card>
        <dl className="grid gap-4 text-sm sm:grid-cols-2 lg:grid-cols-4">
          <div><dt className="text-xs text-slate-400">Assignment</dt><dd className="mt-1 font-medium">{sub.assignment_title}</dd></div>
          {sub.student_email && <div><dt className="text-xs text-slate-400">Student</dt><dd className="mt-1 font-medium">{sub.student_email}</dd></div>}
          <div><dt className="text-xs text-slate-400">Language</dt><dd className="mt-1 font-medium">{sub.language}</dd></div>
          <div><dt className="text-xs text-slate-400">Submitted</dt><dd className="mt-1 font-medium">{formatDate(sub.submitted_at)}</dd></div>
        </dl>
      </Card>
      <ErrorBox message={error} />
      {notice && <p className="text-sm text-emerald-100" role="status">{notice}</p>}
      {user?.role === "professor" && <ReviewNotes submissionId={sub.id} />}
      <div className="flex flex-wrap gap-3">
        {user?.role === "professor" && <button className={btnGhost} disabled={!!busy} onClick={changeReview}>
          {sub.review_status === "reviewed" ? "Return to review queue" : "Mark reviewed"}</button>}
        <button className={btnGhost} disabled={!!busy} onClick={() => act("rerun", async () => { await api.rerun(sub.id); setSelected(null); s.reload(); })}>
          {busy === "rerun" ? "Running…" : "Run analysis again"}</button>
        {analysis?.analysis_status === "failed" && (
          <button className={btn} disabled={!!busy} onClick={() => act("retry", async () => { await api.retry(analysis.analysis_id); setSelected(null); s.reload(); })}>Retry failed analysis</button>)}
        {user?.role === "professor" && analysis && (
          <button className={btn} disabled={!!busy} onClick={makeReport}>{busy === "report" ? "Generating…" : "Generate PDF report"}</button>)}
        <button className={btnDanger} disabled={!!busy} onClick={() => {
          if (window.confirm("Delete this submission and its stored file? This cannot be undone."))
            act("delete", async () => { await api.deleteSubmission(sub.id); nav("/submissions"); });
        }}>Delete submission</button>
      </div>
      {sub.analyses.length > 1 && (
        <label className="block text-sm">Analysis run
          <select className={`${btnGhost} ml-2`} value={idx} onChange={(e) => setSelected(Number(e.target.value))}>
            {sub.analyses.map((a, i) => <option key={a.analysis_id} value={i}>#{i + 1} · {formatDate(a.created_at)}</option>)}
          </select></label>)}
      {analysis ? <AnalysisView analysis={analysis} /> : <Card>No analysis has been run yet.</Card>}
      <Card title="Submitted source">
        {sub.source === null ? <p className="text-sm text-amber-200">The stored file is no longer available.</p> :
          <pre className="max-h-96 overflow-auto rounded bg-navy-900 p-3 text-xs">{sub.source}</pre>}
      </Card>
    </div>
  );
}
