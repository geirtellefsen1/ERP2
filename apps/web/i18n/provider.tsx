"use client"

/**
 * Client-side i18n provider for Tier 1.5 scaffolding.
 *
 * This deliberately does NOT use next-intl's server-side middleware
 * (which would require restructuring the whole app/ directory under
 * [locale]/). Instead it reads the active locale from localStorage on
 * mount, loads the appropriate messages JSON, and exposes it via React
 * context — a low-risk incremental adoption path.
 *
 * Migration to full next-intl middleware routing can happen later once
 * we have more translated pages to justify the restructuring.
 *
 * Usage:
 *   import { useTranslations } from "@/i18n/provider"
 *   const t = useTranslations("Dashboard")
 *   return <h1>{t("goodMorning")}</h1>
 */

import * as React from "react"
import { defaultLocale, isLocale, type Locale } from "./config"
import en from "@/messages/en.json"
import nb from "@/messages/nb.json"
import sv from "@/messages/sv.json"
import fi from "@/messages/fi.json"

type Messages = typeof en
type Namespace = keyof Messages

const MESSAGES: Record<Locale, Messages> = { en, nb, sv, fi }

interface I18nContextValue {
  locale: Locale
  setLocale: (l: Locale) => void
  messages: Messages
}

const I18nContext = React.createContext<I18nContextValue | null>(null)

const STORAGE_KEY = "claud_erp_locale"

export function I18nProvider({ children }: { children: React.ReactNode }) {
  const [locale, setLocaleState] = React.useState<Locale>(defaultLocale)

  React.useEffect(() => {
    // Read saved preference on mount
    try {
      const stored = localStorage.getItem(STORAGE_KEY)
      if (stored && isLocale(stored)) {
        setLocaleState(stored)
      }
    } catch {
      /* localStorage unavailable — use default */
    }
  }, [])

  const setLocale = React.useCallback((l: Locale) => {
    setLocaleState(l)
    try {
      localStorage.setItem(STORAGE_KEY, l)
    } catch {
      /* ignore */
    }
  }, [])

  const value = React.useMemo<I18nContextValue>(
    () => ({
      locale,
      setLocale,
      messages: MESSAGES[locale],
    }),
    [locale, setLocale]
  )

  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>
}

/**
 * Access the active locale and switcher. Use in components that need to
 * render a language picker or adapt behaviour per locale.
 */
export function useLocale() {
  const ctx = React.useContext(I18nContext)
  if (!ctx) {
    // Graceful fallback — if the provider isn't mounted (e.g. during SSR
    // of a page that doesn't use I18nProvider), return the default.
    return {
      locale: defaultLocale,
      setLocale: () => {},
      messages: MESSAGES[defaultLocale],
    }
  }
  return ctx
}

/**
 * Namespaced translation hook. `useTranslations("Dashboard")` returns a
 * function `t(key)` that looks up `Dashboard.<key>` in the active locale.
 *
 * Unknown keys return the key itself so the UI never shows undefined —
 * easier to spot gaps during manual testing.
 */
export function useTranslations<N extends Namespace>(namespace: N) {
  const { messages } = useLocale()
  return React.useCallback(
    (key: keyof Messages[N]) => {
      const ns = messages[namespace] as Record<string, string>
      return ns[key as string] ?? (key as string)
    },
    [messages, namespace]
  )
}
