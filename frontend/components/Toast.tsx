"use client";

import {
  createContext,
  useCallback,
  useContext,
  useState,
  type ReactNode,
} from "react";

type ToastType = "success" | "error" | "warning" | "info";

interface Toast {
  id: string;
  type: ToastType;
  message: string;
}

interface ToastContextValue {
  addToast: (type: ToastType, message: string) => void;
}

const ToastContext = createContext<ToastContextValue>({
  addToast: () => {},
});

export function useToast() {
  return useContext(ToastContext);
}

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const addToast = useCallback((type: ToastType, message: string) => {
    const id = crypto.randomUUID();
    setToasts((prev) => [...prev, { id, type, message }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 4000);
  }, []);

  return (
    <ToastContext.Provider value={{ addToast }}>
      {children}
      <div className="fixed top-20 right-4 z-[100] space-y-2 max-w-sm pointer-events-none">
        {toasts.map((t) => (
          <div
            key={t.id}
            className={`pointer-events-auto flex items-center gap-3 px-4 py-3 rounded-lg shadow-lg animate-[slideIn_0.2s_ease-out] ${
              t.type === "error"
                ? "bg-error/90 text-white"
                : t.type === "success"
                  ? "bg-success/90 text-white"
                  : t.type === "warning"
                    ? "bg-warning/90 text-black"
                    : "bg-surface-container-high text-on-surface border border-white/10"
            }`}
          >
            <span className="material-symbols-outlined text-lg">
              {t.type === "error"
                ? "error"
                : t.type === "success"
                  ? "check_circle"
                  : t.type === "warning"
                    ? "warning"
                    : "info"}
            </span>
            <span className="text-sm font-medium">{t.message}</span>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}
