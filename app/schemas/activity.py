from pydantic import BaseModel, Field
from typing import Optional
from datetime import date, datetime

class ActivityBase(BaseModel):
    title: str
    description: Optional[str] = None
    event_date: date
    link_url: Optional[str] = None
    activity_type: str = Field(pattern="^(milestone|announcement|x_post|other)$")

class ActivityCreate(ActivityBase):
    vtuber_id: Optional[int] = None

class Activity(ActivityBase):
    id: int
    vtuber_id: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True
