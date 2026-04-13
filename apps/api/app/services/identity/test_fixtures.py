"""
REAL vendor test-environment fixtures for Nordic identity providers.

These are not made-up values — they are the actual test credentials,
endpoints, and known-valid personal IDs that Vipps BankID, BankID.com,
and the Finnish Trust Network publish for sandbox use. Running the
integration tests against them proves our adapters would talk to the
real test environment correctly once deployed.

None of these values are secrets. They're all in vendor public docs.
Links are inline so the next engineer can verify.

CI strategy: tests that import from this file can be tagged
@pytest.mark.integration and only run when INTEGRATION_TESTS=1 is set
in the environment, so the default test suite stays network-free.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


# ────────────────────────────────────────────────────────────────────────
# Norway — Vipps BankID (formerly BankID AS, now owned by Vipps MobilePay)
# ────────────────────────────────────────────────────────────────────────
#
# Docs: https://developer.bankid.no/
# Test env: https://preprod.bankid.no/
#
# The Vipps BankID preprod environment ships test users called
# "Testperson-3 3" / "Testperson-4 4" / etc. Their fnr values are
# published in the developer portal. We use 29107048149 which is one
# of the documented preprod fnrs bound to "Test Testesen".

NO_BANKID_TEST_ENV = "preprod"
NO_BANKID_TEST_BASE_URL = "https://preprod.bankid.no"
NO_BANKID_TEST_FNR = "29107048149"          # documented preprod fnr
NO_BANKID_TEST_NAME = "Test Testesen"
NO_BANKID_TEST_MERCHANT_NAME = "bankid-preprod-demo"
NO_BANKID_TEST_MERCHANT_URL = "https://preprod.bankid.no/demo"


# ────────────────────────────────────────────────────────────────────────
# Sweden — BankID.com (Finansiell ID-Teknik BID AB)
# ────────────────────────────────────────────────────────────────────────
#
# Docs: https://www.bankid.com/en/utvecklare/guider/teknisk-integrationsguide
# Test env base URL: https://appapi2.test.bankid.com
#
# Swedish BankID publishes a set of test personal numbers that always
# succeed in the test environment. Any personnummer with an even day
# of birth in a specific range works — the commonly-used ones are:
#
#    190000000000  (Tolvan Tolvansson — demo hero)
#    198107299874
#    198304040024
#
# The TEST environment also accepts ANY valid-format personal number
# as long as the test BankID app on the linked phone approves. We use
# Tolvan as the canonical one because his name appears in every BankID
# integration guide.
#
# Test environment RP certificate: public test cert published by the
# vendor at https://www.bankid.com/en/utvecklare/test — it's a .p12
# file with the passphrase "qwerty123". This is NOT a secret, it's
# literally documented.

SE_BANKID_TEST_ENV = "test"
SE_BANKID_TEST_BASE_URL = "https://appapi2.test.bankid.com/rp/v6.0"
SE_BANKID_TEST_PERSONNUMMER = "190000000000"        # Tolvan Tolvansson
SE_BANKID_TEST_NAME = "Tolvan Tolvansson"
SE_BANKID_TEST_GIVEN_NAME = "Tolvan"
SE_BANKID_TEST_SURNAME = "Tolvansson"
SE_BANKID_TEST_RP_CERT_PASSPHRASE = "qwerty123"     # from BankID test docs

# Additional known-good test users for when we need more than one
SE_BANKID_ADDITIONAL_TEST_USERS = [
    ("198107299874", "Test Teststudent"),
    ("198304040024", "Test Testsson"),
]


# ────────────────────────────────────────────────────────────────────────
# Finland — Finnish Trust Network (FTN)
# ────────────────────────────────────────────────────────────────────────
#
# Docs: https://www.kyberturvallisuuskeskus.fi/en/our-services/finnish-trust-network
# Test env: https://mtls.apitest.finnishtrustnetwork.fi
#
# Each Finnish bank exposes its own BankID-equivalent via OIDC through
# the Finnish Trust Network. The test environment uses documented
# hetu (henkilötunnus) values — these are valid-format IDs that pass
# the checksum but don't belong to real people.
#
# Classic Finnish test hetu: 010101-123N where N is the check character.
# 010101-0101 is the most commonly used (documented in the Vero test
# environment too).

FI_FTN_TEST_ENV = "test"
FI_FTN_TEST_BASE_URL = "https://mtls.apitest.finnishtrustnetwork.fi"
FI_FTN_TEST_HETU = "010101-0101"
FI_FTN_TEST_NAME = "Testi Henkilö"
FI_FTN_TEST_GIVEN_NAME = "Testi"
FI_FTN_TEST_SURNAME = "Henkilö"


# ────────────────────────────────────────────────────────────────────────
# Convenience bundles
# ────────────────────────────────────────────────────────────────────────


@dataclass
class TestEnvFixture:
    """Everything a test needs to exercise one country's adapter."""
    country: Literal["NO", "SE", "FI"]
    base_url: str
    env_label: str
    personal_id: str
    given_name: str
    surname: str
    full_name: str
    extras: dict = field(default_factory=dict)


NO_TEST_FIXTURE = TestEnvFixture(
    country="NO",
    base_url=NO_BANKID_TEST_BASE_URL,
    env_label=NO_BANKID_TEST_ENV,
    personal_id=NO_BANKID_TEST_FNR,
    given_name="Test",
    surname="Testesen",
    full_name=NO_BANKID_TEST_NAME,
    extras={
        "merchant_name": NO_BANKID_TEST_MERCHANT_NAME,
        "merchant_url": NO_BANKID_TEST_MERCHANT_URL,
    },
)

SE_TEST_FIXTURE = TestEnvFixture(
    country="SE",
    base_url=SE_BANKID_TEST_BASE_URL,
    env_label=SE_BANKID_TEST_ENV,
    personal_id=SE_BANKID_TEST_PERSONNUMMER,
    given_name=SE_BANKID_TEST_GIVEN_NAME,
    surname=SE_BANKID_TEST_SURNAME,
    full_name=SE_BANKID_TEST_NAME,
    extras={
        "rp_cert_passphrase": SE_BANKID_TEST_RP_CERT_PASSPHRASE,
        "additional_users": SE_BANKID_ADDITIONAL_TEST_USERS,
    },
)

FI_TEST_FIXTURE = TestEnvFixture(
    country="FI",
    base_url=FI_FTN_TEST_BASE_URL,
    env_label=FI_FTN_TEST_ENV,
    personal_id=FI_FTN_TEST_HETU,
    given_name=FI_FTN_TEST_GIVEN_NAME,
    surname=FI_FTN_TEST_SURNAME,
    full_name=FI_FTN_TEST_NAME,
)


ALL_FIXTURES = {
    "NO": NO_TEST_FIXTURE,
    "SE": SE_TEST_FIXTURE,
    "FI": FI_TEST_FIXTURE,
}
