/**
 * Pricing config — prices are config values, NOT hard-coded in flows, so they
 * can be A/B tested after launch (per the brief). Currency in GBP pence.
 *
 * `stripePriceId` is filled in once the Stripe products exist (billing
 * increment). Until then the catalogue still renders for the pricing page.
 */
export interface PricingPlan {
  id: string;
  name: string;
  kind: "free" | "credits" | "subscription";
  /** Headline price in GBP pence. 0 for free tier. */
  pricePence: number;
  /** For credits: documents included. For subscription: pages/month. */
  allowance: number;
  allowanceUnit: "statements" | "pages/month";
  blurb: string;
  stripePriceId: string | null;
}

export const FREE_PAGE_LIMIT = Number(
  process.env.NEXT_PUBLIC_FREE_PAGE_LIMIT ?? 5,
);

export const pricingPlans: PricingPlan[] = [
  {
    id: "free",
    name: "Free",
    kind: "free",
    pricePence: 0,
    allowance: FREE_PAGE_LIMIT,
    allowanceUnit: "pages/month",
    blurb: "Try it free — one statement, no signup.",
    stripePriceId: null,
  },
  {
    id: "payg-10",
    name: "Pay as you go",
    kind: "credits",
    pricePence: 900,
    allowance: 10,
    allowanceUnit: "statements",
    blurb: "10 statement credits. For occasional conversions.",
    stripePriceId: null,
  },
  {
    id: "pro-monthly",
    name: "Pro",
    kind: "subscription",
    pricePence: 1500,
    allowance: 300,
    allowanceUnit: "pages/month",
    blurb: "For bookkeepers with recurring volume.",
    stripePriceId: null,
  },
];

export function formatGbp(pence: number): string {
  return new Intl.NumberFormat("en-GB", {
    style: "currency",
    currency: "GBP",
  }).format(pence / 100);
}
