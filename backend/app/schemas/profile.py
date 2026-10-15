from typing import Literal

from pydantic import BaseModel, Field


class ProfileUpdate(BaseModel):
    interests: list[str] = Field(default_factory=list)

    budget_style: Literal[
        "budget",
        "mid",
        "comfort",
    ] = "mid"

    preferred_transport: Literal[
        "Bus",
        "Metro",
        "Auto",
        "Walk",
    ] = "Bus"

    home_area: str = "Pune Station"

    share_checkins: bool = True


class ProfileResponse(ProfileUpdate):
    id: int
    name: str
    email: str