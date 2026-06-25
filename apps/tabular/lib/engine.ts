// Server-only helper: the engine URL is never exposed to the browser.
export const ENGINE_URL = process.env.ENGINE_URL ?? "http://localhost:8000";

// Shared secret sent to the engine so it can reject direct (non-app) callers.
// Set the same value as ENGINE_API_TOKEN on both Vercel and the engine host.
export const ENGINE_API_TOKEN = process.env.ENGINE_API_TOKEN ?? "";

// Headers to authenticate the app→engine call (empty token = header omitted).
export function engineHeaders(extra: Record<string, string> = {}): Record<string, string> {
  return ENGINE_API_TOKEN ? { ...extra, "x-engine-token": ENGINE_API_TOKEN } : extra;
}
