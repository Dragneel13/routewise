from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )

    password_hash: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    bio: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    interests: Mapped[str] = mapped_column(
        Text,
        default="",
        nullable=False,
    )

    budget_style: Mapped[str] = mapped_column(
        String(20),
        default="mid",
        nullable=False,
    )

    preferred_transport: Mapped[str] = mapped_column(
        String(20),
        default="Bus",
        nullable=False,
    )

    home_area: Mapped[str] = mapped_column(
        String(60),
        default="Pune Station",
        nullable=False,
    )

    share_checkins: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )