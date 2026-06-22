import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Tabular — Bank statement PDF to CSV & Excel",
  description:
    "Convert a bank or credit-card statement PDF into a clean CSV or Excel file, verified against the statement's own running balance. UK banks. We never store your statements.",
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
