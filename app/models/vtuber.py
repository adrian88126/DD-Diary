from typing import List, Optional
from datetime import datetime
from sqlalchemy import String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.models.association import vtuber_songs, record_vtubers

class VTuber(Base):
    __tablename__ = "vtubers"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name_main: Mapped[str] = mapped_column(String, nullable=False)
    name_ja: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    name_zh: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    name_romaji: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    youtube_channel_id: Mapped[Optional[str]] = mapped_column(String, unique=True, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    avatar_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    theme_color: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    banner_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    social_links: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    schedule_image_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    # 關聯關係
    links: Mapped[List["VTuberLink"]] = relationship(
        "VTuberLink", back_populates="vtuber", cascade="all, delete-orphan"
    )
    activities: Mapped[List["Activity"]] = relationship(
        "Activity", back_populates="vtuber", cascade="all, delete-orphan"
    )
    
    # 新增影片與直播一對多關聯
    videos: Mapped[List["Video"]] = relationship(
        "Video", back_populates="vtuber", cascade="all, delete-orphan"
    )
    
    # 拆分常駐歌單與點歌歌單
    signature_songs: Mapped[List["Song"]] = relationship(
        "Song", 
        secondary=vtuber_songs, 
        primaryjoin="and_(VTuber.id==vtuber_songs.c.vtuber_id, vtuber_songs.c.association_type=='signature')",
        back_populates="signature_vtubers",
        overlaps="requestable_songs,requestable_vtubers"
    )
    requestable_songs: Mapped[List["Song"]] = relationship(
        "Song",
        secondary=vtuber_songs,
        primaryjoin="and_(VTuber.id==vtuber_songs.c.vtuber_id, vtuber_songs.c.association_type=='requestable')",
        back_populates="requestable_vtubers",
        overlaps="signature_songs,signature_vtubers"
    )
    
    singing_records: Mapped[List["SingingRecord"]] = relationship(
        "SingingRecord", secondary=record_vtubers, back_populates="singers"
    )
