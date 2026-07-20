from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from app.schemas.artist import Artist

class SongBase(BaseModel):
    title_main: str
    title_ja: Optional[str] = None
    title_zh: Optional[str] = None
    title_romaji: Optional[str] = None
    song_type: str = Field(default="cover", pattern="^(original|cover)$")

class SongCreate(SongBase):
    artist_ids: List[int] = [] # 新增歌曲時關聯的原唱歌手 ID 清單

class Song(SongBase):
    id: int
    created_at: datetime
    updated_at: datetime
    artists: List[Artist] = []

    class Config:
        from_attributes = True
