"use client"

import { useEffect, useState, Suspense } from "react"
import { useSearchParams } from "next/navigation"
import { LogIn, Mail, Lock, AlertCircle } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { API_BASE } from "@/lib/utils"

interface ProvidersStatus {
  google: boolean
  microsoft: boolean
}

function LoginPageInner() {
  const params = useSearchParams()
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [error, setError] = useState("")
  const [loading, setLoading] = useState(false)
  const [providers, setProviders] = useState<ProvidersStatus>({
    google: false,
    microsoft: false,
  })

  useEffect(() => {
    // Show any error passed in the URL (e.g. from /auth/callback?error=...)
    const urlError = params.get("error")
    if (urlError) setError(urlError)

    // Discover which OAuth providers are configured on the server
    fetch(`${API_BASE}/api/v1/auth/providers`)
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => {
        if (data) setProviders(data)
      })
      .catch(() => {
        /* ignore — buttons just won't appear */
      })
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
    // Full-page redirect — the API will redirect us through the provider
    // and back to /auth/callback with a token.
    window.location.href = `${API_BASE}/api/v1/auth/${provider}/login`
  }

  const anyOAuth = providers.google || providers.microsoft

  return (
    <main className="min-h-screen flex">
      {/* Left panel — branding */}
      <div className="hidden lg:flex lg:w-1/2 bg-primary relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-primary to-primary/80" />
        <div className="relative z-10 flex flex-col justify-between p-12 text-primary-foreground">
          <div>
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-white/20 backdrop-blur flex items-center justify-center font-bold text-lg">
                N
              </div>
              <span className="text-xl font-semibold">BPO Nexus</span>
            </div>
          </div>
          <div className="space-y-4">
            <h2 className="text-3xl font-bold leading-tight">
              AI-powered accounting
              <br />
              for modern agencies
            </h2>
            <p className="text-primary-foreground/70 max-w-md">
              Manage clients, automate bookkeeping, and generate insights
              — all from a single platform.
            </p>
          </div>
          <p className="text-sm text-primary-foreground/50">Saga Advisory AS</p>
        </div>
        <div className="absolute -bottom-32 -right-32 w-96 h-96 rounded-full bg-white/5" />
        <div className="absolute -top-16 -right-16 w-64 h-64 rounded-full bg-white/5" />
      </div>

      {/* Right panel — form */}
      <div className="flex-1 flex items-center justify-center p-8">
        <div className="w-full max-w-sm space-y-6">
          <div className="lg:hidden flex items-center gap-3 mb-4">
            <div className="w-9 h-9 rounded-lg bg-primary text-primary-foreground flex items-center justify-center font-bold text-sm">
              N
            </div>
            <span className="text-lg font-semibold">BPO Nexus</span>
          </div>

          <div>
            <h1 className="text-xl font-semibold">Welcome back</h1>
            <p className="text-sm text-muted-foreground mt-1">
              Sign in or create an account to continue
            </p>
          </div>

          {/* Social sign-in buttons */}
          {anyOAuth && (
            <div className="space-y-2">
              {providers.google && (
                <button
                  type="button"
                  onClick={() => startOAuth("google")}
                  className="flex items-center justify-center gap-3 w-full h-10 px-4 rounded-md border border-input bg-background text-sm font-medium hover:bg-accent transition-colors"
                >
                  <GoogleIcon />
                  Continue with Google
                </button>
              )}
              {providers.microsoft && (
                <button
                  type="button"
                  onClick={() => startOAuth("microsoft")}
                  className="flex items-center justify-center gap-3 w-full h-10 px-4 rounded-md border border-input bg-background text-sm font-medium hover:bg-accent transition-colors"
                >
                  <MicrosoftIcon />
                  Continue with Microsoft
                </button>
              )}
            </div>
          )}

          {anyOAuth && (
            <div className="relative flex items-center">
              <div className="flex-1 border-t" />
              <span className="px-3 text-2xs uppercase tracking-wider text-muted-foreground">
                or continue with email
              </span>
              <div className="flex-1 border-t" />
            </div>
          )}

          <form onSubmit={handleLogin} className="space-y-4">
            <Input
              label="Email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@company.com"
              icon={<Mail />}
              required
            />

            <Input
              label="Password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter your password"
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
              Sign In
            </Button>
          </form>

          <p className="text-center text-xs text-muted-foreground">
            By signing in, you agree to our Terms and Privacy Policy.
          </p>
        </div>
      </div>
    </main>
  )
}

export default function LoginPage() {
  return (
    <Suspense fallback={<div className="min-h-screen" />}>
      <LoginPageInner />
    </Suspense>
  )
}

// ─── Provider icons (inline SVG, no extra deps) ────────────────────────────

function GoogleIcon() {
  return (
    <svg className="h-4 w-4" viewBox="0 0 24 24" aria-hidden="true">
      <path
        d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
        fill="#4285F4"
      />
      <path
        d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
        fill="#34A853"
      />
      <path
        d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l3.66-2.84z"
        fill="#FBBC05"
      />
      <path
        d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84C6.71 7.31 9.14 5.38 12 5.38z"
        fill="#EA4335"
      />
    </svg>
  )
}

function MicrosoftIcon() {
  return (
    <svg className="h-4 w-4" viewBox="0 0 24 24" aria-hidden="true">
      <path d="M11.4 11.4H1V1h10.4v10.4z" fill="#F25022" />
      <path d="M23 11.4H12.6V1H23v10.4z" fill="#7FBA00" />
      <path d="M11.4 23H1V12.6h10.4V23z" fill="#00A4EF" />
      <path d="M23 23H12.6V12.6H23V23z" fill="#FFB900" />
    </svg>
  )
}
