from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime

class VideoBase(BaseModel):
    video_id: str
    title: str
    published_at: Optional[date] = None
    video_type: Optional[str] = "stream_singing"
    thumbnail_url: Optional[str] = None
    vtuber_id: Optional[int] = None # 歸屬的主播 ID
    has_timeline: Optional[bool] = False # 新增：標記是否有時間軸紀錄

class VideoCreate(VideoBase):
    pass

class Video(VideoBase):
    created_at: datetime

    class Config:
        from_attributes = True
