from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from jose import jwt
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.poi import POI
from app.models.trip import Trip, TripLeg, TripStop
from app.models.user import User
from app.routers.auth import get_current_user
from app.schemas.trip import (
    SharedTripResponse,
    SharedTripStopResponse,
    TripBudgetResponse,
    TripCreate,
    TripReorder,
    TripResponse,
    TripShareResponse,
    TripStopAdd,
    TripStopUpdate,
)
from app.schemas.weather import TripWeatherImpactResponse
from app.services.weather_service import get_weather_assessment
from app.schemas.weather import (
    ReplanResponse,
    TripWeatherImpactResponse,
)
from app.services.transport_service import generate_transport_options
from app.services.weather_service import get_weather_assessment
from fastapi.responses import Response
from app.services.pdf_service import generate_trip_pdf
from app.config import settings


router = APIRouter(prefix="/trips", tags=["Trips"])


def get_user_trip(db: Session, trip_id: int, user_id: int) -> Trip:
    trip = db.scalar(
        select(Trip).where(
            Trip.id == trip_id,
            Trip.user_id == user_id,
        )
    )

    if not trip:
        raise HTTPException(
            status_code=404,
            detail="Trip not found.",
        )

    return trip


def invalidate_transport_legs(db: Session, trip: Trip):
    db.query(TripLeg).filter(
        TripLeg.trip_id == trip.id
    ).delete(synchronize_session=False)

    trip.total_transport_cost = 0.0


def recalculate_entry_cost(db: Session, trip: Trip):
    stops = db.scalars(
        select(TripStop).where(
            TripStop.trip_id == trip.id
        )
    ).all()

    total = 0.0

    for stop in stops:
        poi = db.get(POI, stop.poi_id)

        if poi:
            stop.entry_cost = poi.entry_fee
            total += poi.entry_fee

    trip.total_entry_cost = total


def calculate_trip_budget(db: Session, trip: Trip):
    stops = db.scalars(
        select(TripStop)
        .where(TripStop.trip_id == trip.id)
        .order_by(TripStop.sequence)
    ).all()
    food_per_stop = 150.0
    estimated_food = len(stops) * food_per_stop
    base_cost = (
        trip.total_transport_cost
        + trip.total_entry_cost
        + estimated_food
    )

    buffer = round(base_cost * 0.10, 2)

    trip.total_food_cost = estimated_food
    trip.buffer_cost = buffer

    estimated_total = round(
        trip.total_transport_cost
        + trip.total_entry_cost
        + trip.total_food_cost
        + trip.buffer_cost,
        2,
    )

    remaining_budget = round(
        trip.budget - estimated_total,
        2,
    )

    if trip.budget > 0:
        budget_used_percent = round(
            (estimated_total / trip.budget) * 100,
            2,
        )
    else:
        budget_used_percent = 100.0

    if estimated_total <= trip.budget:
        budget_status = "Within budget"
        suggestion = None
    else:
        budget_status = "Over budget"

        excess = round(
            estimated_total - trip.budget,
            2,
        )

        suggestion = (
            f"Reduce approximately ₹{excess:.0f} "
            "by choosing cheaper transport, removing a paid place, "
            "or reducing food spending."
        )

    return {
        "trip_id": trip.id,
        "budget": round(trip.budget, 2),
        "total_transport_cost": round(
            trip.total_transport_cost,
            2,
        ),
        "total_entry_cost": round(
            trip.total_entry_cost,
            2,
        ),
        "total_food_cost": round(
            trip.total_food_cost,
            2,
        ),
        "buffer_cost": round(
            trip.buffer_cost,
            2,
        ),
        "estimated_total": estimated_total,
        "remaining_budget": remaining_budget,
        "budget_used_percent": budget_used_percent,
        "budget_status": budget_status,
        "suggestion": suggestion,
    }


