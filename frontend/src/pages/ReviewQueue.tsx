import { useState } from "react";
import { Link } from "react-router-dom";
import { ArrowRight, Check, RotateCcw } from "lucide-react";
import { useAsync } from "../hooks/useAsync";
import { api, ApiError } from "../services/api";
import { AnalysisStatus, btnGhost, Card, Empty, ErrorBox, Loading, ReviewStatus } from "../components/ui";
import { formatDate } from "../utils/format";

type Filter = "needs_review" | "reviewed" | "all";

export default function ReviewQueue() {
  const [filter, setFilter] = useState<Filter>("needs_review");
  const [page, setPage] = useState(1);
  const [busyId, setBusyId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const list = useAsync(() => api.submissions({
    review_status: filter === "all" ? undefined : filter,
    page,
    page_size: 20,
  }), [filter, page]);
  const totalPages = list.data ? Math.max(1, Math.ceil(list.data.total / list.data.page_size)) : 1;

  async function changeStatus(submissionId: number, status: "needs_review" | "reviewed") {
    setBusyId(submissionId);
    setError(null);
    try {
      await api.setReviewStatus(submissionId, status);
      list.reload();
    } catch (cause) {
      setError(cause instanceof ApiError ? cause.message : "Could not update review status.");
    } finally {
      setBusyId(null);
    }
  }

  return (
    <div className="space-y-6">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div><p className="text-xs font-semibold uppercase tracking-[0.14em] text-emerald-200">Professor workspace</p>
          <h1 className="mt-2 text-3xl font-semibold tracking-tight">Review queue</h1>
          <p className="mt-1 text-sm text-slate-400">Track human review status for submissions to your assignments.</p></div>
        <div className="inline-flex rounded-md border border-white/10 p-1" aria-label="Filter review status">
          {(["needs_review", "reviewed", "all"] as const).map((value) => (
            <button key={value} aria-pressed={filter === value} onClick={() => { setFilter(value); setPage(1); }}
              className={`min-h-9 rounded px-3 text-sm transition ${filter === value ? "bg-emerald-300/15 text-emerald-100" : "text-slate-300 hover:bg-white/5"}`}>
              {value === "needs_review" ? "Needs review" : value === "reviewed" ? "Reviewed" : "All"}
            </button>))}
        </div>
      </header>
      <ErrorBox message={error} />
      <Card className="overflow-hidden p-0">
        {list.loading ? <div className="p-5"><Loading label="Loading submissions…" /></div> : list.error ? <div className="p-5"><ErrorBox message={list.error} onRetry={list.reload} /></div> :
          !list.data || list.data.items.length === 0 ? <Empty>{filter === "needs_review" ? "No submissions need review." : "No submissions in this view."}</Empty> : (
            <div className="overflow-x-auto">
              <table className="w-full min-w-[800px] text-left text-sm">
                <thead className="bg-white/[0.03] text-xs uppercase tracking-wide text-slate-400">
                  <tr>{["Submission", "Assignment", "Student", "Language", "Analysis", "Review", "Submitted", ""].map((heading) => <th className="px-4 py-3 font-medium" key={heading}>{heading}</th>)}</tr>
                </thead>
                <tbody>
                  {list.data.items.map((submission) => (
                    <tr className="border-t border-white/10" key={submission.id}>
                      <td className="px-4 py-3"><Link className="font-medium text-emerald-100 hover:underline" to={`/submissions/${submission.id}`}>{submission.original_filename}</Link></td>
                      <td className="px-4 py-3">{submission.assignment_title}</td>
                      <td className="px-4 py-3">{submission.student_email}</td>
                      <td className="px-4 py-3">{submission.language}</td>
                      <td className="px-4 py-3"><AnalysisStatus status={submission.latest_analysis_status} /></td>
                      <td className="px-4 py-3"><ReviewStatus status={submission.review_status} /></td>
                      <td className="px-4 py-3 text-xs text-slate-400">{formatDate(submission.submitted_at)}</td>
                      <td className="px-4 py-3 text-right">
                        <button className={btnGhost} disabled={busyId === submission.id}
                          onClick={() => changeStatus(submission.id, submission.review_status === "reviewed" ? "needs_review" : "reviewed")}>
                          {submission.review_status === "reviewed" ? <RotateCcw size={14} /> : <Check size={14} />}
                          {busyId === submission.id ? "Saving…" : submission.review_status === "reviewed" ? "Reopen" : "Mark reviewed"}
                        </button>
                        <Link className="ml-2 inline-grid size-9 place-items-center rounded-md text-slate-300 hover:bg-white/5 hover:text-white"
                          aria-label={`Open ${submission.original_filename}`} to={`/submissions/${submission.id}`}><ArrowRight size={16} /></Link>
                      </td>
                    </tr>))}
                </tbody>
              </table>
            </div>)}
      </Card>
      {list.data && list.data.total > 0 && <div className="flex items-center justify-between gap-3 text-sm text-slate-400">
        <span>{list.data.total} submission{list.data.total === 1 ? "" : "s"}</span>
        <div className="flex items-center gap-3">
          <button className={btnGhost} disabled={page <= 1} onClick={() => setPage(page - 1)}>Previous</button>
          <span>{page} / {totalPages}</span>
          <button className={btnGhost} disabled={page >= totalPages} onClick={() => setPage(page + 1)}>Next</button>
        </div>
      </div>}
    </div>
  );
}