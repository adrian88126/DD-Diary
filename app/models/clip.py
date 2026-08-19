from typing import List, Optional
from datetime import datetime, date
from sqlalchemy import String, DateTime, Date, Text, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.extensions import db
from app.models.association import clip_vtubers

class ClipAuthor(db.Model):
    __tablename__ = "clip_authors"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    youtube_channel_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    channel_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    clips: Mapped[List["Clip"]] = relationship("Clip", back_populates="author")


class Clip(db.Model):
    __tablename__ = "clips"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    video_id: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    tags: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    published_at: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    author_id: Mapped[Optional[int]] = mapped_column(ForeignKey("clip_authors.id", ondelete="SET NULL"), nullable=True)
    song_id: Mapped[Optional[int]] = mapped_column(ForeignKey("songs.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    author: Mapped[Optional["ClipAuthor"]] = relationship("ClipAuthor", back_populates="clips")
    song: Mapped[Optional["Song"]] = relationship("Song")
    vtubers: Mapped[List["VTuber"]] = relationship("VTuber", secondary=clip_vtubers)

    @property
    def thumbnail_url(self) -> str:
        if self.video_id:
            return f"https://img.youtube.com/vi/{self.video_id}/mqdefault.jpg"
        return ""
