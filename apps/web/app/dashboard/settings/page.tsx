"use client"

import { useState, useEffect } from "react"
import {
  Building2,
  User,
  Bell,
  Shield,
  CreditCard,
  Globe,
  Palette,
  Link2,
  ChevronRight,
  Check,
} from "lucide-react"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Select } from "@/components/ui/select"
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { useToast } from "@/components/ui/toast"

const SECTIONS = [
  { id: "agency", label: "Agency", icon: Building2 },
  { id: "profile", label: "Profile", icon: User },
  { id: "notifications", label: "Notifications", icon: Bell },
  { id: "security", label: "Security", icon: Shield },
  { id: "billing", label: "Billing", icon: CreditCard },
  { id: "integrations", label: "Integrations", icon: Link2 },
  { id: "appearance", label: "Appearance", icon: Palette },
]

const INTEGRATIONS = [
  { name: "TrueLayer", description: "Open Banking (UK/EU)", connected: false },
  { name: "Auth0", description: "SSO & MFA authentication", connected: true },
  { name: "Claude AI", description: "AI document processing", connected: true },
  { name: "WhatsApp", description: "Client communications", connected: false },
  { name: "Resend", description: "Transactional email", connected: true },
]

export default function SettingsPage() {
  const [activeSection, setActiveSection] = useState("agency")
  const { toast } = useToast()

  const [agencyForm, setAgencyForm] = useState({
    name: "BPO Nexus Demo",
    slug: "bpo-nexus-demo",
    country: "ZA",
    timezone: "Africa/Johannesburg",
  })

  const [profileForm, setProfileForm] = useState({
    name: "",
    email: "",
    role: "admin",
  })

  useEffect(() => {
    try {
      const user = JSON.parse(localStorage.getItem("bpo_user") || "{}")
      setProfileForm({
        name: user.email?.split("@")[0] || "",
        email: user.email || "",
        role: user.role || "admin",
      })
    } catch {}
  }, [])

  const [notifications, setNotifications] = useState({
    email_invoices: true,
    email_reports: true,
    email_anomalies: true,
    push_payments: false,
    push_documents: true,
  })

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold">Settings</h1>
        <p className="text-sm text-muted-foreground mt-0.5">
          Manage your agency configuration
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Settings Nav */}
        <nav className="lg:col-span-1 space-y-0.5">
          {SECTIONS.map((section) => (
            <button
              key={section.id}
              onClick={() => setActiveSection(section.id)}
              className={cn(
                "flex items-center gap-2.5 w-full px-3 py-2 rounded-md text-sm font-medium transition-colors text-left",
                activeSection === section.id
                  ? "bg-primary/10 text-primary"
                  : "text-muted-foreground hover:text-foreground hover:bg-accent"
              )}
            >
              <section.icon className="h-4 w-4" />
              {section.label}
            </button>
          ))}
        </nav>

        {/* Content */}
        <div className="lg:col-span-3 space-y-6">
          {/* Agency Settings */}
          {activeSection === "agency" && (
            <Card>
              <CardHeader>
                <CardTitle>Agency Details</CardTitle>
                <CardDescription>
                  Update your organization information
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <Input
                    label="Agency Name"
                    value={agencyForm.name}
                    onChange={(e) =>
                      setAgencyForm({ ...agencyForm, name: e.target.value })
                    }
                  />
                  <Input
                    label="Slug"
                    value={agencyForm.slug}
                    onChange={(e) =>
                      setAgencyForm({ ...agencyForm, slug: e.target.value })
                    }
                    hint="Used in URLs and portal links"
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <Select
                    label="Country"
                    value={agencyForm.country}
                    onChange={(e) =>
                      setAgencyForm({ ...agencyForm, country: e.target.value })
                    }
                    options={[
                      { value: "ZA", label: "South Africa" },
                      { value: "NO", label: "Norway" },
                      { value: "UK", label: "United Kingdom" },
                    ]}
                  />
                  <Select
                    label="Timezone"
                    value={agencyForm.timezone}
                    onChange={(e) =>
                      setAgencyForm({
                        ...agencyForm,
                        timezone: e.target.value,
                      })
                    }
                    options={[
                      {
                        value: "Africa/Johannesburg",
                        label: "Africa/Johannesburg (SAST)",
                      },
                      { value: "Europe/Oslo", label: "Europe/Oslo (CET)" },
                      { value: "Europe/London", label: "Europe/London (GMT)" },
                    ]}
                  />
                </div>
                <div className="flex justify-end pt-2">
                  <Button
                    onClick={() => toast("Agency settings saved")}
                    size="sm"
                  >
                    Save Changes
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Profile */}
          {activeSection === "profile" && (
            <Card>
              <CardHeader>
                <CardTitle>Your Profile</CardTitle>
                <CardDescription>
                  Manage your personal account settings
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <Input
                    label="Display Name"
                    value={profileForm.name}
                    onChange={(e) =>
                      setProfileForm({ ...profileForm, name: e.target.value })
                    }
                  />
                  <Input
                    label="Email"
                    type="email"
                    value={profileForm.email}
                    onChange={(e) =>
                      setProfileForm({ ...profileForm, email: e.target.value })
                    }
                  />
                </div>
                <Input
                  label="Role"
                  value={profileForm.role}
                  disabled
                  hint="Contact an admin to change your role"
                />
                <div className="flex justify-end pt-2">
                  <Button
                    onClick={() => toast("Profile updated")}
                    size="sm"
                  >
                    Save Changes
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Notifications */}
          {activeSection === "notifications" && (
            <Card>
              <CardHeader>
                <CardTitle>Notification Preferences</CardTitle>
                <CardDescription>
                  Choose what you get notified about
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-1">
                {[
                  {
                    key: "email_invoices",
                    label: "Invoice updates",
                    desc: "When invoices are paid or overdue",
                  },
                  {
                    key: "email_reports",
                    label: "Report ready",
                    desc: "When monthly reports are generated",
                  },
                  {
                    key: "email_anomalies",
                    label: "Anomaly alerts",
                    desc: "AI-detected unusual transactions",
                  },
                  {
                    key: "push_payments",
                    label: "Payment received",
                    desc: "Real-time payment notifications",
                  },
                  {
                    key: "push_documents",
                    label: "Document processed",
                    desc: "When AI finishes extracting data",
                  },
                ].map((item) => (
                  <label
                    key={item.key}
                    className="flex items-center justify-between px-3 py-3 rounded-md hover:bg-accent/50 transition-colors cursor-pointer"
                  >
                    <div>
                      <p className="text-sm font-medium">{item.label}</p>
                      <p className="text-xs text-muted-foreground">
                        {item.desc}
                      </p>
                    </div>
                    <button
                      onClick={() =>
                        setNotifications({
                          ...notifications,
                          [item.key]:
                            !notifications[
                              item.key as keyof typeof notifications
                            ],
                        })
                      }
                      className={cn(
                        "relative w-9 h-5 rounded-full transition-colors",
                        notifications[item.key as keyof typeof notifications]
                          ? "bg-primary"
                          : "bg-muted"
                      )}
                    >
                      <div
                        className={cn(
                          "absolute top-0.5 w-4 h-4 rounded-full bg-white shadow transition-transform",
                          notifications[item.key as keyof typeof notifications]
                            ? "translate-x-4"
                            : "translate-x-0.5"
                        )}
                      />
                    </button>
                  </label>
                ))}
              </CardContent>
            </Card>
          )}

          {/* Security */}
          {activeSection === "security" && (
            <Card>
              <CardHeader>
                <CardTitle>Security</CardTitle>
                <CardDescription>
                  Manage authentication and access controls
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between p-4 rounded-lg border">
                  <div>
                    <p className="text-sm font-medium">Two-factor authentication</p>
                    <p className="text-xs text-muted-foreground">
                      Add an extra layer of security to your account
                    </p>
                  </div>
                  <Button variant="outline" size="sm">
                    Enable
                  </Button>
                </div>
                <div className="flex items-center justify-between p-4 rounded-lg border">
                  <div>
                    <p className="text-sm font-medium">Change password</p>
                    <p className="text-xs text-muted-foreground">
                      Update your account password
                    </p>
                  </div>
                  <Button variant="outline" size="sm">
                    Update
                  </Button>
                </div>
                <div className="flex items-center justify-between p-4 rounded-lg border">
                  <div>
                    <p className="text-sm font-medium">Active sessions</p>
                    <p className="text-xs text-muted-foreground">
                      1 active session on this device
                    </p>
                  </div>
                  <Badge variant="success">Current</Badge>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Billing */}
          {activeSection === "billing" && (
            <Card>
              <CardHeader>
                <CardTitle>Billing & Plan</CardTitle>
                <CardDescription>
                  Manage your subscription and payment methods
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between p-4 rounded-lg border border-primary/20 bg-primary/5">
                  <div>
                    <p className="text-sm font-medium">Growth Plan</p>
                    <p className="text-xs text-muted-foreground">
                      Up to 50 clients, AI features, bank integrations
                    </p>
                  </div>
                  <Badge>Active</Badge>
                </div>
                <div className="flex items-center justify-between p-4 rounded-lg border">
                  <div>
                    <p className="text-sm font-medium">Payment method</p>
                    <p className="text-xs text-muted-foreground">
                      Visa ending in 4242
                    </p>
                  </div>
                  <Button variant="outline" size="sm">
                    Update
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Integrations */}
          {activeSection === "integrations" && (
            <Card>
              <CardHeader>
                <CardTitle>Integrations</CardTitle>
                <CardDescription>
                  Connect external services and APIs
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-1">
                {INTEGRATIONS.map((int) => (
                  <div
                    key={int.name}
                    className="flex items-center justify-between px-3 py-3 rounded-md hover:bg-accent/50 transition-colors"
                  >
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-md bg-muted flex items-center justify-center">
                        <Link2 className="h-4 w-4 text-muted-foreground" />
                      </div>
                      <div>
                        <p className="text-sm font-medium">{int.name}</p>
                        <p className="text-xs text-muted-foreground">
                          {int.description}
                        </p>
                      </div>
                    </div>
                    {int.connected ? (
                      <Badge variant="success">
                        <Check className="h-3 w-3 mr-1" />
                        Connected
                      </Badge>
                    ) : (
                      <Button variant="outline" size="sm">
                        Connect
                      </Button>
                    )}
                  </div>
                ))}
              </CardContent>
            </Card>
          )}

          {/* Appearance */}
          {activeSection === "appearance" && (
            <Card>
              <CardHeader>
                <CardTitle>Appearance</CardTitle>
                <CardDescription>
                  Customize the look and feel
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <label className="text-sm font-medium mb-3 block">
                    Theme
                  </label>
                  <div className="flex gap-3">
                    {[
                      { value: "light", label: "Light" },
                      { value: "dark", label: "Dark" },
                      { value: "system", label: "System" },
                    ].map((theme) => (
                      <button
                        key={theme.value}
                        className={cn(
                          "flex-1 p-3 rounded-lg border text-center text-sm font-medium transition-colors",
                          theme.value === "light"
                            ? "border-primary bg-primary/5 text-primary"
                            : "hover:bg-accent"
                        )}
                      >
                        {theme.label}
                      </button>
                    ))}
                  </div>
                </div>
                <Select
                  label="Density"
                  value="comfortable"
                  onChange={() => {}}
                  options={[
                    { value: "compact", label: "Compact" },
                    { value: "comfortable", label: "Comfortable" },
                    { value: "spacious", label: "Spacious" },
                  ]}
                />
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  )
}
