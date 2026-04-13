"""
Integration config service — read/write per-agency encrypted credentials.

Public API:
    list_providers()                 → static catalogue of known integrations
    get_config(db, agency_id, prov)  → dict of decrypted values for a provider
    set_config(db, agency_id, ...)   → upsert encrypted values
    verify_config(db, agency_id, p)  → call the provider's verify() function
    mask_for_display(dict)           → return a display-safe dict with masked secrets

The provider registry is the single source of truth for every integration
the app knows about — config screens use it to render forms, routers use
it to validate incoming payloads, and the background tasks use it to know
which integrations are live per agency.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable, Optional

from sqlalchemy.orm import Session

from app.models import IntegrationConfig
from app.services.secrets import decrypt, encrypt, mask

logger = logging.getLogger(__name__)


# ─── Provider catalogue ─────────────────────────────────────────────────


@dataclass
class ConfigField:
    key: str
    label: str
    type: str                # "string", "password", "textarea", "select", "boolean"
    is_secret: bool = False
    required: bool = True
    placeholder: str = ""
    help_text: str = ""
    options: list[str] = field(default_factory=list)  # for type="select"


@dataclass
class ProviderSpec:
    key: str                 # stable identifier, e.g. "google_oauth"
    label: str               # human-readable name for the UI
    category: str            # "auth", "banking", "filing", "storage", "email", "ai", "pms", "whatsapp"
    description: str
    docs_url: str = ""
    fields: list[ConfigField] = field(default_factory=list)
    verify: Optional[Callable] = None  # optional liveness check


# ── Known providers ─────────────────────────────────────────────────────

PROVIDERS: dict[str, ProviderSpec] = {
    # ── Auth ─────────────────────────────────────────────────────
    "google_oauth": ProviderSpec(
        key="google_oauth",
        label="Google Workspace (OAuth)",
        category="auth",
        description=(
            "Let users sign in with their Google Workspace account. "
            "Register an OAuth client in Google Cloud Console with "
            "redirect URI https://<your-domain>/api/v1/auth/google/callback"
        ),
        docs_url="https://console.cloud.google.com/apis/credentials",
        fields=[
            ConfigField("client_id", "Client ID", "string", is_secret=False),
            ConfigField("client_secret", "Client secret", "password", is_secret=True),
        ],
    ),
    "microsoft_oauth": ProviderSpec(
        key="microsoft_oauth",
        label="Microsoft 365 (OAuth)",
        category="auth",
        description=(
            "Let users sign in with their Microsoft 365 or Azure AD account. "
            "Register an app in Entra ID (Azure portal) with redirect URI "
            "https://<your-domain>/api/v1/auth/microsoft/callback"
        ),
        docs_url="https://portal.azure.com",
        fields=[
            ConfigField("client_id", "Application (client) ID", "string", is_secret=False),
            ConfigField("client_secret", "Client secret", "password", is_secret=True),
            ConfigField(
                "tenant", "Tenant",
                "string", is_secret=False, required=False,
                placeholder="common",
                help_text="'common' allows any Microsoft account. Use your tenant GUID to restrict.",
            ),
        ],
    ),

    # ── Banking ──────────────────────────────────────────────────
    "aiia": ProviderSpec(
        key="aiia",
        label="Aiia (Nordic open banking)",
        category="banking",
        description=(
            "Nordic open banking aggregator covering Norway (DNB, "
            "Sparebank1, Nordea NO), Sweden (SEB, Handelsbanken, "
            "Swedbank), and Finland (OP, Nordea FI). Single integration."
        ),
        docs_url="https://aiia.eu/",
        fields=[
            ConfigField("client_id", "Client ID", "string", is_secret=False),
            ConfigField("client_secret", "Client secret", "password", is_secret=True),
            ConfigField(
                "environment", "Environment", "select",
                is_secret=False, required=True,
                options=["sandbox", "production"],
            ),
        ],
    ),
    "tink": ProviderSpec(
        key="tink",
        label="Tink (banking fallback)",
        category="banking",
        description="Alternative Nordic open banking provider. Sweden primary coverage.",
        docs_url="https://console.tink.com/",
        fields=[
            ConfigField("client_id", "Client ID", "string", is_secret=False),
            ConfigField("client_secret", "Client secret", "password", is_secret=True),
        ],
    ),

    # ── Identity / e-signing ─────────────────────────────────────
    "bankid_no": ProviderSpec(
        key="bankid_no",
        label="BankID (Norway)",
        category="identity",
        description="Norwegian BankID for document signing and strong authentication.",
        docs_url="https://www.bankid.no/en/corporate/",
        fields=[
            ConfigField("merchant_name", "Merchant name", "string", is_secret=False),
            ConfigField("client_certificate", "Client certificate (PEM)", "textarea", is_secret=True),
            ConfigField("client_key", "Client private key (PEM)", "textarea", is_secret=True),
        ],
    ),
    "bankid_se": ProviderSpec(
        key="bankid_se",
        label="BankID (Sweden)",
        category="identity",
        description="Swedish BankID for identity verification and e-signing.",
        docs_url="https://www.bankid.com/en/foretag",
        fields=[
            ConfigField("rp_certificate", "RP certificate (.p12, base64)", "textarea", is_secret=True),
            ConfigField("rp_passphrase", "Certificate passphrase", "password", is_secret=True),
            ConfigField(
                "environment", "Environment", "select",
                is_secret=False, options=["test", "production"],
            ),
        ],
    ),
    "ftn_fi": ProviderSpec(
        key="ftn_fi",
        label="Finnish Trust Network",
        category="identity",
        description="Finnish Trust Network (FTN) for strong electronic identification.",
        docs_url="https://www.kyberturvallisuuskeskus.fi/en/our-services/finnish-trust-network",
        fields=[
            ConfigField("client_id", "Client ID", "string", is_secret=False),
            ConfigField("client_secret", "Client secret", "password", is_secret=True),
        ],
    ),

    # ── File storage ─────────────────────────────────────────────
    "do_spaces": ProviderSpec(
        key="do_spaces",
        label="DigitalOcean Spaces",
        category="storage",
        description="S3-compatible object storage for document uploads.",
        docs_url="https://docs.digitalocean.com/products/spaces/",
        fields=[
            ConfigField("endpoint", "Endpoint URL", "string", is_secret=False,
                        placeholder="https://cap-1.digitaloceanspaces.com"),
            ConfigField("region", "Region", "string", is_secret=False,
                        placeholder="cap-1"),
            ConfigField("bucket", "Bucket name", "string", is_secret=False,
                        placeholder="claud-erp-files"),
            ConfigField("access_key", "Access key", "password", is_secret=True),
            ConfigField("secret_key", "Secret key", "password", is_secret=True),
        ],
    ),

    # ── Email ────────────────────────────────────────────────────
    "resend": ProviderSpec(
        key="resend",
        label="Resend (email delivery)",
        category="email",
        description="Transactional email delivery for invoices, payslips, and reports.",
        docs_url="https://resend.com/docs",
        fields=[
            ConfigField("api_key", "API key", "password", is_secret=True),
            ConfigField("from_email", "Sender address", "string", is_secret=False,
                        placeholder="no-reply@your-domain.com"),
            ConfigField("from_name", "Sender name", "string", is_secret=False, required=False,
                        placeholder="ClaudERP"),
        ],
    ),

    # ── Messaging ────────────────────────────────────────────────
    "openclaw_whatsapp": ProviderSpec(
        key="openclaw_whatsapp",
        label="OpenClaw WhatsApp (via Twilio)",
        category="whatsapp",
        description="WhatsApp client communications, document intake, and AI chat.",
        docs_url="https://www.openclaw.ai/",
        fields=[
            ConfigField("twilio_account_sid", "Twilio Account SID", "string", is_secret=False),
            ConfigField("twilio_auth_token", "Twilio Auth Token", "password", is_secret=True),
            ConfigField("whatsapp_number", "WhatsApp business number", "string", is_secret=False,
                        placeholder="+4712345678"),
        ],
    ),

    # ── AI ───────────────────────────────────────────────────────
    "claude": ProviderSpec(
        key="claude",
        label="Claude API (Anthropic)",
        category="ai",
        description="Claude API key for AI features (GL coding, narratives, chat).",
        docs_url="https://console.anthropic.com/",
        fields=[
            ConfigField("api_key", "API key", "password", is_secret=True,
                        placeholder="sk-ant-..."),
        ],
    ),

    # ── Tax authorities ──────────────────────────────────────────
    "altinn": ProviderSpec(
        key="altinn",
        label="Altinn (Norway)",
        category="filing",
        description="Norwegian government filing (VAT, A-melding, RF-forms).",
        docs_url="https://www.altinn.no/en/",
        fields=[
            ConfigField("virksomhetssertifikat", "Enterprise certificate (.p12, base64)", "textarea", is_secret=True),
            ConfigField("certificate_passphrase", "Certificate passphrase", "password", is_secret=True),
            ConfigField(
                "environment", "Environment", "select",
                is_secret=False, options=["tt02", "production"],
            ),
        ],
    ),
    "skatteverket": ProviderSpec(
        key="skatteverket",
        label="Skatteverket (Sweden)",
        category="filing",
        description="Swedish tax authority (moms, AGD, KU, inkomstdeklaration).",
        docs_url="https://www.skatteverket.se/",
        fields=[
            ConfigField("organisation_number", "Organisation number", "string", is_secret=False),
            ConfigField("signing_certificate", "Signing certificate (.p12, base64)", "textarea", is_secret=True),
            ConfigField("certificate_passphrase", "Passphrase", "password", is_secret=True),
        ],
    ),
    "omavero": ProviderSpec(
        key="omavero",
        label="OmaVero / Vero (Finland)",
        category="filing",
        description="Finnish tax portal for VAT and corporate tax returns.",
        docs_url="https://www.vero.fi/en/",
        fields=[
            ConfigField("api_token", "API token", "password", is_secret=True),
            ConfigField("business_id", "Y-tunnus", "string", is_secret=False),
        ],
    ),
    "tulorekisteri": ProviderSpec(
        key="tulorekisteri",
        label="Tulorekisteri (Finland — Incomes Register)",
        category="filing",
        description=(
            "REAL-TIME payroll reporting. Every salary payment must be "
            "reported within 5 calendar days. NOT a batch job."
        ),
        docs_url="https://www.vero.fi/en/incomes-register/",
        fields=[
            ConfigField("api_client_id", "API client ID", "string", is_secret=False),
            ConfigField("api_client_secret", "API client secret", "password", is_secret=True),
            ConfigField("business_id", "Y-tunnus", "string", is_secret=False),
        ],
    ),

    # ── Hospitality PMS ──────────────────────────────────────────
    "mews": ProviderSpec(
        key="mews",
        label="Mews PMS",
        category="pms",
        description="Mews hotel property management system — daily revenue import.",
        docs_url="https://mews-systems.gitbook.io/connector-api/",
        fields=[
            ConfigField("client_token", "Client token", "password", is_secret=True),
            ConfigField("access_token", "Access token", "password", is_secret=True),
        ],
    ),
    "opera_cloud": ProviderSpec(
        key="opera_cloud",
        label="Opera Cloud (Oracle)",
        category="pms",
        description="Oracle Opera Cloud PMS integration.",
        docs_url="https://docs.oracle.com/cd/F27986_01/",
        fields=[
            ConfigField("api_key", "API key", "password", is_secret=True),
            ConfigField("api_secret", "API secret", "password", is_secret=True),
            ConfigField("hotel_id", "Hotel ID", "string", is_secret=False),
        ],
    ),
    "apaleo": ProviderSpec(
        key="apaleo",
        label="Apaleo PMS",
        category="pms",
        description="Apaleo cloud-native PMS integration.",
        docs_url="https://apaleo.dev/",
        fields=[
            ConfigField("client_id", "Client ID", "string", is_secret=False),
            ConfigField("client_secret", "Client secret", "password", is_secret=True),
        ],
    ),
}


def list_providers() -> list[ProviderSpec]:
    """Return all registered providers, sorted by category then label."""
    return sorted(
        PROVIDERS.values(),
        key=lambda p: (p.category, p.label),
    )


def get_provider(key: str) -> ProviderSpec:
    if key not in PROVIDERS:
        raise ValueError(
            f"Unknown integration provider: {key}. "
            f"Known: {sorted(PROVIDERS.keys())}"
        )
    return PROVIDERS[key]


# ─── Read / write ────────────────────────────────────────────────────


def get_config(
    db: Session,
    agency_id: int,
    provider: str,
    *,
    decrypt_values: bool = True,
) -> dict[str, str]:
    """
    Return all keys for a given provider as a dict.
    Defaults to decrypted values. Pass decrypt_values=False to get the
    raw encrypted tokens (useful for auditing, never return to UI).
    """
    get_provider(provider)  # validates provider exists
    rows = (
        db.query(IntegrationConfig)
        .filter(
            IntegrationConfig.agency_id == agency_id,
            IntegrationConfig.provider == provider,
        )
        .all()
    )
    result: dict[str, str] = {}
    for row in rows:
        if decrypt_values:
            try:
                result[row.key] = decrypt(row.value_encrypted)
            except Exception:
                logger.exception(
                    "Failed to decrypt %s.%s for agency %s",
                    provider, row.key, agency_id,
                )
                result[row.key] = ""
        else:
            result[row.key] = row.value_encrypted
    return result


def set_config(
    db: Session,
    agency_id: int,
    provider: str,
    values: dict[str, str],
    user_id: Optional[int] = None,
) -> None:
    """
    Upsert a batch of config values for one (agency, provider) pair.

    `values` is a plaintext dict like {"client_id": "...", "client_secret": "..."}.
    Empty-string values are treated as "leave unchanged" (useful for
    the UI so users can save a form without re-entering secrets they
    can't see).
    """
    spec = get_provider(provider)
    known_keys = {f.key: f for f in spec.fields}

    # Validate incoming keys against the provider spec
    unknown = set(values.keys()) - set(known_keys.keys())
    if unknown:
        raise ValueError(
            f"Unknown config keys for {provider}: {sorted(unknown)}. "
            f"Expected any of: {sorted(known_keys.keys())}"
        )

    for key, plaintext in values.items():
        # Empty string means "don't change" (UI-friendly for secrets)
        if plaintext == "":
            continue
        field = known_keys[key]
        existing = (
            db.query(IntegrationConfig)
            .filter(
                IntegrationConfig.agency_id == agency_id,
                IntegrationConfig.provider == provider,
                IntegrationConfig.key == key,
            )
            .first()
        )
        encrypted = encrypt(plaintext)
        if existing:
            existing.value_encrypted = encrypted
            existing.is_secret = field.is_secret
            existing.updated_by = user_id
        else:
            db.add(
                IntegrationConfig(
                    agency_id=agency_id,
                    provider=provider,
                    key=key,
                    value_encrypted=encrypted,
                    is_secret=field.is_secret,
                    updated_by=user_id,
                )
            )
    db.commit()


def delete_config(
    db: Session,
    agency_id: int,
    provider: str,
) -> int:
    """Delete every row for a provider. Returns count deleted."""
    get_provider(provider)
    deleted = (
        db.query(IntegrationConfig)
        .filter(
            IntegrationConfig.agency_id == agency_id,
            IntegrationConfig.provider == provider,
        )
        .delete()
    )
    db.commit()
    return deleted


def mask_for_display(provider: str, plaintext: dict[str, str]) -> dict[str, str]:
    """
    Return a display-safe copy of a config dict — secret fields masked,
    public fields shown in clear.
    """
    spec = get_provider(provider)
    result: dict[str, str] = {}
    for field in spec.fields:
        raw = plaintext.get(field.key, "")
        if not raw:
            result[field.key] = ""
        elif field.is_secret:
            result[field.key] = mask(raw)
        else:
            result[field.key] = raw
    return result


def mark_verified(
    db: Session,
    agency_id: int,
    provider: str,
    error: Optional[str] = None,
) -> None:
    """Stamp last_verified_at + last_verification_error on every row."""
    now = datetime.now(timezone.utc)
    rows = (
        db.query(IntegrationConfig)
        .filter(
            IntegrationConfig.agency_id == agency_id,
            IntegrationConfig.provider == provider,
        )
        .all()
    )
    for row in rows:
        if error is None:
            row.last_verified_at = now
            row.last_verification_error = None
        else:
            row.last_verification_error = error
    db.commit()
