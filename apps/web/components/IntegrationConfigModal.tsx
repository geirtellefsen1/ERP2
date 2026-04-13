"use client"

import * as React from "react"
import { Loader2, CheckCircle2, AlertCircle, ExternalLink } from "lucide-react"
import {
  Modal,
  ModalHeader,
  ModalTitle,
  ModalDescription,
  ModalContent,
  ModalFooter,
} from "@/components/ui/modal"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Select } from "@/components/ui/select"
import { Badge } from "@/components/ui/badge"
import { apiGet, apiPut, apiPost } from "@/lib/api"

/**
 * Modal for editing one integration provider's configuration.
 *
 * Renders a form dynamically from the provider's field spec. Secret
 * fields display an "unchanged" placeholder when a value is already
 * stored — submitting empty keeps the existing secret so users don't
 * have to re-enter credentials on every edit.
 *
 * Save → PUT /api/v1/integrations/{provider}
 * Test → POST /api/v1/integrations/{provider}/verify
 */

export interface ProviderField {
  key: string
  label: string
  type: "string" | "password" | "textarea" | "select" | "boolean"
  is_secret: boolean
  required: boolean
  placeholder: string
  help_text: string
  options: string[]
}

export interface ProviderSchema {
  key: string
  label: string
  category: string
  description: string
  docs_url: string
  fields: ProviderField[]
}

interface ProviderConfigResponse {
  provider: string
  values: Record<string, string>
  last_verified_at: string | null
  last_verification_error: string | null
  is_configured: boolean
}

interface Props {
  open: boolean
  provider: ProviderSchema | null
  onClose: () => void
  onSaved?: () => void
}

export function IntegrationConfigModal({
  open,
  provider,
  onClose,
  onSaved,
}: Props) {
  const [loading, setLoading] = React.useState(false)
  const [saving, setSaving] = React.useState(false)
  const [testing, setTesting] = React.useState(false)
  const [existing, setExisting] = React.useState<ProviderConfigResponse | null>(
    null
  )
  const [form, setForm] = React.useState<Record<string, string>>({})
  const [testResult, setTestResult] = React.useState<
    { ok: boolean; message: string } | null
  >(null)
  const [error, setError] = React.useState<string | null>(null)

  // Load the current config when the modal opens for a new provider
  React.useEffect(() => {
    if (!open || !provider) return
    setLoading(true)
    setError(null)
    setTestResult(null)
    setForm({})
    setExisting(null)
    apiGet<ProviderConfigResponse>(`/api/v1/integrations/${provider.key}`)
      .then((data) => {
        setExisting(data)
        // Pre-populate non-secret fields; keep secret fields blank so
        // users see the "unchanged" placeholder.
        const seed: Record<string, string> = {}
        for (const f of provider.fields) {
          if (!f.is_secret) {
            seed[f.key] = data.values[f.key] || ""
          } else {
            seed[f.key] = ""
          }
        }
        setForm(seed)
      })
      .catch((e) => setError(e.message || "Failed to load config"))
      .finally(() => setLoading(false))
  }, [open, provider])

  if (!provider) return null

  const handleSave = async () => {
    setSaving(true)
    setError(null)
    setTestResult(null)
    try {
      // Submit only the fields the user actually touched. Empty string
      // on a secret field = "don't change" per the API contract.
      await apiPut(`/api/v1/integrations/${provider.key}`, { values: form })
      onSaved?.()
      onClose()
    } catch (e: any) {
      setError(e.message || "Save failed")
    } finally {
      setSaving(false)
    }
  }

  const handleTest = async () => {
    setTesting(true)
    setTestResult(null)
    try {
      // Save first so /verify sees the values the user just typed.
      await apiPut(`/api/v1/integrations/${provider.key}`, { values: form })
      const res = await apiPost<{ ok: boolean; message: string }>(
        `/api/v1/integrations/${provider.key}/verify`,
        {}
      )
      setTestResult(res)
    } catch (e: any) {
      setTestResult({
        ok: false,
        message: e.message || "Test failed",
      })
    } finally {
      setTesting(false)
    }
  }

  return (
    <Modal open={open} onClose={onClose} className="max-w-xl">
      <ModalHeader onClose={onClose}>
        <ModalTitle>{provider.label}</ModalTitle>
        <ModalDescription>{provider.description}</ModalDescription>
      </ModalHeader>

      <ModalContent className="space-y-4">
        {loading ? (
          <div className="flex items-center justify-center py-12 text-muted-foreground">
            <Loader2 className="h-5 w-5 animate-spin mr-2" />
            Loading configuration…
          </div>
        ) : (
          <>
            {existing && (
              <div className="flex items-center justify-between text-xs text-muted-foreground border rounded-md px-3 py-2">
                <span>
                  {existing.is_configured ? (
                    <>
                      <Badge variant="success">Configured</Badge>
                      {existing.last_verified_at && (
                        <span className="ml-2">
                          Last verified{" "}
                          {new Date(
                            existing.last_verified_at
                          ).toLocaleString()}
                        </span>
                      )}
                    </>
                  ) : (
                    <Badge>Not configured</Badge>
                  )}
                </span>
                {provider.docs_url && (
                  <a
                    href={provider.docs_url}
                    target="_blank"
                    rel="noreferrer noopener"
                    className="flex items-center gap-1 text-primary hover:underline"
                  >
                    Docs <ExternalLink className="h-3 w-3" />
                  </a>
                )}
              </div>
            )}

            {provider.fields.map((f) => (
              <FieldInput
                key={f.key}
                field={f}
                value={form[f.key] || ""}
                hasStoredSecret={
                  f.is_secret && !!existing?.values?.[f.key]
                }
                onChange={(v) => setForm({ ...form, [f.key]: v })}
              />
            ))}

            {error && (
              <div className="flex items-start gap-2 text-sm text-destructive border border-destructive/30 bg-destructive/5 rounded-md px-3 py-2">
                <AlertCircle className="h-4 w-4 mt-0.5 flex-none" />
                <span>{error}</span>
              </div>
            )}

            {testResult && (
              <div
                className={`flex items-start gap-2 text-sm border rounded-md px-3 py-2 ${
                  testResult.ok
                    ? "border-emerald-500/30 bg-emerald-500/5 text-emerald-700"
                    : "border-destructive/30 bg-destructive/5 text-destructive"
                }`}
              >
                {testResult.ok ? (
                  <CheckCircle2 className="h-4 w-4 mt-0.5 flex-none" />
                ) : (
                  <AlertCircle className="h-4 w-4 mt-0.5 flex-none" />
                )}
                <span>{testResult.message}</span>
              </div>
            )}
          </>
        )}
      </ModalContent>

      <ModalFooter>
        <Button
          variant="outline"
          size="sm"
          onClick={handleTest}
          disabled={saving || testing || loading}
        >
          {testing ? (
            <>
              <Loader2 className="h-3 w-3 mr-1 animate-spin" />
              Testing…
            </>
          ) : (
            "Test connection"
          )}
        </Button>
        <Button size="sm" onClick={handleSave} disabled={saving || loading}>
          {saving ? (
            <>
              <Loader2 className="h-3 w-3 mr-1 animate-spin" />
              Saving…
            </>
          ) : (
            "Save"
          )}
        </Button>
      </ModalFooter>
    </Modal>
  )
}


