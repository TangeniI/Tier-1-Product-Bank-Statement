/**
 * @tabular/billing — Stripe (subscription + usage credits), shared.
 *
 * SKELETON (increment 1): pricing catalogue + the usage-gate interface the app
 * codes against. Stripe Checkout + webhooks land in the billing increment.
 */
export * from "./pricing";

export interface UsageState {
  /** Pages already consumed in the current period (free or paid). */
  pagesUsed: number;
  /** Page allowance for the current plan. */
  pageAllowance: number;
}

export function isBillingConfigured(): boolean {
  return Boolean(process.env.STRIPE_SECRET_KEY);
}

/**
 * Decide whether a conversion of `pageCount` pages is allowed. Skeleton uses
 * the free-tier page limit; replaced by Stripe-backed usage in the billing
 * increment.
 */
export function canConvert(usage: UsageState, pageCount: number): boolean {
  return usage.pagesUsed + pageCount <= usage.pageAllowance;
}
