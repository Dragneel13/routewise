from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.constants import INTERESTS
from app.database import get_db
from app.models.user import User
from app.routers.auth import get_current_user
from app.schemas.profile import ProfileResponse, ProfileUpdate


router = APIRouter(
    prefix="/me",
    tags=["Profile"],
)


def to_profile(user: User) -> ProfileResponse:
    return ProfileResponse(
        id=user.id,
        name=user.name,
        email=user.email,
        interests=[
            interest
            for interest in user.interests.split(",")
            if interest
        ],
        budget_style=user.budget_style,
        preferred_transport=user.preferred_transport,
        home_area=user.home_area,
        share_checkins=user.share_checkins,
    )


@router.get(
    "/profile",
    response_model=ProfileResponse,
)
def get_profile(
    user: User = Depends(get_current_user),
):
    return to_profile(user)


@router.put(
    "/profile",
    response_model=ProfileResponse,
)
def update_profile(
    data: ProfileUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    invalid_interests = [
        interest
        for interest in data.interests
        if interest not in INTERESTS
    ]

    if invalid_interests:
        raise HTTPException(
            status_code=422,
            detail=(
                f"Unknown interests: {invalid_interests}. "
                f"Use: {INTERESTS}"
            ),
        )

    user.interests = ",".join(data.interests)
    user.budget_style = data.budget_style
    user.preferred_transport = data.preferred_transport
    user.home_area = data.home_area
    user.share_checkins = data.share_checkins

    db.commit()
    db.refresh(user)

    return to_profile(user)