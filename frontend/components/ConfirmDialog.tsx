"use client";

import { useEffect, useRef } from "react";

interface ConfirmDialogProps {
  open: boolean;
  title: string;
  message: string;
  confirmLabel?: string;
  cancelLabel?: string;
  variant?: "danger" | "primary";
  onConfirm: () => void;
  onCancel: () => void;
}

export function ConfirmDialog({
  open,
  title,
  message,
  confirmLabel = "确认",
  cancelLabel = "取消",
  variant = "primary",
  onConfirm,
  onCancel,
}: ConfirmDialogProps) {
  const dialogRef = useRef<HTMLDialogElement>(null);

  useEffect(() => {
    if (open) {
      dialogRef.current?.showModal();
    } else {
      dialogRef.current?.close();
    }
  }, [open]);

  if (!open) return null;

  return (
    <dialog
      ref={dialogRef}
      className="rounded-2xl p-0 backdrop:bg-black/60 backdrop:backdrop-blur-md bg-surface-container-high border border-white/5 text-on-surface"
      onClose={onCancel}
    >
      <div className="p-6 w-full max-w-sm">
        <h3 className="text-lg font-bold mb-2">{title}</h3>
        <p className="text-sm text-on-surface-variant mb-6 leading-relaxed">{message}</p>
        <div className="flex gap-3 justify-end">
          <button
            onClick={onCancel}
            className="px-4 py-2 rounded-lg text-sm font-bold bg-surface-container-highest text-on-surface hover:bg-surface-bright transition-colors"
          >
            {cancelLabel}
          </button>
          <button
            onClick={onConfirm}
            className={`px-4 py-2 rounded-lg text-sm font-bold text-on-primary-fixed active:scale-[0.98] transition-transform ${
              variant === "danger"
                ? "bg-error hover:opacity-90"
                : "bg-primary hover:opacity-90"
            }`}
          >
            {confirmLabel}
          </button>
        </div>
      </div>
    </dialog>
  );
}
