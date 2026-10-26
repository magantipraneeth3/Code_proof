import { useAsync } from "../hooks/useAsync";
import { api } from "../services/api";
import { Card, Empty, ErrorBox, input, Loading } from "../components/ui";
import { formatDate } from "../utils/format";
import { useState } from "react";

function CodePanel({ title, filename, source, loading, error }: {
  title: string; filename?: string; source: string | null | undefined; loading: boolean; error: string | null;
}) {
  return (
    <Card className="min-w-0 p-0">
      <header className="border-b border-white/10 px-4 py-3">
        <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">{title}</p>
        <p className="mt-1 truncate text-sm font-medium" title={filename}>{filename ?? "Select a submission"}</p>
      </header>
      {loading ? <div className="p-4"><Loading label="Loading source…" /></div> : error ? <div className="p-4"><ErrorBox message={error} />
        </div> : source === null ? <Empty>Source is unavailable for this submission.</Empty> : source === undefined ?
        <Empty>Select a submission to view its source.</Empty> : (
          <pre className="max-h-[65vh] min-h-72 overflow-auto p-4 text-xs leading-6 text-slate-200" tabIndex={0}>
            <code>{source.split("\n").map((line, index) => <span className="block min-w-max" key={index}>
              <span className="mr-4 inline-block w-8 select-none text-right text-slate-600">{index + 1}</span>{line || " "}
            </span>)}</code>
          </pre>)}
    </Card>
  );
}

export default function Compare() {
  const [page, setPage] = useState(1);
  const [leftId, setLeftId] = useState("");
  const [rightId, setRightId] = useState("");
  const items = useAsync(() => api.submissions({ page, page_size: 100 }), [page]);
  const left = useAsync(() => leftId ? api.submission(Number(leftId)) : Promise.resolve(null), [leftId]);
  const right = useAsync(() => rightId ? api.submission(Number(rightId)) : Promise.resolve(null), [rightId]);
  const options = items.data?.items ?? [];
  const pageCount = items.data ? Math.max(1, Math.ceil(items.data.total / items.data.page_size)) : 1;

  function optionLabel(item: (typeof options)[number]) {
    return `${item.original_filename} · ${item.assignment_title} · ${formatDate(item.submitted_at)}`;
  }

  return (
    <div className="space-y-6">
      <header><p className="text-xs font-semibold uppercase tracking-[0.14em] text-emerald-200">Source review</p>
        <h1 className="mt-2 text-3xl font-semibold tracking-tight">Compare code</h1>
        <p className="mt-1 max-w-2xl text-sm text-slate-400">Inspect two submissions side by side. This view does not calculate code similarity or make an authorship assessment.</p></header>
      <Card>
        <div className="grid gap-4 md:grid-cols-2">
          <label className="block text-sm">First submission
            <select className={`${input} mt-1`} value={leftId} onChange={(event) => setLeftId(event.target.value)}>
              <option value="">Choose a submission</option>{options.map((item) => <option key={item.id} value={item.id}>{optionLabel(item)}</option>)}
            </select>
          </label>
          <label className="block text-sm">Second submission
            <select className={`${input} mt-1`} value={rightId} onChange={(event) => setRightId(event.target.value)}>
              <option value="">Choose a submission</option>{options.map((item) => <option key={item.id} value={item.id}>{optionLabel(item)}</option>)}
            </select>
          </label>
        </div>
        {items.loading ? <Loading label="Loading your accessible submissions…" /> : items.error ? <div className="mt-3"><ErrorBox message={items.error} onRetry={items.reload} /></div> :
          items.data?.total === 0 ? <div className="mt-4"><Empty>There are no accessible submissions to compare yet.</Empty></div> : null}
        {items.data && items.data.total > items.data.page_size && <div className="mt-4 flex items-center justify-end gap-3 text-sm text-slate-400">
          <button className="rounded-md border border-white/15 px-3 py-2 disabled:opacity-50" disabled={page <= 1} onClick={() => setPage(page - 1)}>Previous</button>
          <span>Page {page} of {pageCount}</span>
          <button className="rounded-md border border-white/15 px-3 py-2 disabled:opacity-50" disabled={page >= pageCount} onClick={() => setPage(page + 1)}>Next</button>
        </div>}
      </Card>
      <div className="grid min-w-0 gap-4 xl:grid-cols-2">
        <CodePanel title="Submission A" filename={left.data?.original_filename} source={left.data?.source}
          loading={Boolean(leftId) && left.loading} error={left.error} />
        <CodePanel title="Submission B" filename={right.data?.original_filename} source={right.data?.source}
          loading={Boolean(rightId) && right.loading} error={right.error} />
      </div>
    </div>
  );
}