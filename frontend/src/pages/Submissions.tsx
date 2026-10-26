import { useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import { useAsync } from "../hooks/useAsync";
import { api } from "../services/api";
import { AnalysisStatus, btnGhost, Card, Empty, ErrorBox, input, Loading, ReviewStatus } from "../components/ui";
import { formatDate } from "../utils/format";

export default function Submissions() {
  const { user } = useAuth();
  const [q, setQ] = useState("");
  const [language, setLanguage] = useState("");
  const [assignmentId, setAssignmentId] = useState("");
  const [reviewStatus, setReviewStatus] = useState("all");
  const [page, setPage] = useState(1);
  const langs = useAsync(() => api.languages(), []);
  const assignments = useAsync(() => api.assignments(), []);
  const list = useAsync(() => api.submissions({ q, language, assignment_id: assignmentId || undefined,
    review_status: user?.role === "professor" && reviewStatus !== "all" ? reviewStatus : undefined, page, page_size: 20 }),
    [q, language, assignmentId, reviewStatus, user?.role, page]);
  const pages = list.data ? Math.max(1, Math.ceil(list.data.total / list.data.page_size)) : 1;
  const reset = <T,>(set: (v: T) => void) => (v: T) => { set(v); setPage(1); };

  return (
    <div className="space-y-4">
      <header><p className="text-xs font-semibold uppercase tracking-[0.14em] text-emerald-200">Coursework</p>
        <h1 className="mt-2 text-3xl font-semibold tracking-tight">Submissions</h1>
        <p className="mt-1 text-sm text-slate-400">Search and filter the submissions available to your account.</p></header>
      <Card className="p-4">
        <div className="grid gap-3 sm:grid-cols-3">
          <label className="block text-xs font-medium text-slate-400">File name
            <input className={`${input} mt-1`} placeholder="Search file name" aria-label="Search file name" value={q} onChange={(e) => reset(setQ)(e.target.value)} />
          </label>
          <select className={input} aria-label="Language filter" value={language} onChange={(e) => reset(setLanguage)(e.target.value)}>
            <option value="">All languages</option>{langs.data?.languages.map((l) => <option key={l.id} value={l.id}>{l.name}</option>)}
          </select>
          <select className={input} aria-label="Assignment filter" value={assignmentId} onChange={(e) => reset(setAssignmentId)(e.target.value)}>
            <option value="">All assignments</option>{assignments.data?.items.map((a) => <option key={a.id} value={a.id}>{a.title}</option>)}
          </select>
          {user?.role === "professor" && <select className={input} aria-label="Review status filter" value={reviewStatus} onChange={(e) => reset(setReviewStatus)(e.target.value)}>
            <option value="all">All review statuses</option><option value="needs_review">Needs review</option><option value="reviewed">Reviewed</option>
          </select>}
        </div>
      </Card>
      {list.loading ? <Loading label="Loading submissions…" /> : list.error ? <ErrorBox message={list.error} onRetry={list.reload} /> :
        !list.data || list.data.items.length === 0 ? <Empty>{q || language || assignmentId || reviewStatus !== "all" ? "No submissions match these filters." :
          user?.role === "professor" ? "No submissions yet. They will appear after students submit code." : "You have not submitted any work yet."}</Empty> : (
          <Card className="overflow-hidden p-0"><div className="overflow-x-auto"><table className="w-full min-w-[760px] text-left text-sm">
            <thead className="bg-white/[0.03] text-xs uppercase tracking-wide text-slate-400"><tr><th className="px-4 py-3">File</th><th className="px-4 py-3">Assignment</th><th className="px-4 py-3">Student</th><th className="px-4 py-3">Language</th><th className="px-4 py-3">Analysis</th>{user?.role === "professor" && <th className="px-4 py-3">Review</th>}<th className="px-4 py-3">Submitted</th></tr></thead>
            <tbody>{list.data.items.map((s) => (
              <tr key={s.id} className="border-t border-white/10">
                <td className="px-4 py-3"><Link className="font-medium text-emerald-100 hover:underline" to={`/submissions/${s.id}`}>{s.original_filename}</Link></td>
                <td className="px-4 py-3">{s.assignment_title}</td><td className="px-4 py-3">{s.student_email ?? "You"}</td><td className="px-4 py-3">{s.language}</td>
                <td className="px-4 py-3"><AnalysisStatus status={s.latest_analysis_status} /></td>
                {user?.role === "professor" && <td className="px-4 py-3"><ReviewStatus status={s.review_status} /></td>}
                <td className="px-4 py-3 text-xs text-slate-400">{formatDate(s.submitted_at)}</td></tr>))}
          </tbody></table></div></Card>)}
      {list.data && list.data.total > 0 && <div className="flex items-center justify-between gap-3 text-sm text-slate-400">
        <span>{list.data.total} submission{list.data.total === 1 ? "" : "s"}</span>
        <div className="flex items-center gap-3">
          <button className={btnGhost} disabled={page <= 1} onClick={() => setPage(page - 1)}>Previous</button>
          <span>{page} / {pages}</span>
          <button className={btnGhost} disabled={page >= pages} onClick={() => setPage(page + 1)}>Next</button>
        </div>
      </div>
      }
    </div>
  );
}
