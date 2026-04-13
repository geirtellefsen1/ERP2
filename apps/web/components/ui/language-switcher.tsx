"use client"

import { Globe } from "lucide-react"
import { useLocale } from "@/i18n/provider"
import { locales, localeLabels, type Locale } from "@/i18n/config"
import { cn } from "@/lib/utils"

interface LanguageSwitcherProps {
  /** Compact (just a globe icon + code) or full (labelled dropdown) */
  variant?: "compact" | "full"
  className?: string
}

export function LanguageSwitcher({
  variant = "compact",
  className,
}: LanguageSwitcherProps) {
  const { locale, setLocale } = useLocale()

  return (
    <div className={cn("relative inline-flex items-center", className)}>
      <Globe className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground pointer-events-none" />
      <select
        value={locale}
        onChange={(e) => setLocale(e.target.value as Locale)}
        className={cn(
          "appearance-none rounded-md border border-input bg-background pl-7 pr-7 text-xs font-medium text-foreground focus:outline-none focus:ring-2 focus:ring-ring",
          variant === "compact" ? "h-7" : "h-9 text-sm pl-8 pr-8"
        )}
        aria-label="Select language"
      >
        {locales.map((l) => (
          <option key={l} value={l}>
            {variant === "compact" ? l.toUpperCase() : localeLabels[l]}
          </option>
        ))}
      </select>
    </div>
  )
}
