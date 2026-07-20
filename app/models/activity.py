from typing import Optional
from datetime import datetime, date
from sqlalchemy import String, Integer, ForeignKey, Date, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

class Activity(Base):
    __tablename__ = "activities"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    vtuber_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("vtubers.id", ondelete="CASCADE"), nullable=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    event_date: Mapped[date] = mapped_column(Date, nullable=False)
    link_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    activity_type: Mapped[str] = mapped_column(String, nullable=False) # CHECK is handled at DB level, but we enforce it in schemas too
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # 關聯至 VTuber
    vtuber: Mapped[Optional["VTuber"]] = relationship("VTuber", back_populates="activities")
