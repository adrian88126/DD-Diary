from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from app.schemas.link import VTuberLink
from app.schemas.activity import Activity
from app.schemas.song import Song

class VTuberBase(BaseModel):
    name_main: str
    name_ja: Optional[str] = None
    name_zh: Optional[str] = None
    name_romaji: Optional[str] = None
    description: Optional[str] = None
    youtube_channel_id: Optional[str] = None
    avatar_url: Optional[str] = None
    theme_color: Optional[str] = None
    banner_url: Optional[str] = None
    social_links: Optional[str] = None
    schedule_image_url: Optional[str] = None

class VTuberCreate(VTuberBase):
    pass

class VTuber(VTuberBase):
    id: int
    created_at: datetime
    links: List[VTuberLink] = []
    activities: List[Activity] = []
    signature_songs: List[Song] = []
    requestable_songs: List[Song] = [] # 點歌歌單列表

    class Config:
        from_attributes = True

class VTuberPlaylistBatch(BaseModel):
    raw_lines: List[str]
    association_type: str = "requestable"
