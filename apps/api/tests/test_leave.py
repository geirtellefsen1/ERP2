from datetime import date
from fastapi.testclient import TestClient
from app.main import app
from app.routers.leave import router as leave_router
from app.services.leave_service import calculate_business_days

# Register the leave router so endpoints are available during tests
app.include_router(leave_router)

client = TestClient(app)


# ──────────────────────────────────────────────
# Auth-protected endpoint tests (401 without token)
# ──────────────────────────────────────────────


def test_create_leave_type_requires_auth():
    response = client.post("/leave/types", json={"client_id": 1, "name": "Annual"})
    assert response.status_code == 401 or response.status_code == 403


def test_list_leave_types_requires_auth():
    response = client.get("/leave/types")
    assert response.status_code == 401 or response.status_code == 403


def test_create_leave_request_requires_auth():
    response = client.post(
        "/leave/requests",
        json={"leave_type_id": 1, "start_date": "2026-04-01", "end_date": "2026-04-05"},
    )
    assert response.status_code == 401 or response.status_code == 403


def test_list_leave_requests_requires_auth():
    response = client.get("/leave/requests")
    assert response.status_code == 401 or response.status_code == 403


def test_get_leave_request_requires_auth():
    response = client.get("/leave/requests/1")
    assert response.status_code == 401 or response.status_code == 403


def test_approve_leave_request_requires_auth():
    response = client.post("/leave/requests/1/approve")
    assert response.status_code == 401 or response.status_code == 403


def test_reject_leave_request_requires_auth():
    response = client.post("/leave/requests/1/reject", json={"reason": "No"})
    assert response.status_code == 401 or response.status_code == 403


def test_get_leave_balance_requires_auth():
    response = client.get("/leave/balance/1")
    assert response.status_code == 401 or response.status_code == 403


def test_calculate_days_requires_auth():
    response = client.post(
        "/leave/calculate-days",
        json={"start_date": "2026-04-01", "end_date": "2026-04-05"},
    )
    assert response.status_code == 401 or response.status_code == 403


def test_leave_calendar_requires_auth():
    response = client.get("/leave/calendar/2026/4")
    assert response.status_code == 401 or response.status_code == 403


# ──────────────────────────────────────────────
# calculate_business_days unit tests
# ──────────────────────────────────────────────


def test_business_days_mon_to_fri_same_week():
    """Mon 2026-04-06 to Fri 2026-04-10 = 5 business days."""
    start = date(2026, 4, 6)
    end = date(2026, 4, 10)
    assert calculate_business_days(start, end) == 5


def test_business_days_two_weeks():
    """Mon 2026-04-06 to Fri 2026-04-17 = 10 business days."""
    start = date(2026, 4, 6)
    end = date(2026, 4, 17)
    assert calculate_business_days(start, end) == 10


def test_business_days_single_day_weekday():
    """Single weekday = 1 business day."""
    start = date(2026, 4, 6)  # Monday
    end = date(2026, 4, 6)
    assert calculate_business_days(start, end) == 1


def test_business_days_single_day_weekend():
    """Single weekend day = 0 business days."""
    start = date(2026, 4, 11)  # Saturday
    end = date(2026, 4, 11)
    assert calculate_business_days(start, end) == 0


def test_business_days_end_before_start():
    """End date before start date = 0 business days."""
    start = date(2026, 4, 10)
    end = date(2026, 4, 6)
    assert calculate_business_days(start, end) == 0


# ──────────────────────────────────────────────
# Service module import tests
# ──────────────────────────────────────────────


def test_service_module_imports():
    """Verify all expected functions are importable from leave_service."""
    from app.services.leave_service import (
        calculate_business_days,
        check_balance,
        submit_request,
        approve_request,
        reject_request,
    )
    assert callable(calculate_business_days)
    assert callable(check_balance)
    assert callable(submit_request)
    assert callable(approve_request)
    assert callable(reject_request)


def test_model_imports():
    """Verify leave models are importable."""
    from app.models.leave import LeaveType, LeaveBalance, LeaveRequest, LeaveBlackoutDate
    assert LeaveType.__tablename__ == "leave_types"
    assert LeaveBalance.__tablename__ == "leave_balances"
    assert LeaveRequest.__tablename__ == "leave_requests"
    assert LeaveBlackoutDate.__tablename__ == "leave_blackout_dates"


def test_schema_imports():
    """Verify leave schemas are importable."""
    from app.schemas.leave import (
        LeaveTypeCreate,
        LeaveTypeResponse,
        LeaveBalanceResponse,
        LeaveRequestCreate,
        LeaveRequestResponse,
        LeaveRequestList,
        LeaveCalendarResponse,
        BusinessDaysResponse,
    )
    assert LeaveTypeCreate is not None
    assert LeaveTypeResponse is not None
    assert LeaveBalanceResponse is not None
    assert LeaveRequestCreate is not None
    assert LeaveRequestResponse is not None
    assert LeaveRequestList is not None
    assert LeaveCalendarResponse is not None
    assert BusinessDaysResponse is not None
