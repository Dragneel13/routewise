from pydantic import BaseModel


class TransportOption(BaseModel):
    mode: str
    option_type: str

    duration_minutes: int
    walking_minutes: int
    distance_km: float
    fare: float

    boarding_stop: str | None = None
    alighting_stop: str | None = None
    intermediate_stops: list[str] = []

    reliability_score: float

    last_mile_distance_km: float = 0.0
    last_mile_minutes: int = 0


class TransportOptionsResponse(BaseModel):
    trip_id: int
    from_stop_id: int
    to_stop_id: int
    from_poi: str
    to_poi: str
    options: list[TransportOption]

class TransportSelection(BaseModel):
    mode: str
    option_type: str