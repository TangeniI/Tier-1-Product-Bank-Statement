// Lightweight "learning" categoriser. The engine gives a first-pass category
// from keyword rules; this remembers the user's own corrections (per browser,
// via localStorage) so a merchant they've categorised once is auto-applied to
// matching rows and to future statements. No backend required for the demo; the
// same idea moves server-side per-user once auth is wired.

import type { Transaction } from "@/lib/types";

const KEY = "tabular.categoryMemory.v1";

function normalize(desc: string): string {
  return desc
    .toLowerCase()
    .replace(/[^a-z ]+/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function load(): Record<string, string> {
  if (typeof window === "undefined") return {};
  try {
    return JSON.parse(window.localStorage.getItem(KEY) ?? "{}");
  } catch {
    return {};
  }
}

function save(map: Record<string, string>): void {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(KEY, JSON.stringify(map));
  } catch {
    /* storage unavailable (private mode, etc.) — degrade silently */
  }
}

/** Remember that this description should map to this category. */
export function learn(description: string, category: string | null): void {
  const key = normalize(description);
  if (!key) return;
  const map = load();
  if (category) {
    map[key] = category;
  } else {
    delete map[key];
  }
  save(map);
}

/** Best learned category for a description, or null. */
export function suggest(description: string): string | null {
  const map = load();
  const n = normalize(description);
  if (!n) return null;
  if (map[n]) return map[n]!;
  // Fuzzy: a learned merchant key contained in this description (or vice versa).
  for (const [k, v] of Object.entries(map)) {
    if (k.length >= 3 && (n.includes(k) || k.includes(n))) return v;
  }
  return null;
}

/** Apply learned categories over a set of rows (user memory wins). */
export function applyLearned(rows: Transaction[]): Transaction[] {
  let changed = false;
  const next = rows.map((r) => {
    const s = suggest(r.description);
    if (s && s !== r.category) {
      changed = true;
      return { ...r, category: s };
    }
    return r;
  });
  return changed ? next : rows;
}
