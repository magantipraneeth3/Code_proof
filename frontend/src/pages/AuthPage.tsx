import { FormEvent, useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { ArrowRight, ShieldCheck } from "lucide-react";
import { useAuth } from "../auth/AuthContext";
import { ApiError } from "../services/api";
import { btn, Card, ErrorBox, input } from "../components/ui";

export default function AuthPage({ mode }: { mode: "login" | "register" }) {
  const { user, login, register } = useAuth();
  const nav = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState<"student" | "professor">("student");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  if (user) return <Navigate to="/dashboard" replace />;

  async function submit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    if (mode === "register" && password.length < 10) { setError("Password must be at least 10 characters."); return; }
    setBusy(true);
    try {
      if (mode === "login") await login(email, password); else await register(email, password, role);
      nav("/dashboard");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong.");
    } finally { setBusy(false); }
  }

  return (
    <div className="mx-auto flex min-h-screen max-w-6xl flex-col px-5 sm:px-8">
      <header className="border-b border-white/10 py-5">
        <Link to="/" className="inline-flex items-center gap-3 font-semibold tracking-wide"><span className="grid size-9 place-items-center rounded-md bg-emerald-300/10 text-emerald-200"><ShieldCheck size={20} /></span>CodeProof</Link>
      </header>
      <main className="grid flex-1 items-center gap-10 py-10 lg:grid-cols-[1fr_420px] lg:gap-20">
        <section className="max-w-xl">
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-emerald-200">Evidence-led code review</p>
          <h1 className="mt-4 text-3xl font-semibold leading-tight tracking-tight sm:text-4xl">{mode === "login" ? "Welcome back" : "Create your workspace account"}</h1>
          <p className="mt-4 max-w-lg text-base leading-7 text-slate-300">{mode === "login" ? "Continue to your assignments, submissions, and review queue." : "Set up a student or professor account to work with real assignments and code submissions."}</p>
          <p className="mt-6 border-l-2 border-emerald-300/50 pl-4 text-sm leading-6 text-slate-400">CodeProof provides descriptive analysis for human review. It does not determine authorship or misconduct.</p>
        </section>
        <Card title={mode === "login" ? "Sign in" : "Register"} className="w-full">
          <form onSubmit={submit} className="space-y-4">
            <label className="block text-sm font-medium">Email
              <input className={`${input} mt-1`} type="email" required autoComplete="email" value={email} onChange={(e) => setEmail(e.target.value)} />
            </label>
            <label className="block text-sm font-medium">Password
              <input className={`${input} mt-1`} type="password" required minLength={mode === "register" ? 10 : 1}
                     autoComplete={mode === "login" ? "current-password" : "new-password"}
                     value={password} onChange={(e) => setPassword(e.target.value)} />
              {mode === "register" && <span className="mt-1 block text-xs font-normal text-slate-400">Use at least 10 characters.</span>}
            </label>
            {mode === "register" && (
              <label className="block text-sm font-medium">Account type
                <select className={`${input} mt-1`} value={role} onChange={(e) => setRole(e.target.value as "student" | "professor")}>
                  <option value="student">Student</option><option value="professor">Professor</option>
                </select>
              </label>
            )}
            <ErrorBox message={error} />
            <button className={`${btn} w-full`} disabled={busy}>{busy ? "Please wait…" : <>{mode === "login" ? "Sign in" : "Create account"}<ArrowRight size={16} /></>}</button>
          </form>
          <p className="mt-5 border-t border-white/10 pt-4 text-sm text-slate-400">
            {mode === "login" ? <>New to CodeProof? <Link className="font-medium text-emerald-100 hover:underline" to="/register">Create an account</Link></> :
              <>Already registered? <Link className="font-medium text-emerald-100 hover:underline" to="/login">Sign in</Link></>}
          </p>
        </Card>
      </main>
    </div>
  );
}
