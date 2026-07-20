from typing import List, Optional
from datetime import datetime
from sqlalchemy import String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.models.association import song_artists, vtuber_songs

class Song(Base):
    __tablename__ = "songs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title_main: Mapped[str] = mapped_column(String, nullable=False)
    title_ja: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    title_zh: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    title_romaji: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    song_type: Mapped[str] = mapped_column(String, default="cover")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    # 關聯關係
    artists: Mapped[List["Artist"]] = relationship(
        "Artist", secondary=song_artists, back_populates="songs"
    )
    
    # 關聯至常駐與點歌的 VTubers
    signature_vtubers: Mapped[List["VTuber"]] = relationship(
        "VTuber", 
        secondary=vtuber_songs, 
        primaryjoin="and_(Song.id==vtuber_songs.c.song_id, vtuber_songs.c.association_type=='signature')",
        back_populates="signature_songs",
        overlaps="requestable_songs,requestable_vtubers"
    )
    requestable_vtubers: Mapped[List["VTuber"]] = relationship(
        "VTuber", 
        secondary=vtuber_songs, 
        primaryjoin="and_(Song.id==vtuber_songs.c.song_id, vtuber_songs.c.association_type=='requestable')",
        back_populates="requestable_songs",
        overlaps="signature_songs,signature_vtubers"
    )
    
    singing_records: Mapped[List["SingingRecord"]] = relationship(
        "SingingRecord", back_populates="song", cascade="all, delete-orphan"
    )
