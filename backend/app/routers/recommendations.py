from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.poi import POI
from app.models.user import User
from app.routers.auth import get_current_user
from app.schemas.recommendation import RecommendationResponse
from app.services.recommendation_service import recommend_pois


router = APIRouter(
    prefix="/recommendations",
    tags=["Recommendations"],
)


@router.get(
    "",
    response_model=list[RecommendationResponse],
)
def get_recommendations(
    limit: int = 10,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    limit = max(1, min(limit, 50))

    pois = db.scalars(
        select(POI).where(
            POI.is_active.is_(True)
        )
    ).all()

    recommendations = recommend_pois(db, user, pois)

    return recommendations[:limit]