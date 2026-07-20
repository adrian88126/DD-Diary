from typing import List, Optional
from datetime import datetime
from sqlalchemy import String, Integer, ForeignKey, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.models.association import record_vtubers

class SingingRecord(Base):
    __tablename__ = "singing_records"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    song_id: Mapped[int] = mapped_column(Integer, ForeignKey("songs.id", ondelete="CASCADE"), nullable=False)
    video_id: Mapped[str] = mapped_column(String(11), ForeignKey("videos.video_id", ondelete="CASCADE"), nullable=False)
    timestamp_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    note: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # 關聯關係
    song: Mapped["Song"] = relationship("Song", back_populates="singing_records")
    video: Mapped["Video"] = relationship("Video", back_populates="singing_records")
    singers: Mapped[List["VTuber"]] = relationship(
        "VTuber", secondary=record_vtubers, back_populates="singing_records"
    )
