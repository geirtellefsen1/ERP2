from fastapi import APIRouter, Request, HTTPException, Header
import logging

from app.services.billing.stripe_client import construct_webhook_event

router = APIRouter(prefix="/billing/stripe", tags=["billing"])
logger = logging.getLogger(__name__)


@router.post("/webhook", status_code=200)
async def stripe_webhook(request: Request, stripe_signature: str = Header(None)):
    payload = await request.body()
    try:
        event = construct_webhook_event(payload, stripe_signature)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Signature verification failed: {e}")

    event_type = event["type"]

    if event_type == "checkout.session.completed":
        logger.info("Checkout session completed: %s", event["data"]["object"]["id"])
    elif event_type == "customer.subscription.updated":
        logger.info("Subscription updated: %s", event["data"]["object"]["id"])
    elif event_type == "invoice.paid":
        logger.info("Invoice paid: %s", event["data"]["object"]["id"])
    else:
        logger.debug("Unhandled event type: %s", event_type)
        return {"status": "ignored"}

    return {"status": "ok"}
