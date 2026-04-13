/**
 * i18n configuration for ClaudERP.
 *
 * Locale scope for Tier 1.5: scaffolding only. The machinery is in place and
 * one working example (the login page) is translated. Other pages are
 * migrated in Tier 2+ as they're touched.
 *
 * Adding a new locale = drop a messages/<locale>.json file and add the tag
 * to the `locales` array below.
 */

export const locales = ["en", "nb", "sv", "fi"] as const
export const defaultLocale = "en" as const

export type Locale = (typeof locales)[number]

export const localeLabels: Record<Locale, string> = {
  en: "English",
  nb: "Norsk (Bokmål)",
  sv: "Svenska",
  fi: "Suomi",
}

/**
 * Map a country code (NO/SE/FI) to the appropriate IETF locale tag used
 * by messages/ files. Used by the portal to auto-select the client's
 * language based on their jurisdiction.
 */
export function countryToLocale(country: string): Locale {
  const cc = country.toUpperCase()
  if (cc === "NO") return "nb"
  if (cc === "SE") return "sv"
  if (cc === "FI") return "fi"
  return "en"
}

export function isLocale(value: string): value is Locale {
  return (locales as readonly string[]).includes(value)
}
