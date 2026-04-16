"""Feature-gating dependency for subscription tiers.

Usage::

    from app.middleware.feature_gate import require_feature

    @router.post("/ai/chat")
    async def chat(
        ...,
        current_user: CurrentUser = Depends(require_feature("ai_chat")),
    ):
        ...

Returns HTTP 402 if the agency's subscription tier does not include the
requested feature.
"""

from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import get_current_user, CurrentUser
from app.database import get_db

# Features available by tier -- each higher tier is a strict superset.
TIER_FEATURES: dict[str, set[str]] = {
    "starter": {"dsr", "basic_reports", "bank_feeds"},
    "growth": {
        "dsr",
        "basic_reports",
        "bank_feeds",
        "consolidation",
        "ai_chat",
        "advanced_reports",
    },
    "enterprise": {
        "dsr",
        "basic_reports",
        "bank_feeds",
        "consolidation",
        "ai_chat",
        "advanced_reports",
        "api_access",
        "custom_integrations",
        "sla",
    },
}


def require_feature(feature: str):
    """FastAPI dependency that returns 402 if the agency's tier doesn't include *feature*."""

    async def check_feature(
        current_user: CurrentUser = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> CurrentUser:
        from app.models import AgencySubscription

        sub = (
            db.query(AgencySubscription)
            .filter(AgencySubscription.agency_id == current_user.agency_id)
            .first()
        )
        tier = sub.tier if sub else "starter"
        if feature not in TIER_FEATURES.get(tier, set()):
            raise HTTPException(
                status_code=402,
                detail=f"Feature '{feature}' requires a higher subscription tier",
            )
        return current_user

    return check_feature
