import Link from "next/link";

export const metadata = {
  title: "Terms of Use — Tabular",
};

export default function TermsPage() {
  return (
    <main className="mx-auto max-w-2xl px-5 py-12">
      <Link href="/" className="text-sm text-[var(--tab-brand-dark)] underline">
        ← Back to Tabular
      </Link>
      <h1 className="mt-6 text-2xl font-bold">Terms of Use</h1>
      <p className="mt-2 text-sm text-gray-500">Last updated: June 2026</p>

      <div className="mt-6 space-y-5 text-sm leading-relaxed text-gray-700">
        <section>
          <h2 className="font-semibold text-[var(--tab-ink)]">What Tabular does</h2>
          <p className="mt-1">
            Tabular extracts transactions from a bank or credit-card statement
            PDF and checks each row against the running balance printed on that
            statement. Rows that do not reconcile are flagged for your review.
          </p>
        </section>

        <section>
          <h2 className="font-semibold text-[var(--tab-ink)]">Accuracy &amp; your responsibility</h2>
          <p className="mt-1">
            Tabular verifies the <strong>internal consistency</strong> of a
            statement against its own running balance. It does not verify the
            correctness of the underlying bank data, and extraction may contain
            errors — especially on scanned documents. You are responsible for
            reviewing all flagged rows and checking the exported file before
            relying on it for accounting, tax, or any other purpose. Tabular is
            provided &quot;as is&quot;, without warranties, to the maximum extent
            permitted by law.
          </p>
        </section>

        <section>
          <h2 className="font-semibold text-[var(--tab-ink)]">Acceptable use</h2>
          <p className="mt-1">
            Only upload statements you are entitled to process. Do not use the
            service unlawfully or attempt to disrupt it.
          </p>
        </section>

        <section>
          <h2 className="font-semibold text-[var(--tab-ink)]">Privacy</h2>
          <p className="mt-1">
            See our{" "}
            <Link href="/privacy" className="text-[var(--tab-brand-dark)] underline">
              Privacy Policy
            </Link>{" "}
            for how statements are handled (in memory, not stored, never used for
            training).
          </p>
        </section>

        <p className="text-xs text-gray-400">
          This page is a plain-language summary for a demo product and is not
          legal advice.
        </p>
      </div>
    </main>
  );
}
