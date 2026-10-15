from pydantic import BaseModel


class RecommendationResponse(BaseModel):
    poi_id: int
    name: str
    category: str
    area: str
    description: str
    rating: float
    popularity: int
    entry_fee: float
    recommended_duration: int
    tags: str
    near_metro: bool

    friend_score: float
    interest_match: float
    popularity_score: float
    context_score: float
    recommendation_score: float