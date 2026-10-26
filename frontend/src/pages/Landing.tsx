import { Link } from "react-router-dom";
import { ArrowRight, Check, ShieldCheck, Sparkles } from "lucide-react";
import { useAuth } from "../auth/AuthContext";
import { btn, btnGhost } from "../components/ui";

export default function Landing() {
  const { user } = useAuth();

  return (
    <div className="mx-auto flex min-h-screen max-w-7xl flex-col px-5 sm:px-8">
      <header className="flex items-center justify-between border-b border-white/10 py-5">
        <Link to={user ? "/dashboard" : "/"} className="flex items-center gap-3 font-semibold tracking-wide">
          <span className="grid size-9 place-items-center rounded-md bg-emerald-300/10 text-emerald-200"><ShieldCheck size={20} /></span>CodeProof
        </Link>
        <nav className="flex flex-wrap items-center gap-2" aria-label="Account">
          <Link className={btnGhost} to="/analyze"><Sparkles size={15} />Try Free Analyzer</Link>
          {user ? <Link className={btn} to="/dashboard">Open workspace <ArrowRight size={16} /></Link> : <>
            <Link className={btnGhost} to="/login">Log in</Link><Link className={btn} to="/register">Create account</Link></>}
        </nav>
      </header>
      <main className="flex flex-1 flex-col justify-center py-14 sm:py-20">
        <section className="max-w-3xl">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-emerald-200">Evidence-led code review</p>
          <h1 className="mt-5 text-4xl font-semibold leading-tight tracking-tight sm:text-6xl">CodeProof</h1>
          <p className="mt-5 max-w-2xl text-lg leading-8 text-slate-300">Review programming submissions with transparent static analysis and clear evidence reports. Every result is context for a human decision, never a verdict.</p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Link className={btn} to="/analyze"><Sparkles size={16} />Try Free Analyzer<ArrowRight size={16} /></Link>
            <Link className={btn} to={user ? "/dashboard" : "/register"}>{user ? "Open workspace" : "Create account"}<ArrowRight size={16} /></Link>
            {!user && <Link className={btnGhost} to="/login">Log in</Link>}
          </div>
        </section>
        <section className="mt-16 grid gap-8 border-t border-white/10 pt-7 sm:grid-cols-2 lg:grid-cols-3" aria-label="Product capabilities">
          {[["Assignments and submissions", "Role-scoped coursework and source uploads"],
            ["Python static analysis", "Syntax, structure, and descriptive code metrics"],
            ["Evidence reports", "Downloadable PDFs with limitations and review notes"]].map(([title, detail]) => (
              <div key={title} className="flex gap-3"><Check size={17} className="mt-0.5 shrink-0 text-emerald-200" aria-hidden="true" />
                <div><h2 className="text-sm font-semibold">{title}</h2><p className="mt-1 text-sm text-slate-400">{detail}</p></div></div>))}
        </section>
      </main>
      <footer className="border-t border-white/10 py-4 text-right text-xs text-slate-400">
        <p>© 2026 Magantipraneeth · Owner of CodeProof</p>
      </footer>
    </div>
  );
}
