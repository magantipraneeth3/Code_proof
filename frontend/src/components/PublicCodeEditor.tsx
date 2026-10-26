import Editor from "@monaco-editor/react";
import { Clipboard, FileCode2, RotateCcw } from "lucide-react";
import { useRef, useState } from "react";
import { btnGhost, input } from "./ui";
import { formatBytes } from "../utils/format";

export const PUBLIC_LANGUAGES = [
  { id: "auto", name: "Auto-detect", monaco: "plaintext", extensions: [] },
  { id: "python", name: "Python", monaco: "python", extensions: [".py"] },
  { id: "java", name: "Java", monaco: "java", extensions: [".java"] },
  { id: "c", name: "C", monaco: "c", extensions: [".c", ".h"] },
  { id: "cpp", name: "C++", monaco: "cpp", extensions: [".cc", ".cpp", ".hpp"] },
  { id: "javascript", name: "JavaScript", monaco: "javascript", extensions: [".js", ".jsx", ".mjs"] },
  { id: "typescript", name: "TypeScript", monaco: "typescript", extensions: [".ts"] },
  { id: "tsx", name: "TypeScript JSX", monaco: "typescript", extensions: [".tsx"] },
] as const;

interface Props {
  title: string;
  code: string;
  language: string;
  maxBytes: number;
  onCodeChange: (value: string) => void;
  onLanguageChange: (value: string) => void;
  onError: (message: string | null) => void;
  showUtilities?: boolean;
  allowAutoDetect?: boolean;
}

export default function PublicCodeEditor({ title, code, language, maxBytes, onCodeChange,
  onLanguageChange, onError, showUtilities = true, allowAutoDetect = false }: Props) {
  const fileRef = useRef<HTMLInputElement>(null);
  const [pasteBusy, setPasteBusy] = useState(false);
  const bytes = new TextEncoder().encode(code).length;
  const lines = code.split(/\r\n|\r|\n/).length;
  const monacoLanguage = PUBLIC_LANGUAGES.find((item) => item.id === language)?.monaco ?? "plaintext";

  async function pasteFromClipboard() {
    setPasteBusy(true);
    onError(null);
    try {
      const value = await navigator.clipboard.readText();
      onCodeChange(value);
    } catch {
      onError("Clipboard access was denied. You can paste directly into the editor.");
    } finally {
      setPasteBusy(false);
    }
  }

  async function readFile(file?: File) {
    if (!file) return;
    if (file.size > maxBytes) {
      onError(`This file exceeds the ${formatBytes(maxBytes)} source limit.`);
      if (fileRef.current) fileRef.current.value = "";
      return;
    }
    try {
      const text = await file.text();
      onCodeChange(text);
      const filename = file.name.toLowerCase();
      const inferred = PUBLIC_LANGUAGES.find((item) => item.extensions.some((extension) => filename.endsWith(extension)));
      if (inferred) onLanguageChange(inferred.id);
      onError(null);
    } catch {
      onError("Could not read this file. Choose a text source file and try again.");
    }
    if (fileRef.current) fileRef.current.value = "";
  }

  return (
    <section className="overflow-hidden rounded-lg border border-slate-700 bg-[#0c1220]" aria-label={title}>
      <header className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-700 px-4 py-3">
        <div className="flex items-center gap-2 text-sm font-semibold text-slate-100"><FileCode2 size={16} className="text-violet-300" />{title}</div>
        <label className="flex items-center gap-2 text-xs text-slate-300">Language
          <select className={`${input} min-h-9 w-auto min-w-32 border-slate-600 bg-[#111a2b] py-1.5`} value={language}
            onChange={(event) => onLanguageChange(event.target.value)}>
            {PUBLIC_LANGUAGES.filter((item) => allowAutoDetect || item.id !== "auto").map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
          </select>
        </label>
      </header>
      {showUtilities && <div className="flex flex-wrap items-center gap-2 border-b border-slate-700 px-3 py-2">
        <button className="inline-flex min-h-9 items-center gap-2 rounded-md border border-slate-600 px-3 text-xs text-slate-200 hover:bg-slate-800"
          onClick={pasteFromClipboard} disabled={pasteBusy}><Clipboard size={14} />{pasteBusy ? "Pasting…" : "Paste code"}</button>
        <button className="inline-flex min-h-9 items-center gap-2 rounded-md border border-slate-600 px-3 text-xs text-slate-200 hover:bg-slate-800"
          onClick={() => fileRef.current?.click()}><FileCode2 size={14} />Upload file</button>
        <input ref={fileRef} className="sr-only" type="file" aria-label={`${title} upload file`}
          accept=".py,.java,.c,.h,.cc,.cpp,.hpp,.js,.jsx,.mjs,.ts,.tsx" onChange={(event) => readFile(event.target.files?.[0])} />
        <button className="inline-flex min-h-9 items-center gap-2 rounded-md px-3 text-xs text-slate-300 hover:bg-slate-800"
          onClick={() => { onCodeChange(""); onError(null); }} disabled={!code}><RotateCcw size={14} />Clear code</button>
      </div>}
      <Editor
        height="360px"
        language={monacoLanguage}
        theme="vs-dark"
        value={code}
        onChange={(value) => onCodeChange(value ?? "")}
        options={{
          ariaLabel: `${title} editor`,
          automaticLayout: true,
          minimap: { enabled: false },
          lineNumbers: "on",
          scrollBeyondLastLine: false,
          tabSize: 4,
          insertSpaces: true,
          wordWrap: "on",
          fontSize: 13,
          lineHeight: 21,
          padding: { top: 12, bottom: 12 },
          renderLineHighlight: "gutter",
          overviewRulerLanes: 0,
          scrollbar: { verticalScrollbarSize: 10, horizontalScrollbarSize: 10 },
        }}
      />
      <footer className="flex items-center justify-between border-t border-slate-700 px-4 py-2 text-xs tabular-nums text-slate-400">
        <span>{lines} lines</span><span className={bytes > maxBytes ? "text-red-300" : ""}>{formatBytes(bytes)} / {formatBytes(maxBytes)}</span>
      </footer>
    </section>
  );
}
