"""TOTP-based Multi-Factor Authentication helpers.

Uses the ``pyotp`` library to generate secrets, provisioning URIs, and
verify one-time codes.
"""

import pyotp


def generate_totp_secret() -> str:
    """Generate a new base32-encoded TOTP secret."""
    return pyotp.random_base32()


def get_provisioning_uri(secret: str, email: str, issuer: str = "BPO Nexus") -> str:
    """Return an ``otpauth://`` URI suitable for QR-code scanning."""
    totp = pyotp.TOTP(secret)
    return totp.provisioning_uri(name=email, issuer_name=issuer)


def verify_totp(secret: str, code: str) -> bool:
    """Verify a TOTP code against the given secret.

    Allows a 1-step window (30 s) to account for clock skew.
    """
    totp = pyotp.TOTP(secret)
    return totp.verify(code, valid_window=1)
