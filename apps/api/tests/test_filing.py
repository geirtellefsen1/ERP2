"""Statutory filing submitter tests."""
from __future__ import annotations

from datetime import date

import pytest

from app.services.filing import (
    StatutoryFiling,
    SubmissionReceipt,
    MockSubmitter,
    get_submitter,
    SubmitterError,
)


@pytest.fixture(autouse=True)
def _clear_mock():
    MockSubmitter.clear()
    yield
    MockSubmitter.clear()


@pytest.fixture
def sample_filing():
    return StatutoryFiling(
        form_code="MVA-melding",
        period_start=date(2026, 3, 1),
        period_end=date(2026, 4, 30),
        organisation_number="987654321",
        payload_xml="<mva-melding><test/></mva-melding>",
        metadata={"client_id": 42},
    )


# ── Factory ───────────────────────────────────────────────────────────────


def test_get_submitter_mock_returns_mock():
    s = get_submitter("NO", mode="mock")
    assert isinstance(s, MockSubmitter)


def test_get_submitter_live_raises_with_clear_message():
    with pytest.raises(SubmitterError) as exc:
        get_submitter("NO", mode="live")
    # Error message must mention what's missing so future developers know
    assert "credentials" in str(exc.value).lower() or "not yet implemented" in str(exc.value).lower()


def test_get_submitter_unknown_country_raises():
    with pytest.raises(SubmitterError):
        get_submitter("XX", mode="mock")


# ── Mock submitter behaviour ──────────────────────────────────────────────


def test_mock_submit_returns_accepted_receipt(sample_filing):
    submitter = MockSubmitter()
    receipt = submitter.submit(sample_filing)
    assert receipt.status == "accepted"
    assert receipt.provider == "mock"
    assert receipt.reference_number.startswith("MOCK-MVA-MELDING-")
    assert receipt.form_code == "MVA-melding"


def test_mock_submit_reference_is_deterministic(sample_filing):
    """Same filing = same reference number. Prevents duplicate submissions."""
    ref1 = MockSubmitter().submit(sample_filing).reference_number
    ref2 = MockSubmitter().submit(sample_filing).reference_number
    assert ref1 == ref2


def test_mock_submit_different_periods_get_different_refs(sample_filing):
    submitter = MockSubmitter()
    ref1 = submitter.submit(sample_filing).reference_number

    other = StatutoryFiling(
        form_code="MVA-melding",
        period_start=date(2026, 5, 1),
        period_end=date(2026, 6, 30),
        organisation_number="987654321",
        payload_xml="<mva-melding/>",
    )
    ref2 = submitter.submit(other).reference_number
    assert ref1 != ref2


def test_mock_check_status_after_submit(sample_filing):
    submitter = MockSubmitter()
    receipt = submitter.submit(sample_filing)
    fetched = submitter.check_status(receipt.reference_number)
    assert fetched.status == "accepted"
    assert fetched.reference_number == receipt.reference_number


def test_mock_check_status_unknown_reference_returns_error():
    submitter = MockSubmitter()
    result = submitter.check_status("does-not-exist")
    assert result.status == "error"


def test_mock_stores_payload_for_inspection(sample_filing):
    submitter = MockSubmitter()
    receipt = submitter.submit(sample_filing)
    stored = MockSubmitter.get_payload(receipt.reference_number)
    assert stored is not None
    assert stored.form_code == "MVA-melding"
    assert stored.metadata == {"client_id": 42}
    assert stored.payload_xml == sample_filing.payload_xml


def test_mock_all_submissions_collects_all(sample_filing):
    submitter = MockSubmitter()
    submitter.submit(sample_filing)

    other = StatutoryFiling(
        form_code="A-melding",
        period_start=date(2026, 4, 1),
        period_end=date(2026, 4, 30),
        organisation_number="987654321",
        payload_xml="<a-melding/>",
    )
    submitter.submit(other)

    all_subs = MockSubmitter.all_submissions()
    assert len(all_subs) == 2
    form_codes = {s.form_code for s in all_subs}
    assert form_codes == {"MVA-melding", "A-melding"}


# ── Integration: payroll/VAT → filing ────────────────────────────────────


def test_mock_submitter_accepts_payroll_xml_payload():
    """End-to-end: generate A-melding XML, submit via mock, verify receipt."""
    from decimal import Decimal
    from app.services.money import Money
    from app.services.payroll import (
        EmployeeInput,
        PayrollInput,
        run_payroll,
    )
    from app.services.payroll.norway import NorwayPayrollCalculator

    employees = [
        EmployeeInput(
            id=1,
            first_name="Sarah",
            last_name="Mokoena",
            gross_salary=Money("45000.00", "NOK"),
            tax_percentage=Decimal("0.35"),
            age=38,
            work_region="oslo",
            pension_scheme="NO_OTP_2_PERCENT",
        )
    ]
    result = run_payroll(
        PayrollInput(
            country="NO",
            period_start=date(2026, 4, 1),
            period_end=date(2026, 4, 30),
            employees=employees,
        )
    )
    xml = NorwayPayrollCalculator.generate_a_melding(
        organisation_number="987654321",
        period_year=2026,
        period_month=4,
        payslips=result.payslips,
    )

    submitter = get_submitter("NO", mode="mock")
    filing = StatutoryFiling(
        form_code="A-melding",
        period_start=date(2026, 4, 1),
        period_end=date(2026, 4, 30),
        organisation_number="987654321",
        payload_xml=xml,
    )
    receipt = submitter.submit(filing)
    assert receipt.status == "accepted"

    # Verify the stored payload matches what we sent
    stored = MockSubmitter.get_payload(receipt.reference_number)
    assert stored.payload_xml == xml
    assert "Sarah Mokoena" in stored.payload_xml


def test_mock_submitter_accepts_vat_xml_payload():
    """End-to-end: generate MVA-melding XML, submit via mock."""
    from app.services.money import Money
    from app.services.vat import (
        VatTransaction,
        VatReturnInput,
        build_vat_return,
        NorwayVatReturn,
    )

    result = build_vat_return(
        VatReturnInput(
            country="NO",
            period_start=date(2026, 3, 1),
            period_end=date(2026, 4, 30),
            transactions=[
                VatTransaction(Money("10000", "NOK"), "NO-25", "sale"),
                VatTransaction(Money("3000", "NOK"), "NO-25", "purchase"),
            ],
        )
    )
    xml = NorwayVatReturn.to_xml(result, organisation_number="987654321")

    submitter = get_submitter("NO", mode="mock")
    filing = StatutoryFiling(
        form_code="MVA-melding",
        period_start=date(2026, 3, 1),
        period_end=date(2026, 4, 30),
        organisation_number="987654321",
        payload_xml=xml,
    )
    receipt = submitter.submit(filing)
    assert receipt.status == "accepted"
    assert "MOCK-MVA-MELDING" in receipt.reference_number
