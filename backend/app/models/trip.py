from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Trip(Base):
    __tablename__ = "trips"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    start_location: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    budget: Mapped[float] = mapped_column(
        Float,
        default=1000.0,
        nullable=False,
    )

    total_transport_cost: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
    )

    total_entry_cost: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
    )

    total_food_cost: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
    )

    buffer_cost: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
    )

    is_saved: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )


class TripStop(Base):
    __tablename__ = "trip_stops"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    trip_id: Mapped[int] = mapped_column(
        ForeignKey("trips.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    poi_id: Mapped[int] = mapped_column(
        ForeignKey("pois.id"),
        nullable=False,
        index=True,
    )

    sequence: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    duration_minutes: Mapped[int] = mapped_column(
        Integer,
        default=60,
        nullable=False,
    )

    locked: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    entry_cost: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
    )


class TripLeg(Base):
    __tablename__ = "trip_legs"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    trip_id: Mapped[int] = mapped_column(
        ForeignKey("trips.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    from_stop_id: Mapped[int | None] = mapped_column(
        ForeignKey("trip_stops.id", ondelete="CASCADE"),
        nullable=True,
    )

    to_stop_id: Mapped[int | None] = mapped_column(
        ForeignKey("trip_stops.id", ondelete="CASCADE"),
        nullable=True,
    )

    mode: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    option_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    boarding_stop: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    alighting_stop: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    intermediate_stops: Mapped[str] = mapped_column(
        String(500),
        default="",
        nullable=False,
    )

    duration_minutes: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    walking_minutes: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    distance_km: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
    )

    fare: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
    )

    reliability_score: Mapped[float] = mapped_column(
        Float,
        default=0.8,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )