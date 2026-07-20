from typing import List, Optional
from datetime import datetime
from sqlalchemy import String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.models.association import song_artists

class Artist(Base):
    __tablename__ = "artists"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name_main: Mapped[str] = mapped_column(String, nullable=False)
    name_ja: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    name_zh: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    name_romaji: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # 關聯關係：歌手與歌曲的多對多關係
    songs: Mapped[List["Song"]] = relationship(
        "Song", secondary=song_artists, back_populates="artists"
    )
