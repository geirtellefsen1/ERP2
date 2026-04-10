from fastapi.testclient import TestClient
from app.main import app
from app.routers.cashflow import router as cashflow_router
from app.services.cashflow_engine import (
    generate_13_week_forecast,
    detect_alerts,
    generate_alert_narrative,
)

# Register the cashflow router so endpoints are available during tests
app.include_router(cashflow_router)

client = TestClient(app)


# ──────────────────────────────────────────────
# Auth-protected endpoint tests (401 without token)
# ──────────────────────────────────────────────


def test_create_forecast_requires_auth():
    response = client.post(
        "/cashflow/forecasts",
        json={
            "client_id": 1,
            "opening_balance": 100000,
            "avg_weekly_receipts": 50000,
            "avg_weekly_payments": 40000,
        },
    )
    assert response.status_code == 401 or response.status_code == 403


def test_list_forecasts_requires_auth():
    response = client.get("/cashflow/forecasts")
    assert response.status_code == 401 or response.status_code == 403


def test_get_forecast_requires_auth():
    response = client.get("/cashflow/forecasts/1")
    assert response.status_code == 401 or response.status_code == 403


def test_get_latest_forecast_requires_auth():
    response = client.get("/cashflow/forecasts/latest/1")
    assert response.status_code == 401 or response.status_code == 403


def test_publish_forecast_requires_auth():
    response = client.post("/cashflow/forecasts/1/publish")
    assert response.status_code == 401 or response.status_code == 403


def test_list_alerts_requires_auth():
    response = client.get("/cashflow/alerts")
    assert response.status_code == 401 or response.status_code == 403


# ──────────────────────────────────────────────
# Forecast engine unit tests
# ──────────────────────────────────────────────


def test_forecast_positive_scenario():
    """opening=100000, receipts=50000, payments=40000 -> all 13 weeks positive, no alerts."""
    lines = generate_13_week_forecast(
        client_id=1,
        opening_balance=100000,
        avg_weekly_receipts=50000,
        avg_weekly_payments=40000,
    )
    assert len(lines) == 13

    # All weeks should have positive closing balance
    for line in lines:
        assert line["closing_balance"] > 0
        assert line["receipts"] == 50000
        assert line["payments"] == 40000

    # First week opening should be 100000
    assert lines[0]["opening_balance"] == 100000
    # First week closing = 100000 + 50000 - 40000 = 110000
    assert lines[0]["closing_balance"] == 110000

    # Each week should chain: next opening = prev closing
    for i in range(1, 13):
        assert lines[i]["opening_balance"] == lines[i - 1]["closing_balance"]

    # No alerts in positive scenario (all balances well above 50k)
    alerts = detect_alerts(lines)
    # All closings are well above 50000 and growing, so no alerts
    assert len(alerts) == 0


def test_forecast_negative_scenario():
    """opening=10000, receipts=5000, payments=15000 -> goes negative, critical alert."""
    lines = generate_13_week_forecast(
        client_id=1,
        opening_balance=10000,
        avg_weekly_receipts=5000,
        avg_weekly_payments=15000,
    )
    assert len(lines) == 13

    # First week: 10000 + 5000 - 15000 = 0
    assert lines[0]["closing_balance"] == 0
    # Second week: 0 + 5000 - 15000 = -10000
    assert lines[1]["closing_balance"] == -10000

    # Should go negative from week 2 onwards
    negative_weeks = [line for line in lines if line["closing_balance"] < 0]
    assert len(negative_weeks) > 0

    # Detect alerts
    alerts = detect_alerts(lines)
    critical_alerts = [a for a in alerts if a["severity"] == "critical"]
    assert len(critical_alerts) > 0


def test_alert_detection_negative_balance():
    """Negative balance should produce critical alert."""
    lines = [
        {
            "week_commencing": "2026-04-13",
            "opening_balance": 10000,
            "receipts": 5000,
            "payments": 20000,
            "closing_balance": -5000,
            "alert_flag": True,
        },
    ]
    alerts = detect_alerts(lines)
    assert len(alerts) >= 1
    negative_alerts = [a for a in alerts if a["alert_type"] == "negative"]
    assert len(negative_alerts) == 1
    assert negative_alerts[0]["severity"] == "critical"
    assert negative_alerts[0]["week_number"] == 1


