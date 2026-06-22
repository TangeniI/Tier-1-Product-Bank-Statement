// Server-only helper: the engine URL is never exposed to the browser.
export const ENGINE_URL = process.env.ENGINE_URL ?? "http://localhost:8000";
