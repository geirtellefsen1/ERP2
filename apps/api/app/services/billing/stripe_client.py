"""Thin wrappers around the Stripe Python SDK."""

import os

import stripe

stripe.api_key = os.environ.get("STRIPE_SECRET_KEY", "")


def create_customer(
    email: str, name: str, metadata: dict = None
) -> stripe.Customer:
    """Create a Stripe customer."""
    params: dict = {"email": email, "name": name}
    if metadata:
        params["metadata"] = metadata
    return stripe.Customer.create(**params)


def create_subscription(
    customer_id: str, price_id: str
) -> stripe.Subscription:
    """Create a subscription for a customer with the given price."""
    return stripe.Subscription.create(
        customer=customer_id,
        items=[{"price": price_id}],
    )


def create_billing_portal_session(
    customer_id: str, return_url: str
) -> stripe.billing_portal.Session:
    """Create a Stripe Billing Portal session so the customer can manage their subscription."""
    return stripe.billing_portal.Session.create(
        customer=customer_id,
        return_url=return_url,
    )


def construct_webhook_event(
    payload: bytes, sig_header: str
) -> stripe.Event:
    """Verify and construct a Stripe webhook event from a raw payload."""
    webhook_secret = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
    return stripe.Webhook.construct_event(
        payload, sig_header, webhook_secret
    )
