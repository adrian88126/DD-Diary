from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from app.schemas.song import Song
from app.schemas.video import Video

class VTuberSimple(BaseModel):
    id: int
    name_main: str
    name_ja: Optional[str] = None
    name_zh: Optional[str] = None
    name_romaji: Optional[str] = None
    youtube_channel_id: Optional[str] = None

    class Config:
        from_attributes = True

class SingingRecordBase(BaseModel):
    song_id: int
    video_id: str
    timestamp_seconds: int = 0
    note: Optional[str] = None

class SingingRecordCreate(SingingRecordBase):
    singer_ids: List[int] = [] # 參與演唱的主播 VTuber ID 列表

class SingingRecord(SingingRecordBase):
    id: int
    created_at: datetime
    song: Song
    video: Video
    singers: List[VTuberSimple] = []

    class Config:
        from_attributes = True

# 批量匯入專用項目校驗模型
class BatchRecordItem(BaseModel):
    song_title: str
    video_id: str
    timestamp_seconds: int = 0
    singers: List[str] # 演唱主播的主顯示名字列表 (如 ["滔滔饕餮"])
    note: Optional[str] = None
    song_type: Optional[str] = "cover" # 若自動創建新歌時的歌曲類型 (cover 或 original)
