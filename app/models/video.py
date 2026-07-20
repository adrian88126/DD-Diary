from typing import List, Optional
from datetime import date, datetime
from sqlalchemy import String, Date, DateTime, func, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

class Video(Base):
    __tablename__ = "videos"

    video_id: Mapped[str] = mapped_column(String, primary_key=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    published_at: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    video_type: Mapped[str] = mapped_column(String, default="stream_singing")
    thumbnail_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    
    # 新增發布主播外鍵關聯 (一對多)
    vtuber_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("vtubers.id", ondelete="SET NULL"), nullable=True)

    # 關聯關係
    vtuber: Mapped[Optional["VTuber"]] = relationship("VTuber", back_populates="videos")
    singing_records: Mapped[List["SingingRecord"]] = relationship(
        "SingingRecord", back_populates="video", cascade="all, delete-orphan"
    )

    @property
    def has_timeline(self) -> bool:
        return len(self.singing_records) > 0
