import { FormEvent, useState } from "react";
import { Link } from "react-router-dom";
import { ArrowRight, ClipboardList } from "lucide-react";
import { useAuth } from "../auth/AuthContext";
import { useAsync } from "../hooks/useAsync";
import { api, ApiError } from "../services/api";
import { btn, Card, Empty, ErrorBox, input, Loading } from "../components/ui";
import { formatDate } from "../utils/format";

export default function Assignments() {
  const { user } = useAuth();
  const list = useAsync(() => api.assignments(), []);
  const langs = useAsync(() => api.languages(), []);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [instructions, setInstructions] = useState("");
  const [allowed, setAllowed] = useState<string[]>([]);
  const [due, setDue] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function create(e: FormEvent) {
    e.preventDefault(); setError(null); setBusy(true);
    try {
      await api.createAssignment({ title, description, instructions, allowed_languages: allowed,
                                   due_date: due ? new Date(due).toISOString() : null });
      setTitle(""); setDescription(""); setInstructions(""); setAllowed([]); setDue("");
      list.reload();
      setNotice("Assignment created.");
    } catch (err) { setError(err instanceof ApiError ? err.message : "Could not create the assignment."); }
    finally { setBusy(false); }
  }

  const toggle = (id: string) => setAllowed((a) => (a.includes(id) ? a.filter((x) => x !== id) : [...a, id]));

  return (
    <div className="space-y-6">
      <header><p className="text-xs font-semibold uppercase tracking-[0.14em] text-emerald-200">Coursework</p>
        <h1 className="mt-2 text-3xl font-semibold tracking-tight">Assignments</h1>
        <p className="mt-1 text-sm text-slate-400">{user?.role === "professor" ? "Create and manage programming assignments." : "Choose an assignment to review its instructions and submit your work."}</p></header>
      {user?.role === "professor" && (
        <Card title="Create assignment">
          <form onSubmit={create} className="space-y-3">
            <div className="grid gap-3 md:grid-cols-2">
              <label className="block text-sm">Title<input className={`${input} mt-1`} required maxLength={200} value={title} onChange={(e) => setTitle(e.target.value)} /></label>
              <label className="block text-sm">Due date<input className={`${input} mt-1`} type="datetime-local" value={due} onChange={(e) => setDue(e.target.value)} /></label>
              <label className="block text-sm">Description<textarea className={`${input} mt-1`} rows={3} value={description} onChange={(e) => setDescription(e.target.value)} /></label>
              <label className="block text-sm">Evaluation instructions<textarea className={`${input} mt-1`} rows={3} value={instructions} onChange={(e) => setInstructions(e.target.value)} /></label>
            </div>
            <fieldset className="text-sm"><legend className="mb-2 font-medium">Allowed languages <span className="font-normal text-slate-400">(none selected means any)</span></legend>
              {langs.loading ? <Loading label="Loading language options…" /> : langs.error ? <ErrorBox message={langs.error} /> :
              <div className="flex flex-wrap gap-x-5 gap-y-2">
                {langs.data?.languages.map((l) => (
                  <label key={l.id} className="flex items-center gap-1">
                    <input className="size-4 accent-emerald-300" type="checkbox" checked={allowed.includes(l.id)} onChange={() => toggle(l.id)} />
                    {l.name}<span className="text-xs text-slate-400">{l.status === "supported" ? "Analysis available" : "Analysis unavailable"}</span>
                  </label>))}
              </div>}</fieldset>
            <ErrorBox message={error} />
            {notice && <p role="status" className="text-sm text-emerald-100">{notice}</p>}
            <button className={btn} disabled={busy}>{busy ? "Creating…" : <><ClipboardList size={16} />Create assignment</>}</button>
          </form>
        </Card>
      )}
      {list.loading ? <Loading /> : list.error ? <ErrorBox message={list.error} /> :
        list.data?.items.length === 0 ? <Empty>{user?.role === "professor" ? "No assignments yet. Create your first one above." : "No assignments are available yet."}</Empty> :
        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
          {list.data?.items.map((a) => (
            <Link key={a.id} to={`/assignments/${a.id}`} className="group flex min-h-40 flex-col rounded-md border border-white/10 bg-navy-800 p-4 transition hover:border-emerald-300/30 hover:bg-[#1b2921]">
              <div className="flex items-start justify-between gap-3"><h2 className="font-semibold">{a.title}</h2><ArrowRight size={16} className="shrink-0 text-slate-400 group-hover:text-emerald-100" /></div>
              <p className="mt-2 line-clamp-2 text-sm text-slate-400">{a.description || "No description."}</p>
              <p className="mt-auto pt-4 text-xs text-slate-400">{a.allowed_languages.length ? a.allowed_languages.join(", ") : "Any language"} · Due {formatDate(a.due_date)}
                {a.submission_count !== null && ` · ${a.submission_count} submissions`}</p>
            </Link>))}
        </div>}
    </div>
  );
}
