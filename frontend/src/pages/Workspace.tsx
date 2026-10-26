import { useState } from "react";
import { Copy, FileCode2, RotateCcw, WandSparkles } from "lucide-react";
import AnalysisView from "../components/AnalysisView";
import { useAsync } from "../hooks/useAsync";
import { api, ApiError } from "../services/api";
import { btn, btnGhost, Card, Empty, ErrorBox, input, Loading } from "../components/ui";
import type { Analysis } from "../types";
import { formatBytes } from "../utils/format";

const MAX_BYTES = 1_000_000;

export default function Workspace() {
  const langs = useAsync(() => api.languages(), []);
  const [code, setCode] = useState("");
  const [language, setLanguage] = useState("python");
  const [filename, setFilename] = useState<string | undefined>();
  const [result, setResult] = useState<Analysis | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [copied, setCopied] = useState(false);
  const [copyError, setCopyError] = useState<string | null>(null);
  const currentBytes = new TextEncoder().encode(code).length;

  async function analyze() {
    setError(null);
    if (currentBytes > MAX_BYTES) { setError(`Source exceeds the ${formatBytes(MAX_BYTES)} limit.`); return; }
    setBusy(true);
    try { setResult(await api.preview(code, language, filename)); }
    catch (e) { setResult(null); setError(e instanceof ApiError ? e.message : "Analysis request failed."); }
    finally { setBusy(false); }
  }

  async function onFile(f: File | undefined) {
    if (!f) return;
    if (f.size > MAX_BYTES) { setError(`File exceeds the ${formatBytes(MAX_BYTES)} limit.`); return; }
    try { setError(null); setCode(await f.text()); setFilename(f.name); }
    catch { setError("Could not read this file. Choose a text source file and try again."); }
  }

  const clear = () => { setCode(""); setResult(null); setError(null); setCopyError(null); setFilename(undefined); };
  async function copySource() {
    try { await navigator.clipboard.writeText(code); setCopied(true); setCopyError(null); setTimeout(() => setCopied(false), 1500); }
    catch { setCopyError("Clipboard access is unavailable in this browser context."); }
  }

  return (
    <div className="space-y-4">
      <header><p className="text-xs font-semibold uppercase tracking-[0.14em] text-emerald-200">Static analysis</p>
        <h1 className="mt-2 text-3xl font-semibold tracking-tight">Analysis workspace</h1>
        <p className="mt-1 max-w-3xl text-sm text-slate-400">Preview code without creating a submission. Source is parsed, never executed, and is not stored.</p></header>
      <div className="grid gap-6 lg:grid-cols-2">
        <Card className="p-0">
          <div className="flex flex-wrap items-center justify-between gap-3 border-b border-white/10 px-4 py-3">
            <span className="flex items-center gap-2 text-sm font-medium"><FileCode2 size={16} className="text-emerald-200" />Source</span>
            <span className={`text-xs tabular-nums ${currentBytes > MAX_BYTES ? "text-red-200" : "text-slate-400"}`}>{formatBytes(currentBytes)} / {formatBytes(MAX_BYTES)}</span>
          </div>
          <div className="flex flex-wrap items-center gap-3 p-4">
            <label className="sr-only" htmlFor="analysis-language">Language</label>
            <select id="analysis-language" className={`${input} w-auto min-w-36`} value={language} onChange={(e) => setLanguage(e.target.value)}>
              {langs.data?.languages.map((l) => <option key={l.id} value={l.id}>{l.name}{l.status !== "supported" ? " (not yet supported)" : ""}</option>)}
            </select>
            <label className="inline-flex min-h-10 cursor-pointer items-center gap-2 rounded-md border border-white/15 px-3 text-sm hover:bg-white/5">
              <FileCode2 size={15} aria-hidden="true" />Open file
              <input className="sr-only" type="file" aria-label="Upload source file" accept=".py,.java,.js,.jsx,.ts,.tsx,.c,.h,.cpp,.cc,.hpp" onChange={(e) => onFile(e.target.files?.[0])} />
            </label>
          </div>
          <textarea className="min-h-[360px] w-full resize-y border-y border-white/10 bg-[#111a15] px-4 py-3 font-mono text-xs leading-6 text-slate-100 placeholder:text-slate-600 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-emerald-400/30" spellCheck={false} aria-label="Source code" value={code}
                    onChange={(e) => { setCode(e.target.value); setResult(null); }} placeholder="Paste source code here…" />
          <div className="flex flex-wrap items-center gap-2 p-4">
            <button className={btn} disabled={busy || !code.trim() || currentBytes > MAX_BYTES} onClick={analyze}><WandSparkles size={15} />{busy ? "Analyzing…" : "Run analysis"}</button>
            <button className={btnGhost} onClick={copySource} disabled={!code}><Copy size={15} />{copied ? "Copied" : "Copy source"}</button>
            <button className={btnGhost} onClick={clear}><RotateCcw size={15} />Clear</button>
          </div>
        </Card>
        <div>
          <ErrorBox message={error} />
          <ErrorBox message={copyError} />
          {busy ? <Card><Loading label="Analyzing source…" /></Card> : result ? <AnalysisView analysis={result} /> : !error && <Empty>Analysis results will appear here when a run completes.</Empty>}
        </div>
      </div>
    </div>
  );
}
