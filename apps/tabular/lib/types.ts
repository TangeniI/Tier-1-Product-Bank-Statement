// Mirrors services/engine/app/schema.py on the TypeScript side.

export interface Transaction {
  date: string;
  description: string;
  money_in: number | null;
  money_out: number | null;
  balance: number | null;
  category: string | null;
  reconciled: boolean;
  flag_reason: string | null;
}

export interface ReconcileSummary {
  total_rows: number;
  movement_rows: number;
  reconciled_rows: number;
  flagged_rows: number;
  opening_balance: number | null;
  closing_balance: number | null;
  computed_closing: number | null;
  balanced: boolean;
}

export interface ExtractionResult {
  bank_profile: string;
  page_count: number;
  has_text_layer: boolean;
  overall_confidence: number;
  rows: Transaction[];
  summary: ReconcileSummary;
  warnings: string[];
}

export interface Preset {
  name: string;
  label: string;
}
