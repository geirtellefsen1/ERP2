"use client"

import { useState, useRef, useEffect } from "react"
import { ChevronDown, Check, Building2, ExternalLink, X, Globe } from "lucide-react"
import { cn } from "@/lib/utils"
import { useClientContext } from "@/lib/client-context"
import { Button } from "@/components/ui/button"
import { useLocale } from "@/i18n/provider"
import { locales, localeLabels, type Locale } from "@/i18n/config"

const LOCALE_FLAGS: Record<string, string> = {
  en: "EN",
  nb: "NO",
  sv: "SE",
  fi: "FI",
}

export default function TopBar() {
  const { clients, selectedClient, setSelectedClientId } = useClientContext()
  const { locale, setLocale } = useLocale()
  const [open, setOpen] = useState(false)
  const [langOpen, setLangOpen] = useState(false)
  const [search, setSearch] = useState("")
  const ref = useRef<HTMLDivElement>(null)
  const langRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false)
      }
      if (langRef.current && !langRef.current.contains(e.target as Node)) {
        setLangOpen(false)
      }
    }
    document.addEventListener("mousedown", handler)
    return () => document.removeEventListener("mousedown", handler)
  }, [])

  const filtered = search
    ? clients.filter((c) =>
        c.name.toLowerCase().includes(search.toLowerCase())
      )
    : clients

  const openPortal = () => {
    if (selectedClient) {
      window.open(`/portal/${selectedClient.id}`, "_blank")
    }
  }

  return (
    <div className="border-b border-border bg-background/60 backdrop-blur sticky top-0 z-30">
      <div className="flex items-center justify-between px-6 py-2.5">
        <div className="flex items-center gap-2 text-sm" ref={ref}>
          <span className="text-muted-foreground">ClaudERP</span>
          <span className="text-muted-foreground">/</span>

          <div className="relative">
            <button
              onClick={() => setOpen((o) => !o)}
              className={cn(
                "flex items-center gap-1.5 px-2 py-1 rounded-md text-sm font-medium",
                "hover:bg-accent transition-colors",
                selectedClient ? "text-foreground" : "text-muted-foreground"
              )}
            >
              <Building2 className="h-3.5 w-3.5" />
              {selectedClient ? selectedClient.name : "All clients"}
              <ChevronDown className="h-3.5 w-3.5" />
            </button>

            {open && (
              <div className="absolute left-0 top-full mt-1 w-72 rounded-md border border-border bg-popover shadow-md z-50">
                <div className="p-2 border-b">
                  <input
                    autoFocus
                    type="text"
                    placeholder="Search clients..."
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    className="w-full px-2 py-1.5 text-sm bg-background border border-input rounded-md focus:outline-none focus:ring-1 focus:ring-ring"
                  />
                </div>
                <div className="max-h-72 overflow-y-auto py-1">
                  <button
                    onClick={() => {
                      setSelectedClientId(null)
                      setOpen(false)
                      setSearch("")
                    }}
                    className="flex items-center gap-2 w-full px-3 py-2 text-sm hover:bg-accent text-left"
                  >
                    <Check
                      className={cn(
                        "h-3.5 w-3.5",
                        selectedClient === null ? "opacity-100" : "opacity-0"
                      )}
                    />
                    <span className="font-medium">All clients</span>
                    <span className="ml-auto text-xs text-muted-foreground">
                      Agency overview
                    </span>
                  </button>
                  {filtered.length === 0 ? (
                    <p className="px-3 py-2 text-xs text-muted-foreground">
                      No clients match.
                    </p>
                  ) : (
                    filtered.map((c) => (
                      <button
                        key={c.id}
                        onClick={() => {
                          setSelectedClientId(c.id)
                          setOpen(false)
                          setSearch("")
                        }}
                        className="flex items-center gap-2 w-full px-3 py-2 text-sm hover:bg-accent text-left"
                      >
                        <Check
                          className={cn(
                            "h-3.5 w-3.5",
                            selectedClient?.id === c.id ? "opacity-100" : "opacity-0"
                          )}
                        />
                        <span className="font-medium truncate">{c.name}</span>
                        <span className="ml-auto text-xs text-muted-foreground shrink-0">
                          {c.industry || c.country}
                        </span>
                      </button>
                    ))
                  )}
                </div>
              </div>
            )}
          </div>

          {selectedClient && (
            <button
              onClick={() => setSelectedClientId(null)}
              title="Clear client filter"
              className="p-0.5 rounded hover:bg-accent text-muted-foreground"
            >
              <X className="h-3 w-3" />
            </button>
          )}
        </div>

        <div className="flex items-center gap-2">
          {/* Locale Switcher */}
          <div className="relative" ref={langRef}>
            <button
              onClick={() => setLangOpen((o) => !o)}
              className="flex items-center gap-1.5 px-2 py-1 rounded-md text-xs font-medium text-muted-foreground hover:text-foreground hover:bg-accent transition-colors"
              title="Change language"
            >
              <Globe className="h-3.5 w-3.5" />
              {LOCALE_FLAGS[locale]}
            </button>

            {langOpen && (
              <div className="absolute right-0 top-full mt-1 w-44 rounded-md border border-border bg-popover shadow-md z-50 py-1">
                {locales.map((l) => (
                  <button
                    key={l}
                    onClick={() => {
                      setLocale(l)
                      setLangOpen(false)
                    }}
                    className="flex items-center gap-2 w-full px-3 py-2 text-sm hover:bg-accent text-left"
                  >
                    <Check
                      className={cn(
                        "h-3.5 w-3.5",
                        locale === l ? "opacity-100" : "opacity-0"
                      )}
                    />
                    <span className="text-xs font-medium text-muted-foreground w-5">
                      {LOCALE_FLAGS[l]}
                    </span>
                    <span>{localeLabels[l]}</span>
                  </button>
                ))}
              </div>
            )}
          </div>

          {selectedClient && (
            <Button
              variant="outline"
              size="sm"
              onClick={openPortal}
              title="Open the client's portal view in a new tab"
            >
              View as client
              <ExternalLink className="h-3.5 w-3.5 ml-1.5" />
            </Button>
          )}
        </div>
      </div>
    </div>
  )
}
