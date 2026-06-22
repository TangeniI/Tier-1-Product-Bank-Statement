/**
 * @tabular/analytics — privacy-friendly product analytics (PostHog/Plausible).
 *
 * SKELETON (increment 1): a typed event vocabulary + a no-op tracker so app
 * code can call `track(...)` everywhere now. When a PostHog key is configured
 * (analytics increment) the no-op is swapped for the real client. Events carry
 * only metadata — never statement contents — per the privacy stance.
 */

export type AnalyticsEvent =
  | { name: "demo_upload_started"; props: { pageCount?: number } }
  | { name: "extraction_completed"; props: { bankProfile: string; confidence: number; flaggedRows: number } }
  | { name: "row_edited"; props: Record<string, never> }
  | { name: "export_clicked"; props: { format: "csv" | "xlsx"; preset: string } }
  | { name: "paywall_hit"; props: { pageCount: number } };

export interface Tracker {
  track(event: AnalyticsEvent): void;
}

const noopTracker: Tracker = {
  track() {
    /* no-op until a provider is configured */
  },
};

export function isAnalyticsConfigured(): boolean {
  return Boolean(process.env.NEXT_PUBLIC_POSTHOG_KEY);
}

export function getTracker(): Tracker {
  // Real provider wired in the analytics increment; no-op keeps call sites stable.
  return noopTracker;
}

export function track(event: AnalyticsEvent): void {
  getTracker().track(event);
}
