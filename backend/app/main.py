from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import Base, engine, get_db
from app.models.user import User
from app.routers.auth import router as auth_router
from app.routers.profile import router as profile_router
from app.routers.pois import router as pois_router
from app.routers.recommendations import (router as recommendations_router,)
from app.routers.friends import router as friends_router
from app.routers.trips import router as trips_router
from app.routers.transport import router as transport_router
from app.routers.weather import router as weather_router

Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="RouteWise API",
    description="Pune Smart Trip Planner API",
    version="1.0.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth_router)
app.include_router(profile_router)
app.include_router(pois_router)
app.include_router( recommendations_router)
app.include_router(friends_router)
app.include_router(trips_router)
app.include_router(transport_router)
app.include_router(weather_router)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "RouteWise API",
    }


@app.get("/health/db")
def health_db(db: Session = Depends(get_db)):
    postgres = db.execute(
        text("SELECT version()")
    ).scalar()

    postgis = db.execute(
        text("SELECT postgis_version()")
    ).scalar()

    return {
        "postgres": postgres,
        "postgis": postgis,
    }

