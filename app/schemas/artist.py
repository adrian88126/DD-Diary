from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ArtistBase(BaseModel):
    name_main: str
    name_ja: Optional[str] = None
    name_zh: Optional[str] = None
    name_romaji: Optional[str] = None

class ArtistCreate(ArtistBase):
    pass

class Artist(ArtistBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
