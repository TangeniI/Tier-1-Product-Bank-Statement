import type { Metadata } from "next";
import "./globals.css";

const DESCRIPTION =
  "Convert a bank or credit-card statement PDF into a clean CSV, Excel or OFX file, verified against the statement's own running balance. UK banks. We never store your statements.";

export const metadata: Metadata = {
  title: "Tabular — Bank statement PDF to CSV & Excel",
  description: DESCRIPTION,
  applicationName: "Tabular",
  // Inline SVG favicon (ledger glyph) — no asset file needed.
  icons: {
    icon: "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Crect width='100' height='100' rx='20' fill='%230d9488'/%3E%3Ctext x='50' y='72' font-size='64' text-anchor='middle' fill='white' font-family='Arial'%3E%E2%9A%96%3C/text%3E%3C/svg%3E",
  },
  openGraph: {
    title: "Tabular — Bank statement PDF to CSV & Excel",
    description: DESCRIPTION,
    type: "website",
    siteName: "Tabular",
  },
  twitter: {
    card: "summary_large_image",
    title: "Tabular — Bank statement PDF to CSV & Excel",
    description: DESCRIPTION,
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en-GB">
      <body>{children}</body>
    </html>
  );
}
