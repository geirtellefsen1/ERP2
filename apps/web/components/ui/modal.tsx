"use client"

import * as React from "react"
import { X } from "lucide-react"
import { cn } from "@/lib/utils"

interface ModalProps {
  open: boolean
  onClose: () => void
  children: React.ReactNode
  className?: string
}

function Modal({ open, onClose, children, className }: ModalProps) {
  React.useEffect(() => {
    if (open) {
      document.body.style.overflow = "hidden"
      const handleEsc = (e: KeyboardEvent) => {
        if (e.key === "Escape") onClose()
      }
      document.addEventListener("keydown", handleEsc)
      return () => {
        document.body.style.overflow = ""
        document.removeEventListener("keydown", handleEsc)
      }
    }
    document.body.style.overflow = ""
  }, [open, onClose])

  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div
        className="fixed inset-0 bg-black/40 backdrop-blur-[2px] animate-fade-in"
        onClick={onClose}
      />
      <div
        className={cn(
          "relative z-50 w-full max-w-lg mx-4 rounded-xl bg-card border shadow-elevated animate-scale-in",
          className
        )}
      >
        {children}
      </div>
    </div>
  )
}

function ModalHeader({
  className,
  children,
  onClose,
  ...props
}: React.HTMLAttributes<HTMLDivElement> & { onClose?: () => void }) {
  return (
    <div
      className={cn("flex items-center justify-between p-5 pb-3", className)}
      {...props}
    >
      <div className="space-y-1">{children}</div>
      {onClose && (
        <button
          onClick={onClose}
          className="rounded-md p-1 text-muted-foreground hover:text-foreground hover:bg-accent transition-colors"
        >
          <X className="h-4 w-4" />
        </button>
      )}
    </div>
  )
}

function ModalTitle({
  className,
  ...props
}: React.HTMLAttributes<HTMLHeadingElement>) {
  return (
    <h2
      className={cn("text-base font-semibold leading-none", className)}
      {...props}
    />
  )
}

function ModalDescription({
  className,
  ...props
}: React.HTMLAttributes<HTMLParagraphElement>) {
  return (
    <p className={cn("text-sm text-muted-foreground mt-1", className)} {...props} />
  )
}

function ModalContent({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("px-5 pb-5", className)} {...props} />
}

function ModalFooter({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        "flex items-center justify-end gap-2 border-t px-5 py-3",
        className
      )}
      {...props}
    />
  )
}

export { Modal, ModalHeader, ModalTitle, ModalDescription, ModalContent, ModalFooter }
