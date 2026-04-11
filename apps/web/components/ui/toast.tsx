"use client"

import * as React from "react"
import { CheckCircle2, AlertCircle, Info, X } from "lucide-react"
import { cn } from "@/lib/utils"

type ToastVariant = "success" | "error" | "info"

interface Toast {
  id: string
  message: string
  variant: ToastVariant
}

interface ToastContextValue {
  toast: (message: string, variant?: ToastVariant) => void
}

const ToastContext = React.createContext<ToastContextValue | null>(null)

export function useToast() {
  const ctx = React.useContext(ToastContext)
  if (!ctx) throw new Error("useToast must be used within ToastProvider")
  return ctx
}

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = React.useState<Toast[]>([])

  const toast = React.useCallback((message: string, variant: ToastVariant = "success") => {
    const id = Math.random().toString(36).slice(2)
    setToasts((prev) => [...prev, { id, message, variant }])
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id))
    }, 4000)
  }, [])

  const dismiss = (id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id))
  }

  const icons: Record<ToastVariant, React.ReactNode> = {
    success: <CheckCircle2 className="h-4 w-4 text-success" />,
    error: <AlertCircle className="h-4 w-4 text-destructive" />,
    info: <Info className="h-4 w-4 text-primary" />,
  }

  return (
    <ToastContext.Provider value={{ toast }}>
      {children}
      <div className="fixed bottom-4 right-4 z-[100] flex flex-col gap-2 max-w-sm">
        {toasts.map((t) => (
          <div
            key={t.id}
            className={cn(
              "flex items-center gap-3 rounded-lg border bg-card px-4 py-3 shadow-elevated animate-slide-in-right",
              t.variant === "error" && "border-destructive/20",
              t.variant === "success" && "border-success/20"
            )}
          >
            {icons[t.variant]}
            <p className="text-sm flex-1">{t.message}</p>
            <button
              onClick={() => dismiss(t.id)}
              className="text-muted-foreground hover:text-foreground transition-colors"
            >
              <X className="h-3.5 w-3.5" />
            </button>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  )
}
