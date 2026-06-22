/**
 * Tabular design tokens.
 *
 * Shared across every app in the monorepo so the next tool inherits the same
 * look. Kept as plain TS (not a Tailwind preset) so both Tailwind config and
 * runtime code can read them. Colours lean trustworthy/financial: deep ink +
 * a confident teal accent, with explicit semantic colours for the
 * reconciliation states (the product's core trust signal).
 */
export const tokens = {
  color: {
    ink: "#0c1322",
    surface: "#ffffff",
    surfaceMuted: "#f5f7fa",
    border: "#dce1e8",
    brand: "#0e7c86", // teal
    brandDark: "#0a5b62",
    // Reconciliation semantics
    reconciled: "#15803d", // green — row balances
    flagged: "#b45309", // amber — needs review
    error: "#b91c1c", // red — hard failure
  },
  radius: {
    sm: "6px",
    md: "10px",
    lg: "16px",
  },
  font: {
    sans: 'ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif',
    mono: 'ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace',
  },
} as const;

export type Tokens = typeof tokens;