// ── Field input widget ─────────────────────────────────────────────

interface FieldInputProps {
  field: ProviderField
  value: string
  hasStoredSecret: boolean
  onChange: (value: string) => void
}

function FieldInput({ field, value, hasStoredSecret, onChange }: FieldInputProps) {
  if (field.type === "select") {
    return (
      <div className="space-y-1">
        <Select
          label={field.label + (field.required ? " *" : "")}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          options={field.options.map((o) => ({ value: o, label: o }))}
        />
        {field.help_text && (
          <p className="text-xs text-muted-foreground">{field.help_text}</p>
        )}
      </div>
    )
  }
  if (field.type === "textarea") {
    return (
      <div className="space-y-1">
        <label className="text-sm font-medium">
          {field.label}
          {field.required && " *"}
        </label>
        <textarea
          className="w-full rounded-md border bg-background px-3 py-2 text-sm min-h-[80px]"
          value={value}
          placeholder={field.placeholder}
          onChange={(e) => onChange(e.target.value)}
        />
        {field.help_text && (
          <p className="text-xs text-muted-foreground">{field.help_text}</p>
        )}
      </div>
    )
  }
  if (field.type === "boolean") {
    return (
      <label className="flex items-center gap-2 text-sm">
        <input
          type="checkbox"
          checked={value === "true"}
          onChange={(e) => onChange(e.target.checked ? "true" : "false")}
        />
        <span>
          {field.label}
          {field.required && " *"}
        </span>
      </label>
    )
  }

  return (
    <Input
      label={field.label + (field.required ? " *" : "")}
      type={field.type === "password" ? "password" : "text"}
      value={value}
      placeholder={
        hasStoredSecret ? "••••••  (leave blank to keep current)" : field.placeholder
      }
      onChange={(e) => onChange(e.target.value)}
      hint={field.help_text || undefined}
    />
  )
}
