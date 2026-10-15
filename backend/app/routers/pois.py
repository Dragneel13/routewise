from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.poi import POI
from app.models.user import User
from app.routers.auth import get_current_user
from app.schemas.poi import POIResponse


router = APIRouter(
    prefix="/pois",
    tags=["POIs"],
)


@router.get(
    "",
    response_model=list[POIResponse],
)
def list_pois(
    q: str | None = None,
    category: str | None = None,
    area: str | None = None,
    max_fee: float | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    stmt = select(POI).where(
        POI.is_active.is_(True)
    )

    if q:
        stmt = stmt.where(
            POI.name.ilike(f"%{q}%")
        )

    if category:
        stmt = stmt.where(
        POI.category.ilike(category)
    )

    if area:
        stmt = stmt.where(
            POI.area == area
        )

    if max_fee is not None:
        stmt = stmt.where(
            POI.entry_fee <= max_fee
        )

    stmt = stmt.order_by(
        POI.popularity.desc()
    )

    return db.scalars(stmt).all()


@router.get(
    "/{poi_id}",
    response_model=POIResponse,
)
def get_poi(
    poi_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    poi = db.get(POI, poi_id)

    if not poi or not poi.is_active:
        raise HTTPException(
            status_code=404,
            detail="Place not found.",
        )

    return poi