@router.post("", response_model=TripResponse)
def create_trip(
    data: TripCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    trip = Trip(
        user_id=user.id,
        name=data.name,
        start_location=data.start_location,
        budget=data.budget,
        total_transport_cost=0.0,
        total_entry_cost=0.0,
        total_food_cost=0.0,
        buffer_cost=0.0,
        is_saved=True,
    )

    db.add(trip)
    db.commit()
    db.refresh(trip)

    return trip


@router.get("", response_model=list[TripResponse])
def list_trips(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    trips = db.scalars(
        select(Trip)
        .where(Trip.user_id == user.id)
        .order_by(Trip.created_at.desc())
    ).all()

    return trips

@router.get("/saved", response_model=list[TripResponse])
def get_saved_trips(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    trips = db.scalars(
        select(Trip)
        .where(
            Trip.user_id == user.id,
            Trip.is_saved.is_(True),
        )
        .order_by(Trip.updated_at.desc())
    ).all()

    return trips


@router.get("/{trip_id}", response_model=TripResponse)
def get_trip(
    trip_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return get_user_trip(
        db,
        trip_id,
        user.id,
    )


@router.get(
    "/shared/{share_token}",
    response_model=SharedTripResponse,
)
def get_shared_trip(
    share_token: str,
    db: Session = Depends(get_db),
):
    try:
        payload = jwt.decode(
            share_token,
            settings.secret_key,
            algorithms=["HS256"],
        )
    except Exception:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired share link.",
        )

    if payload.get("purpose") != "trip_share":
        raise HTTPException(
            status_code=401,
            detail="Invalid share link.",
        )

    trip_id = payload.get("sub")

    if not trip_id:
        raise HTTPException(
            status_code=401,
            detail="Invalid share link.",
        )

    try:
        trip_id = int(trip_id)
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=401,
            detail="Invalid share link.",
        )

    trip = db.get(Trip, trip_id)

    if not trip:
        raise HTTPException(
            status_code=404,
            detail="Trip not found.",
        )

    stops_db = db.scalars(
        select(TripStop)
        .where(TripStop.trip_id == trip.id)
        .order_by(TripStop.sequence)
    ).all()

    stops = []

    for stop in stops_db:
        poi = db.get(POI, stop.poi_id)

        if poi:
            stops.append(
                SharedTripStopResponse(
                    sequence=stop.sequence,
                    poi_name=poi.name,
                    area=poi.area,
                    duration_minutes=stop.duration_minutes,
                    entry_cost=stop.entry_cost,
                )
            )

    return SharedTripResponse(
        trip_id=trip.id,
        name=trip.name,
        start_location=trip.start_location,
        budget=trip.budget,
        total_transport_cost=trip.total_transport_cost,
        total_entry_cost=trip.total_entry_cost,
        total_food_cost=trip.total_food_cost,
        buffer_cost=trip.buffer_cost,
        stops=stops,
    )


@router.patch("/{trip_id}/save")
def toggle_save_trip(
    trip_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    trip = get_user_trip(db, trip_id, user.id)

    trip.is_saved = not trip.is_saved

    db.commit()
    db.refresh(trip)

    return {
        "trip_id": trip.id,
        "is_saved": trip.is_saved,
        "message": (
            "Trip saved successfully."
            if trip.is_saved
            else "Trip removed from saved trips."
        ),
    }


@router.post(
    "/{trip_id}/share",
    response_model=TripShareResponse,
)
def share_trip(
    trip_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    trip = get_user_trip(db, trip_id, user.id)

    token = jwt.encode(
        {
            "sub": str(trip.id),
            "purpose": "trip_share",
        },
        settings.secret_key,
        algorithm="HS256",
    )

    share_url = (
        f"{settings.frontend_url.rstrip('/')}/shared-trip/{token}"
    )

    return {
        "trip_id": trip.id,
        "share_token": token,
        "share_url": share_url,
    }


@router.get("/{trip_id}", response_model=TripResponse)
def get_trip(
    trip_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return get_user_trip(
        db,
        trip_id,
        user.id,
    )

@router.get(
    "/{trip_id}/budget",
    response_model=TripBudgetResponse,
)
def get_trip_budget(
    trip_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    trip = get_user_trip(
        db,
        trip_id,
        user.id,
    )

    budget = calculate_trip_budget(db, trip)

    db.commit()

    return budget

@router.get(
    "/{trip_id}/weather-impact",
    response_model=TripWeatherImpactResponse,
)
def get_trip_weather_impact(
    trip_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    trip = get_user_trip(
        db,
        trip_id,
        user.id,
    )

    weather = get_weather_assessment()

    if not weather.get("available"):
        raise HTTPException(
            status_code=503,
            detail=weather.get(
                "error",
                "Weather service unavailable.",
            ),
        )

    weather_risk = weather.get(
        "weather_risk",
        "low",
    )

    walking_warning = weather.get(
        "walking_warning",
        False,
    )
    legs = db.scalars(
        select(TripLeg)
        .where(TripLeg.trip_id == trip.id)
    ).all()

    current_walking_minutes = sum(
        leg.walking_minutes
        for leg in legs
    )

    if weather_risk == "storm":
        walking_penalty = 0.50
        recommended_mode = "Metro / Auto"
        replan_recommended = True
        message = (
            "Thunderstorm conditions may make outdoor travel "
            "unsafe or uncomfortable. Prefer metro or auto "
            "and minimize walking."
        )

    elif weather_risk == "rain":
        walking_penalty = 0.30
        recommended_mode = "Metro / Bus / Auto"
        replan_recommended = current_walking_minutes >= 10
        message = (
            "Rain may make walking uncomfortable. Prefer metro, "
            "bus or auto and reduce long walking segments."
        )

    elif weather_risk == "fog":
        walking_penalty = 0.15
        recommended_mode = "Metro / Bus"
        replan_recommended = False
        message = (
            "Reduced visibility is possible. Allow extra travel "
            "time and prefer predictable public transport."
        )

    else:
        walking_penalty = 0.0
        recommended_mode = "Any"
        replan_recommended = False
        message = (
            "Weather conditions are suitable for the current itinerary."
        )

    return {
        "trip_id": trip.id,
        "weather_risk": weather_risk,
        "walking_warning": walking_warning,
        "walking_penalty": walking_penalty,
        "current_walking_minutes": current_walking_minutes,
        "recommended_mode": recommended_mode,
        "replan_recommended": replan_recommended,
        "message": message,
    }

@router.post(
    "/{trip_id}/replan",
    response_model=ReplanResponse,
)
def replan_trip(
    trip_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    trip = get_user_trip(
        db,
        trip_id,
        user.id,
    )

    stops = db.scalars(
        select(TripStop)
        .where(TripStop.trip_id == trip.id)
        .order_by(TripStop.sequence)
    ).all()

    if len(stops) < 2:
        raise HTTPException(
            status_code=400,
            detail="At least two places are required to replan transport.",
        )

    weather = get_weather_assessment()

    if not weather.get("available"):
        raise HTTPException(
            status_code=503,
            detail=weather.get(
                "error",
                "Weather service unavailable.",
            ),
        )

    weather_risk = weather.get(
        "weather_risk",
        "low",
    )
    invalidate_transport_legs(db, trip)

    replanned_legs = []

    for index in range(len(stops) - 1):
        from_stop = stops[index]
        to_stop = stops[index + 1]

        from_poi = db.get(POI, from_stop.poi_id)
        to_poi = db.get(POI, to_stop.poi_id)

        if not from_poi or not to_poi:
            continue

        options = generate_transport_options(
            from_poi,
            to_poi,
        )

        if not options:
            continue

        best_option = None
        best_score = float("inf")

        for option in options:
            duration_score = option["duration_minutes"] / 60.0
            fare_score = option["fare"] / 100.0
            walking_score = option["walking_minutes"] / 30.0

            score = (
                duration_score * 0.45
                + fare_score * 0.20
                + walking_score * 0.35
            )
            if weather_risk == "rain":
                score += option["walking_minutes"] * 0.03

            elif weather_risk == "storm":
                score += option["walking_minutes"] * 0.08

            elif weather_risk == "fog":
                score += option["duration_minutes"] * 0.01

            if score < best_score:
                best_score = score
                best_option = option

        if best_option is None:
            continue
        leg = TripLeg(
            trip_id=trip.id,
            from_stop_id=from_stop.id,
            to_stop_id=to_stop.id,
            mode=best_option["mode"],
            option_type="Replanned",
            boarding_stop=best_option.get("boarding_stop"),
            alighting_stop=best_option.get("alighting_stop"),
            intermediate_stops=",".join(
                best_option.get("intermediate_stops", [])
            ),
            duration_minutes=best_option["duration_minutes"],
            walking_minutes=best_option["walking_minutes"],
            distance_km=best_option["distance_km"],
            fare=best_option["fare"],
            reliability_score=best_option["reliability_score"],
        )

        db.add(leg)

        replanned_legs.append(
            {
                "from_stop_id": from_stop.id,
                "to_stop_id": to_stop.id,
                "from_poi": from_poi.name,
                "to_poi": to_poi.name,
                "mode": best_option["mode"],
                "option_type": "Replanned",
                "duration_minutes": best_option["duration_minutes"],
                "walking_minutes": best_option["walking_minutes"],
                "distance_km": best_option["distance_km"],
                "fare": best_option["fare"],
                "weather_adjusted_score": round(
                    best_score,
                    3,
                ),
            }
        )
    db.flush()

    legs = db.scalars(
        select(TripLeg).where(
            TripLeg.trip_id == trip.id
        )
    ).all()

    trip.total_transport_cost = round(
        sum(leg.fare for leg in legs),
        2,
    )

    db.commit()

    if weather_risk == "rain":
        reason = "Rain-aware replanning"
    elif weather_risk == "storm":
        reason = "Storm-aware replanning"
    elif weather_risk == "fog":
        reason = "Visibility-aware replanning"
    else:
        reason = "Weather-aware route optimization"

    return {
        "trip_id": trip.id,
        "weather_risk": weather_risk,
        "replan_reason": reason,
        "legs": replanned_legs,
        "total_transport_cost": trip.total_transport_cost,
        "message": (
            "The itinerary transport legs were regenerated "
            "using current weather conditions."
        ),
    }

@router.get("/{trip_id}/export/pdf")
def export_trip_pdf(
    trip_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    trip = get_user_trip(
        db,
        trip_id,
        user.id,
    )

    stops_db = db.scalars(
        select(TripStop)
        .where(TripStop.trip_id == trip.id)
        .order_by(TripStop.sequence)
    ).all()

    stops = []

    for stop in stops_db:
        poi = db.get(POI, stop.poi_id)

        if poi:
            stops.append(
                {
                    "stop_id": stop.id,
                    "poi_id": poi.id,
                    "poi_name": poi.name,
                    "area": poi.area,
                    "sequence": stop.sequence,
                    "duration_minutes": stop.duration_minutes,
                    "locked": stop.locked,
                    "entry_cost": stop.entry_cost,
                }
            )

    legs = db.scalars(
        select(TripLeg)
        .where(TripLeg.trip_id == trip.id)
        .order_by(TripLeg.id)
    ).all()

    weather = get_weather_assessment()
    budget = calculate_trip_budget(
        db,
        trip,
    )

    pdf_bytes = generate_trip_pdf(
        trip=trip,
        stops=stops,
        legs=legs,
        weather=weather,
        budget=budget,
    )

    filename = (
        trip.name
        .strip()
        .replace(" ", "_")
        .replace("/", "_")
        + ".pdf"
    )

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": (
                f'attachment; filename="{filename}"'
            )
        },
    )

from app.schemas.weather import (
    ReplanResponse,
    TripWeatherImpactResponse,
)
from app.services.transport_service import generate_transport_options
from app.services.weather_service import get_weather_assessment


@router.delete("/{trip_id}")
def delete_trip(
    trip_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    trip = get_user_trip(
        db,
        trip_id,
        user.id,
    )

    db.delete(trip)
    db.commit()

    return {
        "message": "Trip deleted successfully.",
        "trip_id": trip_id,
    }


@router.post("/{trip_id}/stops")
def add_stop(
    trip_id: int,
    data: TripStopAdd,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    trip = get_user_trip(
        db,
        trip_id,
        user.id,
    )

    poi = db.get(POI, data.poi_id)

    if not poi or not poi.is_active:
        raise HTTPException(
            status_code=404,
            detail="Place not found.",
        )

    existing = db.scalar(
        select(TripStop).where(
            TripStop.trip_id == trip.id,
            TripStop.poi_id == poi.id,
        )
    )

    if existing:
        raise HTTPException(
            status_code=400,
            detail="This place is already in the trip.",
        )

    last_sequence = db.scalar(
        select(TripStop.sequence)
        .where(TripStop.trip_id == trip.id)
        .order_by(TripStop.sequence.desc())
        .limit(1)
    )

    next_sequence = (
        (last_sequence + 1)
        if last_sequence is not None
        else 1
    )

    duration = (
        data.duration_minutes
        if data.duration_minutes is not None
        else poi.recommended_duration
    )

    stop = TripStop(
        trip_id=trip.id,
        poi_id=poi.id,
        sequence=next_sequence,
        duration_minutes=duration,
        locked=False,
        entry_cost=poi.entry_fee,
    )

    db.add(stop)

    invalidate_transport_legs(db, trip)
    db.flush()

    recalculate_entry_cost(db, trip)

    db.commit()
    db.refresh(stop)

    return {
        "message": "Place added to trip.",
        "stop_id": stop.id,
        "poi_id": poi.id,
        "poi_name": poi.name,
        "sequence": stop.sequence,
        "duration_minutes": stop.duration_minutes,
        "locked": stop.locked,
        "entry_cost": stop.entry_cost,
        "trip_total_entry_cost": trip.total_entry_cost,
    }


@router.get("/{trip_id}/stops")
def list_stops(
    trip_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    trip = get_user_trip(
        db,
        trip_id,
        user.id,
    )

    stops = db.scalars(
        select(TripStop)
        .where(TripStop.trip_id == trip.id)
        .order_by(TripStop.sequence)
    ).all()

    result = []

    for stop in stops:
        poi = db.get(POI, stop.poi_id)

        if poi:
            result.append(
                {
                    "stop_id": stop.id,
                    "poi_id": poi.id,
                    "poi_name": poi.name,
                    "area": poi.area,
                    "sequence": stop.sequence,
                    "duration_minutes": stop.duration_minutes,
                    "locked": stop.locked,
                    "entry_cost": stop.entry_cost,
                }
            )

    return result


@router.patch("/{trip_id}/stops/{stop_id}")
def update_stop(
    trip_id: int,
    stop_id: int,
    data: TripStopUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    trip = get_user_trip(
        db,
        trip_id,
        user.id,
    )

    stop = db.scalar(
        select(TripStop).where(
            TripStop.id == stop_id,
            TripStop.trip_id == trip.id,
        )
    )

    if not stop:
        raise HTTPException(
            status_code=404,
            detail="Trip stop not found.",
        )

    if data.duration_minutes is not None:
        stop.duration_minutes = data.duration_minutes

    if data.locked is not None:
        stop.locked = data.locked

    db.commit()
    db.refresh(stop)

    return {
        "message": "Trip stop updated.",
        "stop_id": stop.id,
        "duration_minutes": stop.duration_minutes,
        "locked": stop.locked,
    }


@router.delete("/{trip_id}/stops/{stop_id}")
def remove_stop(
    trip_id: int,
    stop_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    trip = get_user_trip(
        db,
        trip_id,
        user.id,
    )

    stop = db.scalar(
        select(TripStop).where(
            TripStop.id == stop_id,
            TripStop.trip_id == trip.id,
        )
    )

    if not stop:
        raise HTTPException(
            status_code=404,
            detail="Trip stop not found.",
        )

    if stop.locked:
        raise HTTPException(
            status_code=400,
            detail="This stop is locked. Unlock it before removing it.",
        )

    removed_sequence = stop.sequence

    db.delete(stop)

    invalidate_transport_legs(db, trip)
    remaining = db.scalars(
        select(TripStop)
        .where(
            TripStop.trip_id == trip.id,
            TripStop.sequence > removed_sequence,
        )
        .order_by(TripStop.sequence)
    ).all()

    for item in remaining:
        item.sequence -= 1

    recalculate_entry_cost(db, trip)

    db.commit()

    return {
        "message": "Place removed from trip.",
        "trip_id": trip.id,
        "removed_stop_id": stop_id,
        "trip_total_entry_cost": trip.total_entry_cost,
    }


@router.put("/{trip_id}/reorder")
def reorder_stops(
    trip_id: int,
    data: TripReorder,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    trip = get_user_trip(
        db,
        trip_id,
        user.id,
    )

    stops = db.scalars(
        select(TripStop).where(
            TripStop.trip_id == trip.id
        )
    ).all()

    existing_ids = {stop.id for stop in stops}

    requested_ids = data.stop_ids

    if len(requested_ids) != len(existing_ids):
        raise HTTPException(
            status_code=400,
            detail="Reorder list must contain every trip stop exactly once.",
        )

    if set(requested_ids) != existing_ids:
        raise HTTPException(
            status_code=400,
            detail="Reorder list contains invalid or missing stop IDs.",
        )

    invalidate_transport_legs(db, trip)

    stop_map = {
        stop.id: stop
        for stop in stops
    }
    for stop in stops:
        stop.sequence = -(stop.sequence + 1)

    db.flush()

    for index, stop_id in enumerate(requested_ids, start=1):
        stop_map[stop_id].sequence = index

    db.commit()

    return {
        "message": "Trip stops reordered.",
        "trip_id": trip.id,
        "stop_ids": requested_ids,
    }