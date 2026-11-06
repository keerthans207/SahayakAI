/**
 * Centralized HTTP client for the Sahayak AI backend.
 *
 * - All requests go through the configured VITE_API_BASE_URL.
 * - Errors are normalized to ApiError.
 * - Request IDs from X-Request-Id headers are preserved.
 * - Auth header is injected when a token is available (dev: none needed).
 * - Safe requests (GET) are retried once on network failure.
 */

import type { ApiError } from "@/types/api";

const BASE_URL = ""; // Same-origin requests; Vite proxies /api to EC2.
const TIMEOUT_MS = 30_000;

export class SahayakApiError extends Error {
  constructor(
    public status: number,
    public code: string,
    public detail?: string | unknown,
    public requestId?: string
  ) {
    super(typeof detail === "string" ? detail : code);
    this.name = "SahayakApiError";
  }
}

function getAuthHeaders(): HeadersInit {
  // In development (AUTH_PROVIDER=none), no token is needed.
  // In production wire a real token here (from Entra ID / OIDC).
  return {};
}

async function request<T>(
  method: string,
  path: string,
  options?: {
    body?: unknown;
    formData?: FormData;
    signal?: AbortSignal;
    retries?: number;
  }
): Promise<T> {
  const url = `${BASE_URL}${path}`;
  const headers: any = {
    ...getAuthHeaders(),
  };
  if (options?.body) {
    headers["Content-Type"] = "application/json";
  }

  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), TIMEOUT_MS);
  const signal = options?.signal
    ? // Combine caller's signal with timeout signal
      (() => {
        const combined = new AbortController();
        options.signal!.addEventListener("abort", () => combined.abort());
        controller.signal.addEventListener("abort", () => combined.abort());
        return combined.signal;
      })()
    : controller.signal;

  const retries = options?.retries ?? (method === "GET" ? 1 : 0);

  let lastError: unknown;
  for (let attempt = 0; attempt <= retries; attempt++) {
    try {
      const res = await fetch(url, {
        method,
        headers,
        body: options?.formData
          ? options.formData
          : options?.body
          ? JSON.stringify(options.body)
          : undefined,
        signal,
      });

      clearTimeout(timeout);
      const requestId = res.headers.get("x-request-id") ?? undefined;

      if (!res.ok) {
        let errorBody: ApiError = { error: "request_failed" };
        try {
          errorBody = (await res.json()) as ApiError;
        } catch {
          // ignore
        }
        throw new SahayakApiError(
          res.status,
          errorBody.error ?? "request_failed",
          errorBody.detail,
          requestId
        );
      }

      if (res.status === 204) return undefined as T;
      return (await res.json()) as T;
    } catch (err) {
      lastError = err;
      if (err instanceof SahayakApiError) throw err;
      if (attempt < retries) {
        await new Promise((r) => setTimeout(r, 500 * (attempt + 1)));
      }
    } finally {
      clearTimeout(timeout);
    }
  }
  throw lastError;
}

export const api = {
  get: <T>(path: string, signal?: AbortSignal) =>
    request<T>("GET", path, { signal }),
  post: <T>(path: string, body?: unknown, signal?: AbortSignal) =>
    request<T>("POST", path, { body, signal }),
  patch: <T>(path: string, body?: unknown, signal?: AbortSignal) =>
    request<T>("PATCH", path, { body, signal }),
  delete: <T>(path: string, signal?: AbortSignal) =>
    request<T>("DELETE", path, { signal }),
  upload: <T>(path: string, formData: FormData, signal?: AbortSignal) =>
    request<T>("POST", path, { formData, signal }),
  /** Stream SSE from a POST endpoint, yielding raw token strings. */
  async *stream(path: string, body: unknown, signal?: AbortSignal): AsyncGenerator<string> {
    const url = `${BASE_URL}${path}`;
    const res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...getAuthHeaders() },
      body: JSON.stringify(body),
      signal,
    });
    if (!res.ok || !res.body) throw new SahayakApiError(res.status, "stream_failed");
    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() ?? "";
      for (const line of lines) {
        if (!line.startsWith("data:")) continue;

        const payload = line.slice(5).replace(/^ /, "");

        if (payload.trim() === "[DONE]") return;

        let parsed: unknown;

        try {
          parsed = JSON.parse(payload);
        } catch {
          // Support legacy plain-text SSE events.
          yield payload;
          continue;
        }

        if (!parsed || typeof parsed !== "object") continue;

        const event = parsed as {
          type?: string;
          content?: unknown;
          error?: string;
        };

        if (event.type === "token") {
          if (typeof event.content === "string") {
            yield event.content;
          }
        } else if (event.type === "error") {
          throw new Error(event.error || "Assistant streaming failed");
        } else if (event.type === "done") {
          return;
        }

        // Timing and metadata events are intentionally not rendered.
      }
    }
  },
};
