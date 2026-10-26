// Framework-free HTTP client (testable with node --test). No parameter properties / enums,
// so Node's built-in type stripping can run it directly.
export class ApiError extends Error {
  status: number;
  code: string;
  details: unknown;
  constructor(status: number, code: string, message: string, details?: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.details = details;
  }
}

export interface ClientOptions {
  baseUrl: string;
  getToken: () => string | null;
  fetchImpl?: typeof fetch;
  onUnauthorized?: () => void;
}

export function createClient(opts: ClientOptions) {
  const doFetch: typeof fetch = opts.fetchImpl ?? ((...args) => fetch(...args));

  async function raw(method: string, path: string, body?: unknown): Promise<Response> {
    const headers: Record<string, string> = {};
    const token = opts.getToken();
    if (token) headers["Authorization"] = `Bearer ${token}`;
    let payload: BodyInit | undefined;
    if (body instanceof FormData) payload = body;
    else if (body !== undefined) {
      headers["Content-Type"] = "application/json";
      payload = JSON.stringify(body);
    }
    let res: Response;
    try {
      res = await doFetch(`${opts.baseUrl}${path}`, { method, headers, body: payload });
    } catch {
      throw new ApiError(0, "network_error", "Cannot reach the server. Is the API running?");
    }
    if (!res.ok) {
      let code = `http_${res.status}`, message = `Request failed (${res.status}).`, details: unknown;
      try {
        const j = await res.json();
        code = j.error ?? code; message = j.message ?? message; details = j.details;
      } catch { /* non-JSON error body */ }
      if (res.status === 401) opts.onUnauthorized?.();
      throw new ApiError(res.status, code, message, details);
    }
    return res;
  }

  async function request<T>(method: string, path: string, body?: unknown): Promise<T> {
    const res = await raw(method, path, body);
    return (res.status === 204 ? undefined : await res.json()) as T;
  }

  return {
    get: <T>(path: string) => request<T>("GET", path),
    post: <T>(path: string, body?: unknown) => request<T>("POST", path, body ?? {}),
    patch: <T>(path: string, body: unknown) => request<T>("PATCH", path, body),
    del: (path: string) => request<void>("DELETE", path),
    blob: async (path: string) => (await raw("GET", path)).blob(),
  };
}
