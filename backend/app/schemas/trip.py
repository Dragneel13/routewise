from pydantic import BaseModel, Field


class TripCreate(BaseModel):
    name: str = Field(min_length=2, max_length=150)
    start_location: str = Field(min_length=2, max_length=150)
    budget: float = Field(default=1000.0, ge=0)


class TripStopAdd(BaseModel):
    poi_id: int
    duration_minutes: int | None = Field(default=None, ge=1)


class TripStopUpdate(BaseModel):
    duration_minutes: int | None = Field(default=None, ge=1)
    locked: bool | None = None


class TripReorder(BaseModel):
    stop_ids: list[int]


class TripResponse(BaseModel):
    id: int
    name: str
    start_location: str
    budget: float
    total_transport_cost: float
    total_entry_cost: float
    total_food_cost: float
    buffer_cost: float
    is_saved: bool

    model_config = {
        "from_attributes": True
    }


class TripBudgetResponse(BaseModel):
    trip_id: int
    budget: float
    total_transport_cost: float
    total_entry_cost: float
    total_food_cost: float
    buffer_cost: float
    estimated_total: float
    remaining_budget: float
    budget_used_percent: float
    budget_status: str
    suggestion: str | None = None

class TripShareResponse(BaseModel):
    trip_id: int
    share_token: str
    share_url: str


class SharedTripStopResponse(BaseModel):
    sequence: int
    poi_name: str
    area: str
    duration_minutes: int
    entry_cost: float


class SharedTripResponse(BaseModel):
    trip_id: int
    name: str
    start_location: str
    budget: float
    total_transport_cost: float
    total_entry_cost: float
    total_food_cost: float
    buffer_cost: float
    stops: list[SharedTripStopResponse]