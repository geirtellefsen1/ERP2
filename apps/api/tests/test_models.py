"""Test that all models import correctly and have expected attributes."""
from app.models import (
    Base,
    Agency,
    User,
    Client,
    ClientContact,
    Account,
    Invoice,
    InvoiceLineItem,
    Transaction,
    Document,
    PayrollRun,
)


def test_all_models_registered():
    table_names = set(Base.metadata.tables.keys())
    expected = {
        "agencies",
        "users",
        "clients",
        "client_contacts",
        "accounts",
        "invoices",
        "invoice_line_items",
        "transactions",
        "documents",
        "payroll_runs",
    }
    assert expected.issubset(table_names), f"Missing tables: {expected - table_names}"


def test_agency_columns():
    cols = {c.name for c in Agency.__table__.columns}
    assert "name" in cols
    assert "slug" in cols
    assert "subscription_tier" in cols
    assert "countries_enabled" in cols


def test_user_columns():
    cols = {c.name for c in User.__table__.columns}
    assert "email" in cols
    assert "role" in cols
    assert "agency_id" in cols
    assert "auth0_id" in cols


def test_client_columns():
    cols = {c.name for c in Client.__table__.columns}
    assert "agency_id" in cols
    assert "country" in cols
    assert "industry" in cols
    assert "health_score" in cols


def test_account_columns():
    cols = {c.name for c in Account.__table__.columns}
    assert "account_number" in cols
    assert "account_type" in cols
    assert "parent_account_id" in cols
    assert "balance" in cols


def test_transaction_columns():
    cols = {c.name for c in Transaction.__table__.columns}
    assert "transaction_date" in cols
    assert "debit_amount" in cols
    assert "credit_amount" in cols
    assert "transaction_type" in cols
    assert "status" in cols


def test_document_columns():
    cols = {c.name for c in Document.__table__.columns}
    assert "document_type" in cols
    assert "file_url" in cols
    assert "extraction_confidence" in cols
    assert "extracted_data" in cols


def test_invoice_columns():
    cols = {c.name for c in Invoice.__table__.columns}
    assert "invoice_number" in cols
    assert "amount" in cols
    assert "currency" in cols
    assert "status" in cols


def test_payroll_columns():
    cols = {c.name for c in PayrollRun.__table__.columns}
    assert "period_start" in cols
    assert "total_gross" in cols
    assert "total_paye" in cols
    assert "total_uif" in cols
