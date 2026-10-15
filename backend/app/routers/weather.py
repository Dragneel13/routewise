from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.routers.auth import get_current_user
from app.schemas.weather import WeatherResponse
from app.services.weather_service import get_weather_assessment


router = APIRouter(
    prefix="/weather",
    tags=["Weather"],
)


@router.get(
    "/pune",
    response_model=WeatherResponse,
)
def get_pune_weather(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return get_weather_assessment()