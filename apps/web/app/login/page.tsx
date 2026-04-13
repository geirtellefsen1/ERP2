"use client"

import { useEffect, useState, Suspense } from "react"
import { useSearchParams } from "next/navigation"
import { LogIn, Mail, Lock, AlertCircle } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { GoogleIcon, MicrosoftIcon } from "@/components/ui/brand-icons"
import { Logo } from "@/components/ui/logo"
import { LanguageSwitcher } from "@/components/ui/language-switcher"
import { useTranslations } from "@/i18n/provider"
import { API_BASE } from "@/lib/utils"

interface ProvidersStatus {
  google: boolean
  microsoft: boolean
}

function LoginPageInner() {
  const params = useSearchParams()
  const tAuth = useTranslations("Auth")
  const tCommon = useTranslations("Common")
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [error, setError] = useState("")
  const [loading, setLoading] = useState(false)
  const [providers, setProviders] = useState<ProvidersStatus>({
    google: false,
    microsoft: false,
  })
  const [providersLoaded, setProvidersLoaded] = useState(false)

  useEffect(() => {
    const urlError = params.get("error")
    if (urlError) setError(urlError)

    fetch(`${API_BASE}/api/v1/auth/providers`)
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => {
        if (data) setProviders(data)
      })
      .catch(() => {
        /* ignore — buttons just won't appear */
      })
      .finally(() => setProvidersLoaded(true))
  }, [params])

  async function handleLogin(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true)
    setError("")
    try {
      const res = await fetch(`${API_BASE}/api/v1/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      })
      if (!res.ok) {
        const d = await res.json()
        setError(d.detail || "Invalid email or password")
        return
      }
      const data = await res.json()
      localStorage.setItem("bpo_token", data.access_token)
      localStorage.setItem("bpo_user", JSON.stringify(data.user))
      window.location.href = "/dashboard"
    } catch {
      setError("Cannot connect to server. Please try again.")
    } finally {
      setLoading(false)
    }
  }

  function startOAuth(provider: "google" | "microsoft") {
    window.location.href = `${API_BASE}/api/v1/auth/${provider}/login`
  }

  const anyOAuth = providers.google || providers.microsoft

  return (
    <main className="min-h-screen flex">
      {/* Left panel — branding */}
      <div className="hidden lg:flex lg:w-1/2 bg-primary relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-primary to-primary/80" />
        <div className="relative z-10 flex flex-col justify-between p-12 text-primary-foreground">
          <div className="flex items-center gap-3">
            <div className="bg-white rounded-xl p-2 shadow-lg">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src="/logo.svg" alt="ClaudERP" className="h-8 w-auto" />
            </div>
            <span className="text-xl font-semibold">ClaudERP</span>
          </div>
          <div className="space-y-4">
            <h2 className="text-3xl font-bold leading-tight">
              AI-powered accounting
              <br />
              for modern agencies
            </h2>
            <p className="text-primary-foreground/70 max-w-md">
              Manage clients, automate bookkeeping, and generate insights —
              all from a single platform.
            </p>
          </div>
          <div className="space-y-2">
            <p className="text-sm text-primary-foreground/70">
              {tAuth("trustedByHeading")}
            </p>
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2 bg-white/10 backdrop-blur rounded-md px-3 py-1.5 text-xs">
                <GoogleIcon className="h-3.5 w-3.5" />
                Google Workspace
              </div>
              <div className="flex items-center gap-2 bg-white/10 backdrop-blur rounded-md px-3 py-1.5 text-xs">
                <MicrosoftIcon className="h-3.5 w-3.5" />
                Microsoft 365
              </div>
            </div>
          </div>
        </div>
        <div className="absolute -bottom-32 -right-32 w-96 h-96 rounded-full bg-white/5" />
        <div className="absolute -top-16 -right-16 w-64 h-64 rounded-full bg-white/5" />
      </div>

      {/* Right panel — form */}
      <div className="flex-1 flex items-center justify-center p-8">
        <div className="w-full max-w-sm space-y-6">
          <div className="lg:hidden mb-4">
            <Logo size="md" />
          </div>

          <div className="flex items-start justify-between">
            <div>
              <h1 className="text-xl font-semibold">{tAuth("welcomeBack")}</h1>
              <p className="text-sm text-muted-foreground mt-1">
                {tAuth("signInSubtitle")}
              </p>
            </div>
            <LanguageSwitcher />
          </div>

          {/* Social sign-in buttons — larger, more prominent */}
          {anyOAuth && (
            <div className="space-y-2.5">
              {providers.google && (
                <button
                  type="button"
                  onClick={() => startOAuth("google")}
                  className="group flex items-center justify-center gap-3 w-full h-11 px-4 rounded-lg border border-input bg-background text-sm font-medium hover:bg-accent hover:border-foreground/20 transition-all active:scale-[0.99]"
                >
                  <GoogleIcon className="h-5 w-5" />
                  <span>{tAuth("continueWithGoogle")}</span>
                </button>
              )}
              {providers.microsoft && (
                <button
                  type="button"
                  onClick={() => startOAuth("microsoft")}
                  className="group flex items-center justify-center gap-3 w-full h-11 px-4 rounded-lg border border-input bg-background text-sm font-medium hover:bg-accent hover:border-foreground/20 transition-all active:scale-[0.99]"
                >
                  <MicrosoftIcon className="h-5 w-5" />
                  <span>{tAuth("continueWithMicrosoft")}</span>
                </button>
              )}
            </div>
          )}

          {anyOAuth && (
            <div className="relative flex items-center">
              <div className="flex-1 border-t" />
              <span className="px-3 text-2xs uppercase tracking-wider text-muted-foreground">
                {tAuth("orContinueWithEmail")}
              </span>
              <div className="flex-1 border-t" />
            </div>
          )}

          <form onSubmit={handleLogin} className="space-y-4">
            <Input
              label={tAuth("email")}
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder={tAuth("emailPlaceholder")}
              icon={<Mail />}
              required
            />

            <Input
              label={tAuth("password")}
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder={tAuth("passwordPlaceholder")}
              icon={<Lock />}
              required
            />

            {error && (
              <div className="flex items-start gap-2 rounded-lg bg-destructive/10 text-destructive text-sm px-3 py-2.5">
                <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />
                <span className="break-words">{error}</span>
              </div>
            )}

            <Button
              type="submit"
              className="w-full"
              size="lg"
              loading={loading}
            >
              <LogIn className="h-4 w-4" />
              {tCommon("signIn")}
            </Button>
          </form>

          <p className="text-center text-xs text-muted-foreground">
            {tAuth("termsAgreement")}
          </p>
        </div>
      </div>
    </main>
  )
}

export default function LoginPage() {
  return (
    <Suspense
      fallback={
        <main className="min-h-screen flex items-center justify-center">
          <div className="flex items-center gap-3 text-sm text-muted-foreground">
            <div className="h-4 w-4 rounded-full border-2 border-primary border-t-transparent animate-spin" />
            Loading...
          </div>
        </main>
      }
    >
      <LoginPageInner />
    </Suspense>
  )
}
