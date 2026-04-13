"""
Factory for country-specific submitters.

Returns a MockSubmitter in "mock" mode (always safe, no network) or a
LiveSubmitter in "live" mode once the real credentials and endpoints
are in place. LiveSubmitter is NOT implemented yet — it's a TODO that
intentionally raises so we can't accidentally ship without knowing.
"""
from __future__ import annotations

from typing import Literal

from .base import StatutorySubmitter, SubmitterError
from .mock import MockSubmitter


Mode = Literal["mock", "live"]


def get_submitter(country_code: str, mode: Mode = "mock") -> StatutorySubmitter:
    """
    Return a submitter for the given country in the given mode.

    Args:
        country_code: "NO", "SE", or "FI"
        mode: "mock" (default) or "live"

    Raises:
        SubmitterError if mode="live" — live submission is not yet
        implemented because it requires production credentials (Altinn
        enterprise certificate, BankID, Katso ID) that aren't available
        in this environment.
    """
    cc = country_code.upper()
    if cc not in ("NO", "SE", "FI"):
        raise SubmitterError(f"No submitter available for {country_code}")

    if mode == "mock":
        return MockSubmitter()

    if mode == "live":
        raise SubmitterError(
            f"Live submitter for {cc} is not yet implemented. "
            f"Requires production credentials:\n"
            f"  NO: Altinn virksomhetssertifikat + API endpoint\n"
            f"  SE: BankID + Skatteverket e-service credentials\n"
            f"  FI: Katso ID / Suomi.fi certificate + Vero API token\n"
            f"Add these to the .env file and implement LiveSubmitter "
            f"in app/services/filing/live_{cc.lower()}.py before enabling."
        )

    raise SubmitterError(f"Unknown submitter mode: {mode}")
