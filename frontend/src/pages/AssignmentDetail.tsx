import { FormEvent, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import { useAsync } from "../hooks/useAsync";
import { api, ApiError } from "../services/api";
import { AnalysisStatus, btn, btnDanger, btnGhost, Card, Empty, ErrorBox, input, Loading } from "../components/ui";
import { formatDate } from "../utils/format";

export default function AssignmentDetail() {
  const id = Number(useParams().id);
  const { user } = useAuth();
  const nav = useNavigate();
  const a = useAsync(() => api.assignment(id), [id]);
  const subs = useAsync(() => (user?.role === "professor" ? api.submissions({ assignment_id: id }) : Promise.resolve(null)), [id, user?.role]);
  const [filename, setFilename] = useState("solution.py");
  const [source, setSource] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [fileInputKey, setFileInputKey] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit(e: FormEvent) {
    e.preventDefault(); setError(null); setBusy(true);
    try {
      const s = file ? await api.uploadSubmission(id, file) : await api.createSubmission(id, filename, source);
      nav(`/submissions/${s.id}`);
    } catch (err) { setError(err instanceof ApiError ? err.message : "Submission failed."); }
    finally { setBusy(false); }
  }

  async function remove() {
    if (!window.confirm("Delete this assignment and all its submissions? This cannot be undone.")) return;
    try { await api.deleteAssignment(id); nav("/assignments"); }
    catch (err) { setError(err instanceof ApiError ? err.message : "Could not delete."); }
  }

  if (a.loading) return <Loading />;
  if (a.error || !a.data) return <ErrorBox message={a.error} />;
  const as = a.data;
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">{as.title}</h1>
      <Card>
        <p className="text-sm">{as.description || "No description."}</p>
        {as.instructions && <p className="mt-2 whitespace-pre-wrap text-sm text-slate-300">{as.instructions}</p>}
        <p className="mt-2 text-xs text-slate-500">Languages: {as.allowed_languages.length ? as.allowed_languages.join(", ") : "any"} · Due: {formatDate(as.due_date)}</p>
          <p className="mt-3 border-t border-white/10 pt-3 text-xs text-slate-400">Languages: {as.allowed_languages.length ? as.allowed_languages.join(", ") : "Any language"} · Due: {formatDate(as.due_date)}</p>
      </Card>
      <ErrorBox message={error} />
      {user?.role === "student" && (
        <Card title="Submit your code">
            <form onSubmit={submit} className="space-y-4">
              <label className="block text-sm font-medium">Upload source file
                <input key={fileInputKey} className={`${input} mt-1 file:mr-3 file:rounded file:border-0 file:bg-emerald-300/15 file:px-3 file:py-1.5 file:text-sm file:text-emerald-100`} type="file" accept=".py,.java,.js,.jsx,.ts,.tsx,.c,.h,.cpp,.cc,.hpp" onChange={(e) => setFile(e.target.files?.[0] ?? null)} />
            </label>
              {file && <div className="flex flex-wrap items-center justify-between gap-2 rounded-md border border-emerald-300/20 bg-emerald-300/5 px-3 py-2 text-sm"><span className="truncate">{file.name}</span><button type="button" className={btnGhost} onClick={() => { setFile(null); setFileInputKey((key) => key + 1); }}>Remove file</button></div>}
            {!file && (<>
                <p className="text-xs text-slate-400">Or paste source code</p>
                <label className="block text-sm">File name<input className={`${input} mt-1`} value={filename} onChange={(e) => setFilename(e.target.value)} /></label>
                <textarea className={`${input} min-h-64 font-mono text-xs leading-6`} rows={10} aria-label="Source code" value={source} onChange={(e) => setSource(e.target.value)} />
            </>)}
              <button className={btn} disabled={busy || (!file && !source.trim())}>{busy ? "Submitting and analyzing…" : "Submit code"}</button>
          </form>
        </Card>
      )}
      {user?.role === "professor" && (
        <>
          <Card title="Submissions">
            {subs.loading ? <Loading label="Loading assignment submissions…" /> : subs.error ? <ErrorBox message={subs.error} onRetry={subs.reload} /> : !subs.data || subs.data.items.length === 0 ? <Empty>No submissions yet.</Empty> :
              <div className="overflow-x-auto"><table className="w-full min-w-[620px] text-left text-sm"><thead className="text-xs uppercase tracking-wide text-slate-400"><tr><th className="px-3 py-2">Student</th><th className="px-3 py-2">File</th><th className="px-3 py-2">Language</th><th className="px-3 py-2">Analysis</th><th className="px-3 py-2">Submitted</th></tr></thead>
                <tbody>{subs.data.items.map((s) => (
                  <tr key={s.id} className="border-t border-white/10"><td className="px-3 py-3">{s.student_email}</td>
                    <td className="px-3 py-3"><Link className="text-emerald-100 hover:underline" to={`/submissions/${s.id}`}>{s.original_filename}</Link></td>
                    <td className="px-3 py-3">{s.language}</td><td className="px-3 py-3"><AnalysisStatus status={s.latest_analysis_status} /></td><td className="px-3 py-3 text-xs text-slate-400">{formatDate(s.submitted_at)}</td></tr>))}</tbody></table></div>}
          </Card>
          <button className={btnDanger} onClick={remove}>Delete assignment</button>
        </>
      )}
    </div>
  );
}
