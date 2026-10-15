from datetime import time

from pydantic import BaseModel


class POIResponse(BaseModel):
    id: int
    name: str
    description: str
    category: str
    latitude: float
    longitude: float
    address: str
    area: str
    rating: float
    popularity: int
    entry_fee: float
    recommended_duration: int
    opening_time: time | None = None
    closing_time: time | None = None
    tags: str
    near_metro: bool

    model_config = {
        "from_attributes": True,
    }