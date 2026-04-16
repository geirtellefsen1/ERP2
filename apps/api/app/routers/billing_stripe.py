"""Stripe billing endpoints -- webhook + subscription management."""

from datetime import datetime, timezone
import logging

from fastapi import APIRouter, Depends, HTTPException, Header, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth import get_current_user, CurrentUser
from app.database import get_db
from app.models import AgencySubscription
from app.services.billing.stripe_client import (
    construct_webhook_event,
    create_customer,
    create_subscription,
    create_billing_portal_session,
)

router = APIRouter(prefix="/api/v1/billing", tags=["billing"])
logger = logging.getLogger(__name__)

# Map tiers to Stripe price IDs.  In production these come from env vars /
# a config table; hardcoded here for clarity.
TIER_PRICE_IDS: dict[str, str] = {
    "starter": "price_starter_monthly",
    "growth": "price_growth_monthly",
    "enterprise": "price_enterprise_monthly",
}


# -- Schemas ------------------------------------------------------------------


class SubscribeRequest(BaseModel):
    tier: str


class SubscriptionResponse(BaseModel):
    id: int
    agency_id: int
    stripe_customer_id: str
    stripe_subscription_id: str | None
    tier: str
    status: str
    current_period_end: datetime | None

    model_config = {"from_attributes": True}


class PortalResponse(BaseModel):
    url: str


# -- Subscription endpoints ---------------------------------------------------


@router.post("/subscribe", response_model=SubscriptionResponse)
def subscribe(
    body: SubscribeRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create (or replace) a Stripe subscription for the user's agency."""
    tier = body.tier.lower()
    if tier not in TIER_PRICE_IDS:
        raise HTTPException(status_code=400, detail=f"Unknown tier: {body.tier}")

    # Upsert: one subscription row per agency
    sub = (
        db.query(AgencySubscription)
        .filter(AgencySubscription.agency_id == current_user.agency_id)
        .first()
    )

    if sub is None:
        # First subscription -- create Stripe customer
        customer = create_customer(
            email=current_user.email,
            name=f"Agency {current_user.agency_id}",
            metadata={"agency_id": str(current_user.agency_id)},
        )
        stripe_sub = create_subscription(customer["id"], TIER_PRICE_IDS[tier])
        sub = AgencySubscription(
            agency_id=current_user.agency_id,
            stripe_customer_id=customer["id"],
            stripe_subscription_id=stripe_sub["id"],
            tier=tier,
            status=stripe_sub.get("status", "active"),
            current_period_end=datetime.fromtimestamp(
                stripe_sub["current_period_end"], tz=timezone.utc
            )
            if stripe_sub.get("current_period_end")
            else None,
        )
        db.add(sub)
    else:
        # Existing subscription -- create new Stripe subscription on same customer
        stripe_sub = create_subscription(
            sub.stripe_customer_id, TIER_PRICE_IDS[tier]
        )
        sub.stripe_subscription_id = stripe_sub["id"]
        sub.tier = tier
        sub.status = stripe_sub.get("status", "active")
        if stripe_sub.get("current_period_end"):
            sub.current_period_end = datetime.fromtimestamp(
                stripe_sub["current_period_end"], tz=timezone.utc
            )

    db.commit()
    db.refresh(sub)
    return sub


@router.post("/portal", response_model=PortalResponse)
def billing_portal(
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a Stripe Billing Portal session so the agency admin can manage payment methods."""
    sub = (
        db.query(AgencySubscription)
        .filter(AgencySubscription.agency_id == current_user.agency_id)
        .first()
    )
    if sub is None:
        raise HTTPException(
            status_code=404, detail="No subscription found -- subscribe first"
        )

    session = create_billing_portal_session(
        customer_id=sub.stripe_customer_id,
        return_url="http://localhost:3000/dashboard/settings/billing",
    )
    return PortalResponse(url=session["url"])


@router.get("/subscription", response_model=SubscriptionResponse | None)
def get_subscription(
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return the current agency's subscription info (or null)."""
    sub = (
        db.query(AgencySubscription)
        .filter(AgencySubscription.agency_id == current_user.agency_id)
        .first()
    )
    if sub is None:
        return None
    return sub


# -- Stripe webhook -----------------------------------------------------------


@router.post("/stripe/webhook", status_code=200)
async def stripe_webhook(
    request: Request, stripe_signature: str = Header(None)
):
    payload = await request.body()
    try:
        event = construct_webhook_event(payload, stripe_signature)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Signature verification failed: {e}"
        )

    event_type = event["type"]

    if event_type == "checkout.session.completed":
        logger.info(
            "Checkout session completed: %s", event["data"]["object"]["id"]
        )
    elif event_type == "customer.subscription.updated":
        logger.info(
            "Subscription updated: %s", event["data"]["object"]["id"]
        )
    elif event_type == "invoice.paid":
        logger.info("Invoice paid: %s", event["data"]["object"]["id"])
    else:
        logger.debug("Unhandled event type: %s", event_type)
        return {"status": "ignored"}

    return {"status": "ok"}
