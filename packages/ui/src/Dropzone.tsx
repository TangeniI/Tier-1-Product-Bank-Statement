"use client";

import * as React from "react";

export interface DropzoneProps {
  onFile: (file: File) => void;
  accept?: string;
  disabled?: boolean;
  hint?: string;
}

/**
 * Drag-and-drop upload box for the "Try it free" landing surface. Single file,
 * PDF by default. Purely presentational + callback — no network logic here.
 */
export function Dropzone({
  onFile,
  accept = "application/pdf",
  disabled = false,
  hint = "PDF statement, up to ~20 pages",
}: DropzoneProps) {
  const [dragging, setDragging] = React.useState(false);
  const inputRef = React.useRef<HTMLInputElement>(null);

  function handleFiles(files: FileList | null) {
    const file = files?.[0];
    if (file) onFile(file);
  }

  return (
    <div
      onDragOver={(e) => {
        e.preventDefault();
        if (!disabled) setDragging(true);
      }}
      onDragLeave={() => setDragging(false)}
      onDrop={(e) => {
        e.preventDefault();
        setDragging(false);
        if (!disabled) handleFiles(e.dataTransfer.files);
      }}
      onClick={() => !disabled && inputRef.current?.click()}
      role="button"
      tabIndex={0}
      aria-disabled={disabled}
      onKeyDown={(e) => {
        if ((e.key === "Enter" || e.key === " ") && !disabled) {
          e.preventDefault();
          inputRef.current?.click();
        }
      }}
      className={`flex cursor-pointer flex-col items-center justify-center gap-2 rounded-[16px] border-2 border-dashed px-6 py-12 text-center transition-colors ${
        dragging
          ? "border-[var(--tab-brand)] bg-teal-50"
          : "border-[var(--tab-border)] bg-[var(--tab-surface-muted)] hover:border-[var(--tab-brand)]"
      } ${disabled ? "pointer-events-none opacity-60" : ""}`}
    >
      <input
        ref={inputRef}
        type="file"
        accept={accept}
        className="hidden"
        onChange={(e) => handleFiles(e.target.files)}
        disabled={disabled}
      />
      <p className="text-base font-medium text-[var(--tab-ink)]">
        Drop your statement here, or click to choose
      </p>
      <p className="text-sm text-gray-500">{hint}</p>
    </div>
  );
}
