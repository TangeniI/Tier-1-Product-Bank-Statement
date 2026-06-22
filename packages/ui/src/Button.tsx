import * as React from "react";

type Variant = "primary" | "secondary" | "ghost";

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
}

const base =
  "inline-flex items-center justify-center gap-2 rounded-[10px] px-4 py-2 text-sm font-medium transition-colors disabled:cursor-not-allowed disabled:opacity-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--tab-brand)] focus-visible:ring-offset-2";

const variants: Record<Variant, string> = {
  primary:
    "bg-[var(--tab-brand)] text-white hover:bg-[var(--tab-brand-dark)]",
  secondary:
    "border border-[var(--tab-border)] bg-white text-[var(--tab-ink)] hover:bg-[var(--tab-surface-muted)]",
  ghost: "text-[var(--tab-ink)] hover:bg-[var(--tab-surface-muted)]",
};

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ variant = "primary", className = "", ...props }, ref) => (
    <button
      ref={ref}
      className={`${base} ${variants[variant]} ${className}`}
      {...props}
    />
  ),
);
Button.displayName = "Button";
