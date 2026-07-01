const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export class ApiError extends Error {
  status: number;
  body: unknown;
  constructor(status: number, message: string, body?: unknown) {
    super(message);
    this.status = status;
    this.body = body;
  }
}

function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("dira_token");
}

function handleUnauthorized() {
  if (typeof window === "undefined") return;
  localStorage.removeItem("dira_token");
  localStorage.removeItem("dira_role");
  localStorage.removeItem("dira_username");
  if (window.location.pathname !== "/login") {
    window.location.href = "/login";
  }
}

interface RequestOptions {
  method?: string;
  body?: unknown;
  skipAuthRedirect?: boolean;
}

async function request<T>(
  path: string,
  options: RequestOptions = {}
): Promise<T> {
  const { method = "GET", body, skipAuthRedirect } = options;
  const token = getToken();

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  let res: Response;
  try {
    res = await fetch(`${API_BASE_URL}${path}`, {
      method,
      headers,
      body: body !== undefined ? JSON.stringify(body) : undefined,
      cache: "no-store",
    });
  } catch {
    throw new ApiError(0, "Network error: unable to reach the API server");
  }

  if (res.status === 401) {
    if (!skipAuthRedirect) {
      handleUnauthorized();
    }
    throw new ApiError(401, "Unauthorized");
  }

  if (!res.ok) {
    let message = `Request failed with status ${res.status}`;
    let body_: unknown = null;
    try {
      body_ = await res.json();
      if (body_ && typeof body_ === "object" && "detail" in body_) {
        const detail = (body_ as { detail: unknown }).detail;
        message = typeof detail === "string" ? detail : JSON.stringify(detail);
      }
    } catch {
      // ignore parse errors
    }
    throw new ApiError(res.status, message, body_);
  }

  if (res.status === 204) {
    return undefined as T;
  }

  const text = await res.text();
  if (!text) return undefined as T;
  return JSON.parse(text) as T;
}

export const apiClient = {
  get: <T>(path: string, opts?: RequestOptions) =>
    request<T>(path, { ...opts, method: "GET" }),
  post: <T>(path: string, body?: unknown, opts?: RequestOptions) =>
    request<T>(path, { ...opts, method: "POST", body }),
  patch: <T>(path: string, body?: unknown, opts?: RequestOptions) =>
    request<T>(path, { ...opts, method: "PATCH", body }),
  delete: <T>(path: string, opts?: RequestOptions) =>
    request<T>(path, { ...opts, method: "DELETE" }),
};

export { API_BASE_URL };
