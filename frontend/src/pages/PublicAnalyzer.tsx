import { FormEvent, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ArrowRight, Check, LoaderCircle, ShieldCheck, Sparkles } from "lucide-react";
import PublicAnalysisResults from "../components/PublicAnalysisResults";
import PublicCodeEditor from "../components/PublicCodeEditor";
import { api, ApiError } from "../services/api";
import type { PublicAnalysisResult, PublicCompareResult, PublicSample } from "../types";
import { btn, btnGhost, ErrorBox } from "../components/ui";
import { formatBytes } from "../utils/format";

const DEFAULT_LIMIT = 1_000_000;

type Mode = "analyze" | "compare";

export default function PublicAnalyzer() {
  const [mode, setMode] = useState<Mode>("analyze");
  const [code, setCode] = useState("");
  const [language, setLanguage] = useState("python");
  const [referenceCode, setReferenceCode] = useState("");
  const [referenceLanguage, setReferenceLanguage] = useState("python");
  const [compareSamples, setCompareSamples] = useState(true);
  const [maxBytes, setMaxBytes] = useState(DEFAULT_LIMIT);
  const [samples, setSamples] = useState<PublicSample[]>([]);
  const [serviceError, setServiceError] = useState<string | null>(null);
  const [inputError, setInputError] = useState<string | null>(null);
  const [requestError, setRequestError] = useState<string | null>(null);
  const [analysis, setAnalysis] = useState<PublicAnalysisResult | null>(null);
  const [comparison, setComparison] = useState<PublicCompareResult | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    let active = true;
    api.publicHealth().then((health) => {
      if (!active) return;
      setMaxBytes(health.max_source_bytes);
      setServiceError(null);
    }).catch((error: unknown) => {
      if (active) setServiceError(error instanceof ApiError ? error.message : "Public analysis API is unavailable.");
    });
    api.publicSamples().then((response) => {
      if (active) setSamples(response.items);
    }).catch(() => {
      if (active) setSamples([]);
    });
    return () => { active = false; };
  }, []);

  const primaryBytes = new TextEncoder().encode(code).length;
  const referenceBytes = new TextEncoder().encode(referenceCode).length;

  function onPrimaryCode(value: string) {
    setCode(value);
    setAnalysis(null);
    setComparison(null);
    setRequestError(null);
  }

  function onReferenceCode(value: string) {
    setReferenceCode(value);
    setComparison(null);
    setRequestError(null);
  }

  function validateInputs(compare: boolean) {
    if (!code.trim()) {
      setInputError("Paste or upload source code before continuing.");
      return false;
    }
    if (primaryBytes > maxBytes || (compare && referenceBytes > maxBytes)) {
      setInputError(`Each source sample must be no larger than ${formatBytes(maxBytes)}.`);
      return false;
    }
    if (compare && !referenceCode.trim()) {
      setInputError("Add reference code in the second editor to compare samples.");
      return false;
    }
    setInputError(null);
    return true;
  }

  async function analyze(event: FormEvent) {
    event.preventDefault();
    if (!validateInputs(false)) return;
    setBusy(true);
    setAnalysis(null);
    setComparison(null);
    setRequestError(null);
    try {
      const response = await api.publicAnalyze(code, language === "auto" ? null : language, compareSamples);
      setAnalysis(response);
      if (language === "auto" && response.language_detection.detected_language) {
        setLanguage(response.language_detection.detected_language);
      }
      setServiceError(null);
    } catch (error) {
      setRequestError(error instanceof ApiError ? error.message : "The analysis request failed. Check the connection and retry.");
    } finally {
      setBusy(false);
    }
  }

  async function compare(event: FormEvent) {
    event.preventDefault();
    if (!validateInputs(true)) return;
    setBusy(true);
    setAnalysis(null);
    setComparison(null);
    setRequestError(null);
    try {
      const response = await api.publicCompare(code, language, referenceCode, referenceLanguage);
      setComparison(response);
      setServiceError(null);
    } catch (error) {
      setRequestError(error instanceof ApiError ? error.message : "The comparison request failed. Check the connection and retry.");
    } finally {
      setBusy(false);
    }
  }

  async function retryRequest() {
    setBusy(true);
    setRequestError(null);
    try {
      if (mode === "analyze") setAnalysis(await api.publicAnalyze(code, language === "auto" ? null : language, compareSamples));
      else setComparison(await api.publicCompare(code, language, referenceCode, referenceLanguage));
      setServiceError(null);
    } catch (error) {
      setRequestError(error instanceof ApiError ? error.message : "The request failed again. Check the connection and retry.");
    } finally {
      setBusy(false);
    }
  }

  function setInputErrorForEditor(message: string | null) {
    setInputError(message);
  }

  return (
    <div className="min-h-screen bg-[#0b1020] text-slate-100">
      <header className="border-b border-slate-800 bg-[#0b1020]/95">
        <div className="mx-auto flex max-w-[1440px] flex-wrap items-center justify-between gap-3 px-4 py-3 sm:px-6">
          <Link to="/" className="flex items-center gap-2 font-semibold tracking-wide"><span className="grid size-9 place-items-center rounded-md bg-violet-400/10 text-violet-200"><ShieldCheck size={19} /></span>CodeProof</Link>
          <nav className="flex flex-wrap items-center gap-1 text-sm" aria-label="Public navigation">
            <Link className="rounded px-3 py-2 text-slate-300 hover:bg-slate-800 hover:text-white" to="/">Home</Link>
            <a className="rounded px-3 py-2 text-violet-100 hover:bg-slate-800" href="#analyzer">Analyze Code</a>
            <a className="rounded px-3 py-2 text-slate-300 hover:bg-slate-800 hover:text-white" href="#how">How It Works</a>
            <a className="rounded px-3 py-2 text-slate-300 hover:bg-slate-800 hover:text-white" href="#about">About</a>
            <Link className="rounded px-3 py-2 text-slate-300 hover:bg-slate-800 hover:text-white" to="/login">Login</Link>
          </nav>
        </div>
      </header>

      <main className="mx-auto max-w-[1440px] px-4 pb-16 sm:px-6">
        <section className="py-10 sm:py-14">
          <p className="inline-flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.16em] text-violet-200"><Sparkles size={14} />Public sample analyzer · No account required</p>
          <h1 className="mt-4 max-w-4xl text-3xl font-semibold leading-tight tracking-tight sm:text-5xl">Was This Code Written by a Human or AI?</h1>
          <p className="mt-4 max-w-3xl text-base leading-7 text-slate-300">Analyze programming patterns, compare implementations, and review evidence that may help explain how a code sample was produced.</p>
          <p className="mt-4 inline-flex items-center gap-2 rounded-md border border-amber-300/20 bg-amber-300/5 px-3 py-2 text-sm text-amber-100"><ShieldCheck size={16} />Code analysis provides evidence, not guaranteed proof of authorship.</p>
        </section>

        <section id="analyzer" className="scroll-mt-4 overflow-hidden rounded-lg border border-slate-700 bg-[#111a2b] shadow-2xl shadow-black/20">
          <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-700 px-4 py-4 sm:px-5">
            <div><h2 className="font-semibold">AI Code Authorship Analyzer</h2>
              <p className="mt-1 max-w-3xl text-sm text-slate-300">Paste your code, analyze its characteristics, compare it with other code samples, and review evidence about its possible origin.</p>
              <p className="mt-1 text-xs text-slate-400">Code is sent to the API, analyzed in memory, and not saved as a submission. The per-process abuse limiter uses the request IP in memory.</p></div>
            <div className="inline-flex rounded-md border border-slate-700 p-1" role="group" aria-label="Analysis mode">
              <button className={`min-h-9 rounded px-3 text-sm ${mode === "analyze" ? "bg-violet-500/20 text-violet-100" : "text-slate-300 hover:bg-slate-800"}`}
                aria-pressed={mode === "analyze"} onClick={() => { setMode("analyze"); setInputError(null); setRequestError(null); }}>Analyze code</button>
              <button className={`min-h-9 rounded px-3 text-sm ${mode === "compare" ? "bg-violet-500/20 text-violet-100" : "text-slate-300 hover:bg-slate-800"}`}
                aria-pressed={mode === "compare"} onClick={() => { setMode("compare"); if (language === "auto") setLanguage("python"); setAnalysis(null); setComparison(null); setInputError(null); setRequestError(null); }}>Compare samples</button>
            </div>
          </div>

          {mode === "analyze" ? <form onSubmit={analyze} className="space-y-4 p-4 sm:p-5">
            <PublicCodeEditor title="Code Under Investigation" code={code} language={language} maxBytes={maxBytes}
              onCodeChange={onPrimaryCode} onLanguageChange={(value) => { setLanguage(value); setAnalysis(null); }} onError={setInputErrorForEditor} allowAutoDetect />
            <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
              <label className="inline-flex items-start gap-2 text-sm text-slate-300">
                <input className="mt-1 size-4 accent-violet-400" type="checkbox" checked={compareSamples} onChange={(event) => setCompareSamples(event.target.checked)} />
                Compare with public reference samples
              </label>
              <button className="inline-flex min-h-11 items-center justify-center gap-2 rounded-md bg-violet-600 px-5 text-sm font-semibold text-white hover:bg-violet-500 disabled:cursor-not-allowed disabled:opacity-50"
                type="submit" disabled={busy}>
                {busy ? <><LoaderCircle size={16} className="animate-spin" />Analyzing…</> : <>Analyze Code<ArrowRight size={16} /></>}
              </button>
            </div>
          </form> : <form onSubmit={compare} className="space-y-4 p-4 sm:p-5">
            <div className="grid min-w-0 gap-4 xl:grid-cols-2">
              <PublicCodeEditor title="Code Under Investigation" code={code} language={language} maxBytes={maxBytes}
                onCodeChange={onPrimaryCode} onLanguageChange={(value) => { setLanguage(value); setComparison(null); }} onError={setInputErrorForEditor} />
              <PublicCodeEditor title="Reference Code" code={referenceCode} language={referenceLanguage} maxBytes={maxBytes}
                onCodeChange={onReferenceCode} onLanguageChange={(value) => { setReferenceLanguage(value); setComparison(null); }} onError={setInputErrorForEditor} />
            </div>
            <div className="flex flex-wrap items-center justify-between gap-3">
              <p className="max-w-2xl text-xs leading-5 text-slate-400">Both samples have unknown provenance unless you have independently verified their origin. Similarity does not establish shared authorship.</p>
              <button className="inline-flex min-h-11 items-center justify-center gap-2 rounded-md bg-violet-600 px-5 text-sm font-semibold text-white hover:bg-violet-500 disabled:cursor-not-allowed disabled:opacity-50"
                type="submit" disabled={busy}>
                {busy ? <><LoaderCircle size={16} className="animate-spin" />Comparing…</> : <>Compare Samples<ArrowRight size={16} /></>}
              </button>
            </div>
          </form>}
        </section>

        <div className="mt-4 space-y-3">
          <ErrorBox message={serviceError ? `Backend connection: ${serviceError}` : null} />
          <ErrorBox message={inputError} />
          <ErrorBox message={requestError} onRetry={() => void retryRequest()} />
        </div>

        <section className="mt-8" aria-label="Analysis results">
          {busy ? <div className="flex min-h-40 items-center justify-center gap-3 text-sm text-slate-300" role="status"><LoaderCircle size={18} className="animate-spin text-violet-200" />Waiting for the analysis API…</div> :
            analysis || comparison ? <PublicAnalysisResults result={analysis} samples={samples} compareResult={comparison} /> :
              <div className="rounded-lg border border-dashed border-slate-700 bg-[#10182a] px-5 py-10 text-center text-sm text-slate-400">Your real API results will appear here after analysis. No sample or fallback report is shown.</div>}
        </section>

        <section id="how" className="mt-14 scroll-mt-6 border-t border-slate-800 pt-8">
          <p className="text-xs font-semibold uppercase tracking-wider text-violet-200">Method</p>
          <h2 className="mt-2 text-xl font-semibold">How It Works</h2>
          <div className="mt-5 grid gap-5 md:grid-cols-3">
            {[["1", "Parse source", "Python uses AST/tokenize; Java, C/C++, JavaScript, TypeScript, and TSX use Tree-sitter. Source is never executed."],
              ["2", "Inspect structure", "Supported metrics describe syntax and program structure; they do not determine authorship."],
              ["3", "Compare transparently", "Same-language token and n-gram similarity shows resemblance, not authorship or AI likelihood."]].map(([number, title, text]) => (
              <article className="border-l border-slate-700 pl-4" key={number}><span className="text-xs text-violet-200">{number}</span><h3 className="mt-1 text-sm font-semibold">{title}</h3><p className="mt-2 text-sm leading-6 text-slate-400">{text}</p></article>))}
          </div>
        </section>
        <section id="about" className="mt-10 scroll-mt-6 rounded-lg border border-slate-800 bg-[#10182a] p-5">
          <h2 className="text-sm font-semibold">About this analyzer</h2>
          <p className="mt-2 text-sm leading-6 text-slate-300">There is no validated authorship classifier configured. AI-likelihood remains unavailable, and authorship is inconclusive. Reference samples are original CodeProof examples with unknown, unverified authoring process; they demonstrate code resemblance only.</p>
          <div className="mt-4 flex flex-wrap items-center gap-2 text-xs text-slate-400">
            <span className="inline-flex items-center gap-1"><Check size={13} className="text-violet-200" />No account required</span>
            <span>·</span><span>Not stored</span><span>·</span><span>Not executed</span>
            {samples.length > 0 && <><span>·</span><span>{samples.length} documented demo references</span></>}
          </div>
        </section>
      </main>
      <footer className="border-t border-slate-800 px-4 py-4 text-center text-xs text-slate-500">© 2026 Magantipraneeth · Owner of CodeProof</footer>
    </div>
  );
}
