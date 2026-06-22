import * as React from "react";

export type BadgeTone = "neutral" | "reconciled" | "flagged" | "error" | "brand";

const tones: Record<BadgeTone, string> = {
  neutral: "bg-[var(--tab-surface-muted)] text-[var(--tab-ink)]",
  reconciled: "bg-green-50 text-[var(--tab-reconciled)]",
  flagged: "bg-amber-50 text-[var(--tab-flagged)]",
  error: "bg-red-50 text-[var(--tab-error)]",
  brand: "bg-teal-50 text-[var(--tab-brand-dark)]",
};

export interface BadgeProps {
  tone?: BadgeTone;
  children: React.ReactNode;
  className?: string;
}

export function Badge({ tone = "neutral", children, className = "" }: BadgeProps) {
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium ${tones[tone]} ${className}`}
    >
      {children}
    </span>
  );
}

/**
 * Confidence badge — the product's core trust signal. Maps a 0–1 score to a
 * tone + label so every surface renders the reconciliation confidence the same
 * way.
 */
export function ConfidenceBadge({ score }: { score: number }) {
  const pct = Math.round(score * 100);
  const tone: BadgeTone =
    score >= 0.99 ? "reconciled" : score >= 0.85 ? "flagged" : "error";
  const label =
    score >= 0.99 ? "Fully reconciled" : score >= 0.85 ? "Mostly reconciled" : "Needs review";
  return (
    <Badge tone={tone}>
      {label} · {pct}%
    </Badge>
  );
}