def test_alert_detection_low_balance():
    """Balance below 50000 should produce warning alert."""
    lines = [
        {
            "week_commencing": "2026-04-13",
            "opening_balance": 60000,
            "receipts": 10000,
            "payments": 30000,
            "closing_balance": 40000,
            "alert_flag": False,
        },
    ]
    alerts = detect_alerts(lines)
    warning_alerts = [a for a in alerts if a["alert_type"] == "low_balance"]
    assert len(warning_alerts) == 1
    assert warning_alerts[0]["severity"] == "warning"
    assert warning_alerts[0]["week_number"] == 1


def test_alert_detection_volatility():
    """More than 20% drop week-over-week should produce volatility alert."""
    lines = [
        {
            "week_commencing": "2026-04-13",
            "opening_balance": 200000,
            "receipts": 50000,
            "payments": 50000,
            "closing_balance": 200000,
            "alert_flag": False,
        },
        {
            "week_commencing": "2026-04-20",
            "opening_balance": 200000,
            "receipts": 10000,
            "payments": 100000,
            "closing_balance": 110000,
            "alert_flag": False,
        },
    ]
    alerts = detect_alerts(lines)
    volatility_alerts = [a for a in alerts if a["alert_type"] == "volatility"]
    assert len(volatility_alerts) == 1
    assert volatility_alerts[0]["severity"] == "info"
    assert volatility_alerts[0]["week_number"] == 2


def test_generate_alert_narrative_negative():
    narrative = generate_alert_narrative("negative", 3, -5000.0)
    assert "Critical" in narrative
    assert "week 3" in narrative
    assert "-5,000.00" in narrative


def test_generate_alert_narrative_low_balance():
    narrative = generate_alert_narrative("low_balance", 5, 25000.0)
    assert "Warning" in narrative
    assert "week 5" in narrative
    assert "25,000.00" in narrative


def test_generate_alert_narrative_volatility():
    narrative = generate_alert_narrative("volatility", 7, 80000.0)
    assert "Info" in narrative
    assert "week 7" in narrative


def test_forecast_week_chaining():
    """Verify each week's opening equals previous week's closing."""
    lines = generate_13_week_forecast(
        client_id=1,
        opening_balance=50000,
        avg_weekly_receipts=20000,
        avg_weekly_payments=18000,
    )
    for i in range(1, len(lines)):
        assert lines[i]["opening_balance"] == lines[i - 1]["closing_balance"]


# ──────────────────────────────────────────────
# Model and schema import tests
# ──────────────────────────────────────────────


def test_model_imports():
    """Verify cashflow models are importable."""
    from app.models.cashflow import CashflowForecast, CashflowForecastLine, ForecastAlert
    assert CashflowForecast.__tablename__ == "cashflow_forecasts"
    assert CashflowForecastLine.__tablename__ == "cashflow_forecast_lines"
    assert ForecastAlert.__tablename__ == "forecast_alerts"


def test_schema_imports():
    """Verify cashflow schemas are importable."""
    from app.schemas.cashflow import (
        CashflowForecastCreate,
        CashflowForecastResponse,
        CashflowForecastLineResponse,
        CashflowForecastDetail,
        ForecastAlertResponse,
        ForecastAlertList,
    )
    assert CashflowForecastCreate is not None
    assert CashflowForecastResponse is not None
    assert CashflowForecastLineResponse is not None
    assert CashflowForecastDetail is not None
    assert ForecastAlertResponse is not None
    assert ForecastAlertList is not None


def test_service_imports():
    """Verify cashflow engine functions are importable."""
    from app.services.cashflow_engine import (
        generate_13_week_forecast,
        detect_alerts,
        generate_alert_narrative,
    )
    assert callable(generate_13_week_forecast)
    assert callable(detect_alerts)
    assert callable(generate_alert_narrative)
