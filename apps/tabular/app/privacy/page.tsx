import Link from "next/link";

export const metadata = {
  title: "Privacy Policy — Tabular",
};

export default function PrivacyPage() {
  return (
    <main className="mx-auto max-w-2xl px-5 py-12">
      <Link href="/" className="text-sm text-[var(--tab-brand-dark)] underline">
        ← Back to Tabular
      </Link>
      <h1 className="mt-6 text-2xl font-bold">Privacy Policy</h1>
      <p className="mt-2 text-sm text-gray-500">Last updated: June 2026</p>

      <div className="mt-6 space-y-5 text-sm leading-relaxed text-gray-700">
        <section>
          <h2 className="font-semibold text-[var(--tab-ink)]">The short version</h2>
          <p className="mt-1">
            Tabular converts your bank statement entirely in memory. We do not
            store your statements, we do not keep the extracted transactions
            after your session, and we never use your data to train any model.
          </p>
        </section>

        <section>
          <h2 className="font-semibold text-[var(--tab-ink)]">What we process</h2>
          <p className="mt-1">
            When you upload a statement, the file is sent to our extraction
            engine, processed in memory to produce a table of transactions, and
            then discarded. The file is not written to disk and is not retained
            after the response is returned.
          </p>
        </section>

        <section>
          <h2 className="font-semibold text-[var(--tab-ink)]">AI extraction</h2>
          <p className="mt-1">
            For scanned (image-only) statements, Tabular can use a third-party AI
            vision provider to read the document. In that case the statement is
            transmitted to that provider solely to perform the extraction. This
            path is only used when enabled and only for scanned PDFs; text-based
            statements are processed entirely by our own deterministic engine.
          </p>
        </section>

        <section>
          <h2 className="font-semibold text-[var(--tab-ink)]">Analytics</h2>
          <p className="mt-1">
            We may collect anonymous, privacy-friendly product analytics (e.g.
            that an export happened) to improve the service. These events never
            include the contents of your statement.
          </p>
        </section>

        <section>
          <h2 className="font-semibold text-[var(--tab-ink)]">Your rights (UK GDPR)</h2>
          <p className="mt-1">
            Because statements are not stored, there is no retained personal data
            to access, correct, or erase after your session ends. For any
            question about this policy, contact the site owner.
          </p>
        </section>

        <p className="text-xs text-gray-400">
          This page is a plain-language summary for a demo product and is not
          legal advice. A production launch should have this reviewed by a
          qualified adviser.
        </p>
      </div>
    </main>
  );
}
