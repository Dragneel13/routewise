from pydantic import BaseModel


class WeatherResponse(BaseModel):
    available: bool
    city: str | None = None
    temperature_c: float | None = None
    humidity_percent: float | None = None
    precipitation_mm: float | None = None
    wind_speed_kmh: float | None = None
    weather_code: int | None = None
    description: str | None = None
    weather_risk: str | None = None
    walking_warning: bool = False
    recommendation: str | None = None
    source: str | None = None
    error: str | None = None

class TripWeatherImpactResponse(BaseModel):
    trip_id: int
    weather_risk: str
    walking_warning: bool
    walking_penalty: float
    current_walking_minutes: int
    recommended_mode: str
    replan_recommended: bool
    message: str

class ReplanLegResponse(BaseModel):
    from_stop_id: int
    to_stop_id: int
    from_poi: str
    to_poi: str
    mode: str
    option_type: str
    duration_minutes: int
    walking_minutes: int
    distance_km: float
    fare: float
    weather_adjusted_score: float


class ReplanResponse(BaseModel):
    trip_id: int
    weather_risk: str
    replan_reason: str
    legs: list[ReplanLegResponse]
    total_transport_cost: float
    message: str