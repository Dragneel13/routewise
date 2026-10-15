from datetime import time

from sqlalchemy import Boolean, Float, Integer, String, Text, Time
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class POI(Base):
    __tablename__ = "pois"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        index=True,
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    category: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    latitude: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    longitude: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    address: Mapped[str] = mapped_column(
        String(300),
        nullable=False,
    )

    area: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    rating: Mapped[float] = mapped_column(
        Float,
        default=4.0,
        nullable=False,
    )

    popularity: Mapped[int] = mapped_column(
        Integer,
        default=50,
        nullable=False,
    )

    entry_fee: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
    )

    recommended_duration: Mapped[int] = mapped_column(
        Integer,
        default=60,
        nullable=False,
    )

    opening_time: Mapped[time | None] = mapped_column(
        Time,
        nullable=True,
    )

    closing_time: Mapped[time | None] = mapped_column(
        Time,
        nullable=True,
    )

    tags: Mapped[str] = mapped_column(
        Text,
        default="",
        nullable=False,
    )

    accessibility: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    image_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    near_metro: Mapped[bool] = mapped_column(
    Boolean,
    default=False,
    nullable=False,
)