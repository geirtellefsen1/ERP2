"use client"

import { useState, useEffect } from "react"
import { CreditCard, ArrowUpRight, Check, Loader2, Zap, Shield, Building } from "lucide-react"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { useToast } from "@/components/ui/toast"
import { apiGet, apiPost } from "@/lib/api"

interface Subscription {
  id: number
  agency_id: number
  stripe_customer_id: string
  stripe_subscription_id: string | null
  tier: string
  status: string
  current_period_end: string | null
}

const TIERS = [
  {
    key: "starter",
    label: "Starter",
    icon: Zap,
    price: "Free",
    description: "For small agencies getting started",
    features: ["DSR requests", "Basic reports", "Bank feeds"],
    missing: ["Consolidation", "AI chat", "Advanced reports", "API access", "Custom integrations", "SLA"],
  },
  {
    key: "growth",
    label: "Growth",
    icon: Building,
    price: "$49/mo",
    description: "For growing agencies with AI needs",
    features: ["DSR requests", "Basic reports", "Bank feeds", "Consolidation", "AI chat", "Advanced reports"],
    missing: ["API access", "Custom integrations", "SLA"],
  },
  {
    key: "enterprise",
    label: "Enterprise",
    icon: Shield,
    price: "$199/mo",
    description: "Full platform with premium support",
    features: [
      "DSR requests",
      "Basic reports",
      "Bank feeds",
      "Consolidation",
      "AI chat",
      "Advanced reports",
      "API access",
      "Custom integrations",
      "SLA",
    ],
    missing: [],
  },
]

export default function BillingPage() {
  const [subscription, setSubscription] = useState<Subscription | null>(null)
  const [loading, setLoading] = useState(true)
  const [subscribing, setSubscribing] = useState<string | null>(null)
  const [portalLoading, setPortalLoading] = useState(false)
  const { toast } = useToast()

  const loadSubscription = async () => {
    try {
      const data = await apiGet<Subscription | null>("/billing/subscription")
      setSubscription(data)
    } catch (e: any) {
      toast(e.message || "Failed to load subscription")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadSubscription()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const currentTier = subscription?.tier || "starter"

  const handleSubscribe = async (tier: string) => {
    setSubscribing(tier)
    try {
      const data = await apiPost<Subscription>("/billing/subscribe", { tier })
      setSubscription(data)
      toast(`Subscribed to ${tier} plan`)
    } catch (e: any) {
      toast(e.message || "Subscription failed")
    } finally {
      setSubscribing(null)
    }
  }

  const handlePortal = async () => {
    setPortalLoading(true)
    try {
      const data = await apiPost<{ url: string }>("/billing/portal", {})
      window.location.href = data.url
    } catch (e: any) {
      toast(e.message || "Could not open billing portal")
      setPortalLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-16 text-muted-foreground">
        <Loader2 className="h-5 w-5 animate-spin mr-2" />
        Loading billing info...
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold">Billing & Plan</h1>
        <p className="text-sm text-muted-foreground mt-0.5">
          Manage your subscription and payment methods
        </p>
      </div>

      {/* Current plan summary */}
      {subscription && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <CreditCard className="h-5 w-5" />
              Current Subscription
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium capitalize">{subscription.tier} Plan</p>
                <p className="text-sm text-muted-foreground">
                  Status: <Badge variant={subscription.status === "active" ? "success" : "default"}>{subscription.status}</Badge>
                </p>
                {subscription.current_period_end && (
                  <p className="text-sm text-muted-foreground mt-1">
                    Current period ends: {new Date(subscription.current_period_end).toLocaleDateString()}
                  </p>
                )}
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={handlePortal}
                disabled={portalLoading}
              >
                {portalLoading ? (
                  <Loader2 className="h-4 w-4 animate-spin mr-1" />
                ) : (
                  <ArrowUpRight className="h-4 w-4 mr-1" />
                )}
                Manage Subscription
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Tier comparison cards */}
      <div>
        <h2 className="text-lg font-medium mb-4">
          {subscription ? "Change Plan" : "Choose a Plan"}
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {TIERS.map((tier) => {
            const isCurrent = currentTier === tier.key
            const tierIndex = TIERS.findIndex((t) => t.key === tier.key)
            const currentIndex = TIERS.findIndex((t) => t.key === currentTier)
            const isUpgrade = tierIndex > currentIndex

            return (
              <Card
                key={tier.key}
                className={cn(
                  "relative",
                  isCurrent && "border-primary ring-1 ring-primary/20"
                )}
              >
                {isCurrent && (
                  <Badge className="absolute -top-2 left-4" variant="default">
                    Current
                  </Badge>
                )}
                <CardHeader>
                  <div className="flex items-center gap-2">
                    <tier.icon className="h-5 w-5 text-primary" />
                    <CardTitle>{tier.label}</CardTitle>
                  </div>
                  <CardDescription>{tier.description}</CardDescription>
                  <p className="text-2xl font-bold mt-2">{tier.price}</p>
                </CardHeader>
                <CardContent className="space-y-3">
                  <ul className="space-y-1.5">
                    {tier.features.map((f) => (
                      <li key={f} className="flex items-center gap-2 text-sm">
                        <Check className="h-4 w-4 text-green-500 shrink-0" />
                        {f}
                      </li>
                    ))}
                    {tier.missing.map((f) => (
                      <li
                        key={f}
                        className="flex items-center gap-2 text-sm text-muted-foreground line-through"
                      >
                        <span className="h-4 w-4 shrink-0" />
                        {f}
                      </li>
                    ))}
                  </ul>
                  {!isCurrent && (
                    <Button
                      className="w-full mt-4"
                      variant={isUpgrade ? "default" : "outline"}
                      size="sm"
                      disabled={subscribing !== null}
                      onClick={() => handleSubscribe(tier.key)}
                    >
                      {subscribing === tier.key ? (
                        <Loader2 className="h-4 w-4 animate-spin mr-1" />
                      ) : null}
                      {isUpgrade ? "Upgrade" : "Downgrade"}
                    </Button>
                  )}
                </CardContent>
              </Card>
            )
          })}
        </div>
      </div>
    </div>
  )
}
