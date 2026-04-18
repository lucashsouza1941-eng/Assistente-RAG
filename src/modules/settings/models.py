from datetime import datetime
from typing import Any

from sqlalchemy import String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.db.base import Base


class Setting(Base):
    __tablename__ = 'settings'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    key: Mapped[str] = mapped_column(String(100), unique=True)
    value: Mapped[dict[str, Any]] = mapped_column(JSONB)
    category: Mapped[str] = mapped_column(String(50))
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())
