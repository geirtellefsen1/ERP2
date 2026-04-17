import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

const LOCALE_MAP: Record<string, string> = {
  NOK: "nb-NO",
  SEK: "sv-SE",
  EUR: "fi-FI",
  GBP: "en-GB",
  USD: "en-US",
  ZAR: "en-ZA",
}

export function formatCurrency(amount: number, currency = "NOK"): string {
  const locale = LOCALE_MAP[currency] || "nb-NO"
  return new Intl.NumberFormat(locale, {
    style: "currency",
    currency,
    minimumFractionDigits: 2,
  }).format(amount)
}

export function formatDate(date: string | Date): string {
  return new Intl.DateTimeFormat("nb-NO", {
    day: "numeric",
    month: "short",
    year: "numeric",
  }).format(new Date(date))
}

export function formatDateRelative(date: string | Date): string {
  const now = new Date()
  const d = new Date(date)
  const diffMs = now.getTime() - d.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMs / 3600000)
  const diffDays = Math.floor(diffMs / 86400000)

  if (diffMins < 1) return "just now"
  if (diffMins < 60) return `${diffMins}m ago`
  if (diffHours < 24) return `${diffHours}h ago`
  if (diffDays < 7) return `${diffDays}d ago`
  return formatDate(date)
}

export function getInitials(name: string): string {
  return name
    .split(" ")
    .map((n) => n[0])
    .join("")
    .toUpperCase()
    .slice(0, 2)
}

// API_BASE — in production (same-origin with nginx proxy), set
// NEXT_PUBLIC_API_URL="" at build time. Falls back to localhost:8000 for
// dev only when the env var is undefined. Use nullish coalescing so empty
// string ("") passes through as same-origin.
const envApiUrl = process.env.NEXT_PUBLIC_API_URL
export const API_BASE =
  typeof envApiUrl === "string" ? envApiUrl : "http://localhost:8000"
