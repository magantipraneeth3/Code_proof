import { useState } from "react";
import { Link, NavLink, Outlet, useNavigate } from "react-router-dom";
import { BarChart3, ClipboardCheck, ClipboardList, Code2, FileText, GitCompareArrows, LogOut, Menu, ShieldCheck, X } from "lucide-react";
import { useAuth } from "../auth/AuthContext";
import { Badge } from "../components/ui";

const NAV = [
  { to: "/dashboard", label: "Dashboard", icon: BarChart3 },
  { to: "/assignments", label: "Assignments", icon: ClipboardList },
  { to: "/submissions", label: "Submissions", icon: FileText },
  { to: "/reviews", label: "Review queue", icon: ClipboardCheck, professorOnly: true },
  { to: "/compare", label: "Compare code", icon: GitCompareArrows },
  { to: "/workspace", label: "Analyze code", icon: Code2 },
];

export default function AppLayout() {
  const { user, logout } = useAuth();
  const [open, setOpen] = useState(false);
  const nav = useNavigate();
  const links = NAV.filter((item) => !item.professorOnly || user?.role === "professor");
  const link = ({ isActive }: { isActive: boolean }) =>
    `flex min-h-10 items-center gap-3 border-l-2 px-3 py-2 text-sm transition ${isActive ? "border-emerald-300 bg-emerald-300/10 text-white" : "border-transparent text-slate-300 hover:bg-white/5 hover:text-white"}`;

  const sidebar = (
    <>
      <Link to="/dashboard" className="flex items-center gap-3 px-5 py-5 font-semibold tracking-wide">
        <span className="grid size-9 place-items-center rounded-md bg-emerald-300/10 text-emerald-200"><ShieldCheck size={20} /></span>
        <span>CodeProof</span>
      </Link>
      <nav className="flex flex-col gap-1 px-3 pt-3" aria-label="Main">
        <p className="mb-2 px-3 text-[11px] font-semibold uppercase tracking-[0.12em] text-slate-500">Workspace</p>
        {links.map(({ to, label, icon: Icon }) => (
          <NavLink key={to} to={to} className={link} onClick={() => setOpen(false)}><Icon size={17} aria-hidden="true" /> {label}</NavLink>
        ))}
      </nav>
      <div className="mt-auto border-t border-white/10 px-5 py-4">
        <p className="truncate text-sm font-medium text-slate-100">{user?.email}</p>
        <div className="mt-2 flex items-center justify-between gap-2">
          <Badge>{user?.role}</Badge>
          <button className="inline-flex items-center gap-2 rounded px-2 py-1 text-xs text-slate-300 hover:bg-white/5 hover:text-white"
            onClick={async () => { await logout(); nav("/"); }}><LogOut size={14} aria-hidden="true" />Log out</button>
        </div>
      </div>
    </>
  );

  return (
    <div className="min-h-screen md:flex">
      <aside className="hidden w-64 shrink-0 flex-col border-r border-white/10 bg-[#141e18] md:flex">{sidebar}</aside>
      <header className="sticky top-0 z-20 flex items-center justify-between border-b border-white/10 bg-[#141e18] px-4 py-3 md:hidden">
        <Link to="/dashboard" className="flex items-center gap-2 font-semibold"><ShieldCheck size={20} className="text-emerald-200" />CodeProof</Link>
        <button className="grid size-10 place-items-center rounded-md hover:bg-white/5" aria-label={open ? "Close menu" : "Open menu"}
          aria-expanded={open} onClick={() => setOpen(!open)}>{open ? <X size={20} /> : <Menu size={20} />}</button>
      </header>
      {open && <div className="fixed inset-x-0 bottom-0 top-[57px] z-10 flex flex-col border-b border-white/10 bg-[#141e18] md:hidden">{sidebar}</div>}
      <main className="min-w-0 flex-1 px-4 py-6 md:px-8 md:py-9"><div className="mx-auto max-w-7xl"><Outlet /></div></main>
    </div>
  );
}
