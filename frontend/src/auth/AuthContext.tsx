import { createContext, ReactNode, useCallback, useContext, useEffect, useState } from "react";
import { api, setUnauthorizedHandler, tokenStore } from "../services/api";
import type { User } from "../types";

interface AuthState {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, role: "student" | "professor") => Promise<void>;
  logout: () => Promise<void>;
}

const Ctx = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setUnauthorizedHandler(() => { tokenStore.clear(); setUser(null); });
    if (!tokenStore.get()) { setLoading(false); return; }
    api.me().then(setUser).catch(() => tokenStore.clear()).finally(() => setLoading(false));
  }, []);

  const accept = (r: { access_token: string; user: User }) => { tokenStore.set(r.access_token); setUser(r.user); };
  const login = useCallback(async (e: string, p: string) => accept(await api.login(e, p)), []);
  const register = useCallback(async (e: string, p: string, role: "student" | "professor") => accept(await api.register(e, p, role)), []);
  const logout = useCallback(async () => {
    try { await api.logout(); } catch { /* token may already be invalid */ }
    tokenStore.clear(); setUser(null);
  }, []);

  return <Ctx.Provider value={{ user, loading, login, register, logout }}>{children}</Ctx.Provider>;
}

export function useAuth(): AuthState {
  const v = useContext(Ctx);
  if (!v) throw new Error("useAuth must be used inside AuthProvider");
  return v;
}
