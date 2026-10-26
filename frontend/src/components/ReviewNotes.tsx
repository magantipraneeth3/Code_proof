import { FormEvent, useState } from "react";
import { useAsync } from "../hooks/useAsync";
import { api, ApiError } from "../services/api";
import { btn, btnDanger, btnGhost, Card, Empty, ErrorBox, input, Loading } from "./ui";

export default function ReviewNotes({ submissionId }: { submissionId: number }) {
  const notes = useAsync(() => api.reviewNotes(submissionId), [submissionId]);
  const [draft, setDraft] = useState("");
  const [editingId, setEditingId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function add(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await api.createReviewNote(submissionId, draft);
      setDraft("");
      notes.reload();
    } catch (cause) {
      setError(cause instanceof ApiError ? cause.message : "Could not save the note.");
    } finally {
      setBusy(false);
    }
  }

  async function save(noteId: number) {
    setBusy(true);
    setError(null);
    try {
      await api.updateReviewNote(submissionId, noteId, draft);
      setEditingId(null);
      setDraft("");
      notes.reload();
    } catch (cause) {
      setError(cause instanceof ApiError ? cause.message : "Could not update the note.");
    } finally {
      setBusy(false);
    }
  }

  async function remove(noteId: number) {
    setBusy(true);
    setError(null);
    try {
      await api.deleteReviewNote(submissionId, noteId);
      notes.reload();
    } catch (cause) {
      setError(cause instanceof ApiError ? cause.message : "Could not delete the note.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <Card title="Professor review notes">
      <ErrorBox message={error ?? notes.error} />
      {notes.loading ? <Loading label="Loading review notes…" /> : notes.data?.items.length === 0 ?
        <Empty>No review notes yet.</Empty> : (
          <div className="divide-y divide-white/10">
            {notes.data?.items.map((note) => (
              <article className="py-3 first:pt-0 last:pb-0" key={note.id}>
                <p className="text-xs text-slate-400">{note.author_email} · {new Date(note.updated_at).toLocaleString()}</p>
                {editingId === note.id ? (
                  <div className="mt-2 space-y-2">
                    <textarea className={input} rows={3} value={draft} onChange={(event) => setDraft(event.target.value)} />
                    <div className="flex gap-2">
                      <button className={btn} disabled={busy || !draft.trim()} onClick={() => save(note.id)}>Save</button>
                      <button className={btnGhost} disabled={busy} onClick={() => { setEditingId(null); setDraft(""); }}>Cancel</button>
                    </div>
                  </div>
                ) : (
                  <>
                    <p className="mt-1 whitespace-pre-wrap text-sm">{note.body}</p>
                    <div className="mt-2 flex gap-2">
                      <button className={btnGhost} disabled={busy} onClick={() => { setEditingId(note.id); setDraft(note.body); }}>Edit</button>
                      <button className={btnDanger} disabled={busy} onClick={() => {
                        if (window.confirm("Delete this review note?")) void remove(note.id);
                      }}>Delete</button>
                    </div>
                  </>
                )}
              </article>
            ))}
          </div>
        )}
      <form onSubmit={add} className="mt-4 space-y-2">
        <label className="block text-sm" htmlFor="review-note">Add a note</label>
        <textarea id="review-note" className={input} rows={3} maxLength={10_000} value={draft}
          onChange={(event) => setDraft(event.target.value)} placeholder="Private to the assignment's professor" />
        <button className={btn} disabled={busy || !draft.trim() || editingId !== null}>
          {busy && editingId === null ? "Saving…" : "Add note"}
        </button>
      </form>
    </Card>
  );
}