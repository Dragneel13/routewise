from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.poi import POI
from app.models.trip import Trip, TripStop
from app.models.user import User
from app.routers.auth import get_current_user
from app.schemas.transport import (
    TransportOption,
    TransportOptionsResponse,
)
from app.services.transport_service import generate_transport_options
from app.models.trip import Trip, TripLeg, TripStop
from app.schemas.transport import ( TransportOption, TransportOptionsResponse, TransportSelection,
)

router = APIRouter(
    prefix="/trips",
    tags=["Transport"],
)


@router.get(
    "/{trip_id}/stops/{from_stop_id}/{to_stop_id}/transport",
    response_model=TransportOptionsResponse,
)
def get_transport_options(
    trip_id: int,
    from_stop_id: int,
    to_stop_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    trip = db.scalar(
        select(Trip).where(
            Trip.id == trip_id,
            Trip.user_id == user.id,
        )
    )

    if not trip:
        raise HTTPException(
            status_code=404,
            detail="Trip not found.",
        )

    if from_stop_id == to_stop_id:
        raise HTTPException(
            status_code=400,
            detail="Origin and destination stops must be different.",
        )

    from_stop = db.scalar(
        select(TripStop).where(
            TripStop.id == from_stop_id,
            TripStop.trip_id == trip.id,
        )
    )

    to_stop = db.scalar(
        select(TripStop).where(
            TripStop.id == to_stop_id,
            TripStop.trip_id == trip.id,
        )
    )

    if not from_stop:
        raise HTTPException(
            status_code=404,
            detail="Origin trip stop not found.",
        )

    if not to_stop:
        raise HTTPException(
            status_code=404,
            detail="Destination trip stop not found.",
        )

    origin = db.get(POI, from_stop.poi_id)
    destination = db.get(POI, to_stop.poi_id)

    if not origin or not destination:
        raise HTTPException(
            status_code=404,
            detail="Origin or destination place not found.",
        )

    options = generate_transport_options(
        origin=origin,
        destination=destination,
    )

    return {
        "trip_id": trip.id,
        "from_stop_id": from_stop.id,
        "to_stop_id": to_stop.id,
        "from_poi": origin.name,
        "to_poi": destination.name,
        "options": options,
    }

@router.post(
    "/{trip_id}/stops/{from_stop_id}/{to_stop_id}/transport/select"
)
def select_transport_option(
    trip_id: int,
    from_stop_id: int,
    to_stop_id: int,
    data: TransportSelection,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    trip = db.scalar(
        select(Trip).where(
            Trip.id == trip_id,
            Trip.user_id == user.id,
        )
    )

    if not trip:
        raise HTTPException(
            status_code=404,
            detail="Trip not found.",
        )

    from_stop = db.scalar(
        select(TripStop).where(
            TripStop.id == from_stop_id,
            TripStop.trip_id == trip.id,
        )
    )

    to_stop = db.scalar(
        select(TripStop).where(
            TripStop.id == to_stop_id,
            TripStop.trip_id == trip.id,
        )
    )

    if not from_stop or not to_stop:
        raise HTTPException(
            status_code=404,
            detail="Trip stop not found.",
        )

    origin = db.get(POI, from_stop.poi_id)
    destination = db.get(POI, to_stop.poi_id)

    if not origin or not destination:
        raise HTTPException(
            status_code=404,
            detail="Origin or destination POI not found.",
        )

    options = generate_transport_options(
        origin=origin,
        destination=destination,
    )

    selected = next(
        (
            option
            for option in options
            if option["mode"] == data.mode
            and option["option_type"] == data.option_type
        ),
        None,
    )

    if not selected:
        raise HTTPException(
            status_code=400,
            detail="Selected transport option is not available.",
        )

    existing_leg = db.scalar(
        select(TripLeg).where(
            TripLeg.trip_id == trip.id,
            TripLeg.from_stop_id == from_stop.id,
            TripLeg.to_stop_id == to_stop.id,
        )
    )

    if existing_leg:
        leg = existing_leg
    else:
        leg = TripLeg(
            trip_id=trip.id,
            from_stop_id=from_stop.id,
            to_stop_id=to_stop.id,
            mode=selected["mode"],
            option_type=selected["option_type"],
        )
        db.add(leg)

    leg.mode = selected["mode"]
    leg.option_type = selected["option_type"]
    leg.boarding_stop = selected["boarding_stop"]
    leg.alighting_stop = selected["alighting_stop"]
    leg.intermediate_stops = ",".join(
        selected["intermediate_stops"]
    )
    leg.duration_minutes = selected["duration_minutes"]
    leg.walking_minutes = selected["walking_minutes"]
    leg.distance_km = selected["distance_km"]
    leg.fare = selected["fare"]
    leg.reliability_score = selected["reliability_score"]


    db.flush()

    trip.total_transport_cost = sum(
        row[0]
        for row in db.query(TripLeg.fare)
        .filter(TripLeg.trip_id == trip.id)
        .all()
    )

    db.commit()
    db.refresh(leg)

    return {
        "message": "Transport option selected.",
        "leg_id": leg.id,
        "trip_id": trip.id,
        "from_stop_id": from_stop.id,
        "to_stop_id": to_stop.id,
        "mode": leg.mode,
        "option_type": leg.option_type,
        "duration_minutes": leg.duration_minutes,
        "walking_minutes": leg.walking_minutes,
        "distance_km": leg.distance_km,
        "fare": leg.fare,
        "boarding_stop": leg.boarding_stop,
        "alighting_stop": leg.alighting_stop,
        "intermediate_stops": (
            leg.intermediate_stops.split(",")
            if leg.intermediate_stops
            else []
        ),
        "reliability_score": leg.reliability_score,
        "trip_total_transport_cost": trip.total_transport_cost,
    }