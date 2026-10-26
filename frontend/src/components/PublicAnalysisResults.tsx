import { useMemo, useState } from "react";
import { Check, Copy, Download, Info, ShieldAlert } from "lucide-react";
import type { PublicAnalysisResult, PublicCompareResult, PublicSample } from "../types";
import { formatDate, metricLabel } from "../utils/format";
import { Badge, Card, Empty } from "./ui";

const LANGUAGE_LABELS: Record<string, string> = {
  python: "Python", java: "Java", c: "C", cpp: "C++", javascript: "JavaScript",
  typescript: "TypeScript", tsx: "TypeScript JSX",
};

function downloadJson(report: unknown, name: string) {
  const blob = new Blob([JSON.stringify(report, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = name;
  link.click();
  window.setTimeout(() => URL.revokeObjectURL(url), 1_000);
}

function SimilarityTable({ results, samples }: { results: PublicAnalysisResult["similarity_results"]; samples: PublicSample[] }) {
  const [descending, setDescending] = useState(true);
  const sorted = useMemo(() => [...results].sort((a, b) => {
    const left = a.similarity_percent ?? -1;
    const right = b.similarity_percent ?? -1;
    return descending ? right - left : left - right;
  }), [results, descending]);
  if (!results.length) return <Empty>No eligible reference samples were compared for this language.</Empty>;
  return (
    <div className="overflow-x-auto rounded-md border border-slate-700">
      <table className="w-full min-w-[700px] text-left text-sm">
        <thead className="bg-[#121b2c] text-xs uppercase tracking-wide text-slate-400"><tr>
          <th className="px-3 py-3">Reference sample</th><th className="px-3 py-3">Language</th>
          <th className="px-3 py-3"><button className="inline-flex items-center gap-1 hover:text-white" onClick={() => setDescending(!descending)}>
            Similarity {descending ? "↓" : "↑"}</button></th><th className="px-3 py-3">Provenance</th><th className="px-3 py-3">Details</th>
        </tr></thead>
        <tbody>{sorted.map((item) => {
          const sample = samples.find((row) => row.sample_id === item.reference_sample?.sample_id);
          return <tr className="border-t border-slate-700 align-top" key={item.reference_sample?.sample_id ?? item.method}>
            <td className="px-3 py-3 font-medium">{item.reference_sample?.name ?? "Reference sample"}<span className="mt-1 block text-xs text-slate-400">{item.reference_sample?.category}</span></td>
            <td className="px-3 py-3">{item.reference_sample?.language ?? "Python"}</td>
            <td className="px-3 py-3 font-semibold tabular-nums">{item.similarity_percent === null ? "Not available" : `${item.similarity_percent}%`}</td>
            <td className="px-3 py-3"><Badge tone="amber">{item.reference_sample?.provenance_status ?? "unknown"}</Badge></td>
            <td className="max-w-sm px-3 py-3 text-xs leading-5 text-slate-300">
              {item.reference_sample && <p className="mb-2 text-slate-400">Source: {item.reference_sample.source} · License: {item.reference_sample.license}<br />Authorship label: {item.reference_sample.authorship_label} · Verified: {item.reference_sample.label_verified ? "yes" : "no"}{item.reference_sample.collection_date ? ` · Collected ${item.reference_sample.collection_date}` : ""}</p>}
              <p>{item.explanation}</p>
              {item.matching_regions.length > 0 && <details className="mt-2">
                <summary className="cursor-pointer text-violet-200">{item.matching_regions.length} matching region(s)</summary>
                <ul className="mt-2 space-y-1">{item.matching_regions.map((region, index) => <li key={index}>
                  Input lines {region.code_a_lines.join("–")} ↔ reference lines {region.code_b_lines.join("–")} ({region.matching_tokens} normalized tokens)
                  <pre className="mt-2 overflow-auto rounded bg-[#0b1020] p-2 text-[11px] leading-5"><code>{region.code_a_excerpt}</code></pre>
                  <pre className="mt-2 overflow-auto rounded bg-[#0b1020] p-2 text-[11px] leading-5"><code>{region.code_b_excerpt}</code></pre>
                </li>)}</ul>
                {sample && <pre className="mt-2 max-h-48 overflow-auto rounded bg-[#0b1020] p-3 text-[11px] leading-5"><code>{sample.code}</code></pre>}
              </details>}
              {item.matching_regions.length === 0 && sample && <details className="mt-2"><summary className="cursor-pointer text-violet-200">View reference sample</summary>
                <pre className="mt-2 max-h-48 overflow-auto rounded bg-[#0b1020] p-3 text-[11px] leading-5"><code>{sample.code}</code></pre></details>}
            </td>
          </tr>;
        })}</tbody>
      </table>
    </div>
  );
}

function CompareResult({ result }: { result: PublicCompareResult }) {
  if (result.comparison_status !== "completed") return <p className="text-sm text-amber-200">{result.explanation}</p>;
  return <div className="space-y-3">
    <div className="flex flex-wrap items-center gap-2"><span className="text-3xl font-semibold tabular-nums text-violet-100">{result.similarity_percent}%</span><span className="text-sm text-slate-300">Code similarity</span></div>
    <p className="text-xs leading-5 text-slate-400">{result.method}. Similarity is not an authorship or AI-likelihood estimate.</p>
    {result.ngram_similarity_percent !== null && result.ngram_similarity_percent !== undefined &&
      <p className="text-sm text-slate-300">Token 3-gram overlap: <strong>{result.ngram_similarity_percent}%</strong></p>}
    {result.structural_similarity_percent !== null && result.structural_similarity_percent !== undefined &&
      <p className="text-sm text-slate-300">Structural metric similarity: <strong>{result.structural_similarity_percent}%</strong></p>}
    {result.shared_tokens && result.shared_tokens.length > 0 && <p className="text-sm text-slate-300">Shared tokens (including identifiers/literals): {result.shared_tokens.join(", ")}</p>}
    {result.matching_regions?.length ? <details><summary className="cursor-pointer text-sm text-violet-200">Inspect matching regions</summary>
      <ul className="mt-2 space-y-3 text-xs text-slate-300">{result.matching_regions.map((region, index) => <li key={index}>
        <p>Sample A lines {region.code_a_lines.join("–")} ↔ sample B lines {region.code_b_lines.join("–")}</p>
        <pre className="mt-1 overflow-auto rounded bg-[#0b1020] p-2 leading-5"><code>{region.code_a_excerpt}</code></pre>
        <pre className="mt-1 overflow-auto rounded bg-[#0b1020] p-2 leading-5"><code>{region.code_b_excerpt}</code></pre>
      </li>)}</ul>
    </details> : <p className="text-xs text-slate-400">No long matching token regions were identified.</p>}
    <p className="border-t border-slate-700 pt-3 text-xs leading-5 text-slate-400">{result.explanation}</p>
  </div>;
}

export default function PublicAnalysisResults({ result, samples, compareResult }: {
  result: PublicAnalysisResult | null; samples: PublicSample[]; compareResult: PublicCompareResult | null;
}) {
  const [feedback, setFeedback] = useState("");
  const [copied, setCopied] = useState(false);
  const model = result?.authorship_assessment;
  const estimate = model?.ai_likelihood_percent;
  const hasEstimate = model?.model_status === "available" && model.probability_calibrated === true &&
    typeof estimate === "number" && Number.isFinite(estimate) && estimate >= 0 && estimate <= 100;
  const maxSimilarity = result?.similarity_results.reduce((max, row) => Math.max(max, row.similarity_percent ?? 0), 0) ?? 0;
  const languageId = result?.language_detection.detected_language ?? result?.language;
  const languageName = languageId ? LANGUAGE_LABELS[languageId] ?? languageId : "Unknown or unsupported language";
  const report = result;

  async function copyReport() {
    if (!report) return;
    try {
      await navigator.clipboard.writeText(JSON.stringify(report, null, 2));
      setCopied(true);
      setFeedback("Analysis response copied.");
      window.setTimeout(() => setCopied(false), 1_500);
    } catch {
      setFeedback("Clipboard access was denied. Use Download report instead.");
    }
  }

  return (
    <section className="space-y-5" aria-live="polite" aria-label="Analysis report">
      {result && <>
        <header className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-700 pb-4">
          <div><p className="text-xs font-semibold uppercase tracking-wider text-violet-200">Analysis report</p>
            <h2 className="mt-1 text-xl font-semibold">{result.analysis_status === "completed" ? "Analysis complete" : result.analysis_status === "unknown_language" ? "Language unclear" : result.analysis_status === "unsupported_language" ? "Analysis unavailable for this language" : result.analysis_status}</h2>
            <p className="mt-1 text-xs text-slate-400">ID {result.analysis_id.slice(0, 12)} · {languageName} · {formatDate(result.created_at)}</p></div>
          <div className="flex gap-2">
            <button className="inline-flex min-h-10 items-center gap-2 rounded-md border border-slate-600 px-3 text-sm hover:bg-slate-800" onClick={copyReport}><Copy size={15} />{copied ? "Copied" : "Copy report"}</button>
            <button className="inline-flex min-h-10 items-center gap-2 rounded-md bg-violet-600 px-3 text-sm font-semibold text-white hover:bg-violet-500" onClick={() => downloadJson(report, `codeproof-analysis-${result.analysis_id}.json`)}><Download size={15} />Download report</button>
          </div>
        </header>
        {feedback && <p role="status" className="text-xs text-slate-300">{feedback}</p>}
        {result.message && <p className="rounded-md border border-amber-300/20 bg-amber-300/5 p-3 text-sm text-amber-100">{result.message}</p>}
        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
          <Card className="border-violet-300/20 bg-violet-300/[0.04]">
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">Code authorship assessment</p>
            <p className="mt-3 text-2xl font-semibold">{model?.result ?? "Inconclusive"}</p>
            <p className="mt-2 text-sm leading-6 text-slate-300">{model?.explanation ?? "No assessment was returned."}</p>
            <Badge tone="amber">Model {model?.model_status ?? "unavailable"}</Badge>
          </Card>
          <Card>
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">Programming language</p>
            <p className="mt-3 text-xl font-semibold">{languageName}</p>
            <p className="mt-2 text-xs leading-5 text-slate-400">{result.language_detection.confidence === "unique_parser_match" ?
              "Unique clean parser match; not a statistical confidence score." : `Detection status: ${result.language_detection.selection_status}.`}</p>
            {result.language_detection.selection_status === "mismatch" && <p className="mt-2 text-xs text-amber-200">The selected language differs from the parser detection. Results use your selected parser.</p>}
            {result.language_detection.candidates.length > 1 && <p className="mt-2 text-xs text-amber-200">Ambiguous candidates: {result.language_detection.candidates.join(", ")}</p>}
          </Card>
          <Card>
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">Syntax validity</p>
            <p className="mt-3 text-xl font-semibold">{result.syntax.status === "valid" ? "Valid" : result.syntax.status === "invalid" ? "Invalid" : "Unable to validate"}</p>
            <p className="mt-2 text-xs text-slate-400">Validation: {result.syntax.validation}</p>
            {result.syntax.errors.length > 0 && <ul className="mt-2 space-y-1 text-xs text-red-200">{result.syntax.errors.map((error, index) => <li key={index}>
              {error.line ? `Line ${error.line}${error.column ? `, column ${error.column}` : ""}: ` : ""}{error.message}
            </li>)}</ul>}
          </Card>
          <Card>
            <div className="flex items-center justify-between gap-2"><p className="text-xs font-semibold uppercase tracking-wide text-slate-400">AI-likelihood estimate</p>
              <details className="relative"><summary className="grid size-8 cursor-pointer place-items-center rounded-full hover:bg-slate-700" aria-label="About AI-likelihood estimates"><Info size={15} /></summary>
                <p className="absolute right-0 z-10 mt-2 w-64 rounded-md border border-slate-600 bg-[#111a2b] p-3 text-xs leading-5 text-slate-200 shadow-xl">A percentage is shown only when a validated and calibrated model provides one. It is not proof of authorship.</p>
              </details></div>
            <p className="mt-3 text-2xl font-semibold tabular-nums">{hasEstimate ? `${estimate}%` : "Unavailable"}</p>
            {!hasEstimate && <p className="mt-2 text-xs leading-5 text-slate-400">The current analysis examines code characteristics but cannot reliably estimate whether this code was generated by AI.</p>}
            {hasEstimate && <p className="mt-2 text-xs text-slate-400">Model version: {model?.model_version ?? "Not reported"}</p>}
          </Card>
          <Card>
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">Code similarity</p>
            <p className="mt-3 text-2xl font-semibold tabular-nums">{result.similarity.score !== null ? `${result.similarity.score}%` : result.samples_compared ? `${maxSimilarity}%` : "Not available"}</p>
            <p className="mt-2 text-xs leading-5 text-slate-400">Highest result across {result.samples_compared} reference sample(s). This is code resemblance, not AI probability.</p>
            {result.similarity.method && <p className="mt-1 text-xs text-slate-400">{result.similarity.method}</p>}
            {result.similarity.ngram_similarity_percent !== null && result.similarity.ngram_similarity_percent !== undefined &&
              <p className="mt-1 text-xs text-slate-400">N-gram similarity: {result.similarity.ngram_similarity_percent}%</p>}
          </Card>
        </div>
        <Card title="Code structure">
          {result.metrics ? <dl className="grid grid-cols-2 gap-4 sm:grid-cols-3 xl:grid-cols-5">{Object.entries(result.metrics).filter(([key]) => key !== "syntax_errors").map(([key, value]) => (
            <div className="border-l-2 border-violet-300/40 pl-3" key={key}><dt className="text-xs text-slate-400">{metricLabel(key)}</dt><dd className="mt-1 text-xl font-semibold tabular-nums">{String(value)}</dd></div>))}</dl> :
            <p className="text-sm text-slate-400">Not available for {result.language ?? "this language"}.</p>}
          <p className="mt-4 border-t border-slate-700 pt-3 text-xs text-slate-400">{result.structure.summary}</p>
        </Card>
        <Card title="Code Similarity Analysis">
          <p className="mb-4 text-sm leading-6 text-slate-400">Token-based comparison with original CodeProof demonstration samples. Each sample’s authorship is unknown and unverified. Similarity does not establish copying or how a program was produced.</p>
          <SimilarityTable results={result.similarity_results} samples={samples} />
        </Card>
        <Card title="Why Did We Get This Result?">
          <p className="text-sm leading-6 text-slate-200">{result.explanation}</p>
          {result.structural_findings.length > 0 && <ul className="mt-3 space-y-2 text-sm text-slate-300">{result.structural_findings.map((item, index) => <li className="border-l-2 border-slate-600 pl-3" key={index}>{item}</li>)}</ul>}
          <div className="mt-4 grid gap-3 border-t border-slate-700 pt-4 sm:grid-cols-2">
            <div><p className="text-xs font-semibold uppercase tracking-wide text-slate-400">Provenance</p><p className="mt-1 text-sm">{result.provenance.status} · {result.provenance.explanation}</p></div>
            <div><p className="text-xs font-semibold uppercase tracking-wide text-slate-400">Evidence scope</p><p className="mt-1 text-sm">No authorship records were supplied. Missing provenance is not evidence of human or AI authorship.</p></div>
          </div>
        </Card>
        <Card title="Limitations">
          <ul className="space-y-2 text-sm leading-6 text-slate-300">{result.limitations.map((item, index) => <li className="flex gap-2" key={index}><ShieldAlert size={15} className="mt-1 shrink-0 text-amber-200" />{item}</li>)}</ul>
        </Card>
      </>}
      {compareResult && <Card title="Two-sample comparison"><CompareResult result={compareResult} /></Card>}
    </section>
  );
}
