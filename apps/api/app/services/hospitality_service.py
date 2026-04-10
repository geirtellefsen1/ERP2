from decimal import Decimal, ROUND_HALF_UP
from typing import List, Optional
from app.models.hospitality import DailyRevenue


def calculate_revpar(revenue_data: List[DailyRevenue]) -> Decimal:
    """Revenue Per Available Room = total_revenue / rooms_available"""
    total_revenue = sum(
        (Decimal(str(r.total_revenue)) for r in revenue_data),
        Decimal("0"),
    )
    rooms_available = sum(
        (r.rooms_available or 0 for r in revenue_data),
        0,
    )
    if rooms_available == 0:
        return Decimal("0")
    return (total_revenue / Decimal(str(rooms_available))).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )


def calculate_adr(revenue_data: List[DailyRevenue]) -> Decimal:
    """Average Daily Rate = total_revenue / rooms_occupied"""
    total_revenue = sum(
        (Decimal(str(r.total_revenue)) for r in revenue_data),
        Decimal("0"),
    )
    rooms_occupied = sum(
        (r.rooms_occupied or 0 for r in revenue_data),
        0,
    )
    if rooms_occupied == 0:
        return Decimal("0")
    return (total_revenue / Decimal(str(rooms_occupied))).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )


def calculate_occupancy(revenue_data: List[DailyRevenue]) -> Decimal:
    """Occupancy = (rooms_occupied / rooms_available) * 100"""
    rooms_available = sum(
        (r.rooms_available or 0 for r in revenue_data),
        0,
    )
    rooms_occupied = sum(
        (r.rooms_occupied or 0 for r in revenue_data),
        0,
    )
    if rooms_available == 0:
        return Decimal("0")
    return (Decimal(str(rooms_occupied)) / Decimal(str(rooms_available)) * Decimal("100")).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )


def calculate_stock_variance(counted: int, expected: int, unit_cost: Decimal) -> Decimal:
    """Stock variance = (counted - expected) * unit_cost"""
    return (Decimal(str(counted)) - Decimal(str(expected))) * Decimal(str(unit_cost))
