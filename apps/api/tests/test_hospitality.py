from decimal import Decimal
from datetime import date

from fastapi.testclient import TestClient
from app.main import app
from app.services.hospitality_service import (
    calculate_revpar,
    calculate_adr,
    calculate_occupancy,
    calculate_stock_variance,
)

client = TestClient(app)


# ---- Auth guard tests ----

def test_create_hospitality_client_requires_auth():
    response = client.post("/hospitality/clients", json={"client_id": 1})
    assert response.status_code == 401


def test_list_hospitality_clients_requires_auth():
    response = client.get("/hospitality/clients")
    assert response.status_code == 401


def test_create_room_type_requires_auth():
    response = client.post("/hospitality/room-types", json={"hospitality_client_id": 1, "code": "STD", "name": "Standard"})
    assert response.status_code == 401


def test_list_room_types_requires_auth():
    response = client.get("/hospitality/room-types")
    assert response.status_code == 401


def test_create_daily_revenue_requires_auth():
    response = client.post("/hospitality/daily-revenue", json={
        "hospitality_client_id": 1,
        "date": "2026-04-01",
    })
    assert response.status_code == 401


def test_list_daily_revenue_requires_auth():
    response = client.get("/hospitality/daily-revenue")
    assert response.status_code == 401


def test_get_metrics_requires_auth():
    response = client.get("/hospitality/metrics", params={
        "hospitality_client_id": 1,
        "start_date": "2026-04-01",
        "end_date": "2026-04-30",
    })
    assert response.status_code == 401


def test_create_tip_requires_auth():
    response = client.post("/hospitality/tips", json={
        "hospitality_client_id": 1,
        "date": "2026-04-01",
        "amount": "50.00",
    })
    assert response.status_code == 401


def test_create_stock_take_requires_auth():
    response = client.post("/hospitality/stock-take", json={
        "hospitality_client_id": 1,
        "date": "2026-04-01",
    })
    assert response.status_code == 401


# ---- Service / calculation tests ----

class _FakeRevenue:
    """Lightweight stand-in for DailyRevenue rows."""
    def __init__(self, total_revenue, rooms_available, rooms_occupied):
        self.total_revenue = total_revenue
        self.rooms_available = rooms_available
        self.rooms_occupied = rooms_occupied


def test_revpar_calculation():
    """revenue=10000, rooms_available=100 -> RevPAR=100"""
    data = [_FakeRevenue(total_revenue=10000, rooms_available=100, rooms_occupied=80)]
    result = calculate_revpar(data)
    assert result == Decimal("100.00")


def test_adr_calculation():
    """revenue=10000, rooms_occupied=80 -> ADR=125"""
    data = [_FakeRevenue(total_revenue=10000, rooms_available=100, rooms_occupied=80)]
    result = calculate_adr(data)
    assert result == Decimal("125.00")


def test_occupancy_calculation():
    """occupied=80, available=100 -> 80%"""
    data = [_FakeRevenue(total_revenue=10000, rooms_available=100, rooms_occupied=80)]
    result = calculate_occupancy(data)
    assert result == Decimal("80.00")


def test_stock_variance_calculation():
    """counted=95, expected=100, unit_cost=50 -> variance=-250"""
    result = calculate_stock_variance(counted=95, expected=100, unit_cost=Decimal("50"))
    assert result == Decimal("-250")


def test_revpar_zero_rooms():
    """Edge case: no rooms available should return 0."""
    data = [_FakeRevenue(total_revenue=10000, rooms_available=0, rooms_occupied=0)]
    result = calculate_revpar(data)
    assert result == Decimal("0")


def test_adr_zero_occupied():
    """Edge case: no rooms occupied should return 0."""
    data = [_FakeRevenue(total_revenue=10000, rooms_available=100, rooms_occupied=0)]
    result = calculate_adr(data)
    assert result == Decimal("0")


def test_occupancy_zero_available():
    """Edge case: no rooms available should return 0."""
    data = [_FakeRevenue(total_revenue=0, rooms_available=0, rooms_occupied=0)]
    result = calculate_occupancy(data)
    assert result == Decimal("0")


def test_revpar_multiple_rows():
    """RevPAR across multiple rows: total revenue 15000, total available 200 -> 75"""
    data = [
        _FakeRevenue(total_revenue=10000, rooms_available=100, rooms_occupied=80),
        _FakeRevenue(total_revenue=5000, rooms_available=100, rooms_occupied=50),
    ]
    result = calculate_revpar(data)
    assert result == Decimal("75.00")


def test_stock_variance_positive():
    """Surplus: counted=110, expected=100, unit_cost=50 -> variance=500"""
    result = calculate_stock_variance(counted=110, expected=100, unit_cost=Decimal("50"))
    assert result == Decimal("500")
