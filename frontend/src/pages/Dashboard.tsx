import { Link } from "react-router-dom";
import { ArrowRight, ClipboardCheck, ClipboardList, Code2, FileText } from "lucide-react";
import { useAuth } from "../auth/AuthContext";
import { useAsync } from "../hooks/useAsync";
import { api } from "../services/api";
import { btn, Card, Empty, ErrorBox, Loading } from "../components/ui";
import { formatDate } from "../utils/format";

export default function Dashboard() {
  const { user } = useAuth();
  const { data: s, error, loading, reload } = useAsync(() => api.stats(), []);
  if (loading) return <Loading />;
  if (error || !s) return <ErrorBox message={error} onRetry={reload} />;
  const professor = user?.role === "professor";
  const tiles: { label: string; value: number; to: string; icon: typeof ClipboardList }[] = professor ? [
    { label: "Assignments", value: s.total_assignments, to: "/assignments", icon: ClipboardList },
    { label: "Submissions", value: s.total_submissions, to: "/submissions", icon: FileText },
    { label: "Needs review", value: s.needs_review ?? 0, to: "/reviews", icon: ClipboardCheck },
  ] : [
    { label: "Assignments", value: s.total_assignments, to: "/assignments", icon: ClipboardList },
    { label: "Your submissions", value: s.total_submissions, to: "/submissions", icon: FileText },
    { label: "Completed analyses", value: s.completed_analyses, to: "/submissions", icon: Code2 },
  ];
  return (
    <div className="space-y-6">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div><p className="text-xs font-semibold uppercase tracking-[0.14em] text-emerald-200">{professor ? "Professor workspace" : "Student workspace"}</p>
          <h1 className="mt-2 text-3xl font-semibold tracking-tight">Overview</h1>
          <p className="mt-1 text-sm text-slate-400">{professor ? "A clear view of submissions that need your attention." : "Your assignments and submitted work in one place."}</p>
        </div>
        <div className="flex flex-wrap gap-2">
          {professor ? <><Link to="/assignments" className={btn}>Create assignment</Link><Link to="/reviews" className="rounded-md border border-white/15 px-4 py-2 text-sm hover:bg-white/5">Review queue</Link></> :
            <><Link to="/assignments" className={btn}>Browse assignments</Link><Link to="/workspace" className="rounded-md border border-white/15 px-4 py-2 text-sm hover:bg-white/5">Analyze code</Link></>}
        </div>
      </header>
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4">
        {tiles.map(({ label, value, to, icon: Icon }) => (
          <Link key={label} to={to} className="group rounded-md border border-white/10 bg-navy-800 p-4 transition hover:border-emerald-300/30 hover:bg-[#1b2921] focus-visible:outline focus-visible:outline-2 focus-visible:outline-emerald-300">
            <div className="flex items-center justify-between"><span className="text-sm text-slate-300">{label}</span><Icon size={17} className="text-emerald-200" aria-hidden="true" /></div>
            <p className="mt-4 text-3xl font-semibold tabular-nums">{value}</p>
            <span className="mt-3 inline-flex items-center gap-1 text-xs text-slate-400 group-hover:text-emerald-100">View details <ArrowRight size={13} /></span>
          </Link>
        ))}
      </div>
      <div className="max-w-4xl">
        <Card title="Recent submissions">
          {s.recent_submissions.length === 0 ? <Empty>{professor ? "No submissions yet. They will appear here when students submit work." : "Your submissions will appear here."}</Empty> :
            <div className="divide-y divide-white/10">{s.recent_submissions.map((r) => (
              <Link key={r.id} to={`/submissions/${r.id}`} className="flex flex-wrap items-center justify-between gap-2 py-3 first:pt-0 last:pb-0">
                <span><span className="block text-sm font-medium text-slate-100">{r.filename}</span><span className="text-xs text-slate-400">{r.language}</span></span>
                <span className="text-xs text-slate-400">{formatDate(r.submitted_at)}</span>
              </Link>))}</div>}
        </Card>
      </div>
    </div>
  );
}
