from typing import Optional
from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models.video import Video
from app.schemas.video import VideoCreate

def get_video(db: Session, video_id: str):
    return db.scalars(select(Video).where(Video.video_id == video_id)).first()

def get_videos(db: Session, video_type: str = None, vtuber_id: int = None, skip: int = 0, limit: int = 100):
    stmt = select(Video)
    if video_type:
        stmt = stmt.where(Video.video_type == video_type)
    if vtuber_id:
        stmt = stmt.where(Video.vtuber_id == vtuber_id)
    return db.scalars(stmt.offset(skip).limit(limit).order_by(Video.published_at.desc())).all()

def create_video(db: Session, video: VideoCreate):
    dump_data = video.model_dump()
    dump_data.pop("has_timeline", None) # 移除非實體欄位，避免 SQLAlchemy 報錯
    db_video = Video(**dump_data)
    db.add(db_video)
    db.commit()
    db.refresh(db_video)
    return db_video

def update_video_type(db: Session, video_id: str, video_type: str):
    db_video = get_video(db, video_id)
    if db_video:
        db_video.video_type = video_type
        db.commit()
        db.refresh(db_video)
    return db_video

def update_video(db: Session, video_id: str, title: str, published_at: Optional[date], video_type: str, thumbnail_url: Optional[str], vtuber_id: Optional[int]):
    db_video = get_video(db, video_id)
    if db_video:
        db_video.title = title
        db_video.published_at = published_at
        db_video.video_type = video_type
        db_video.thumbnail_url = thumbnail_url
        db_video.vtuber_id = vtuber_id
        db.commit()
        db.refresh(db_video)
    return db_video

def delete_video(db: Session, video_id: str) -> bool:
    db_video = get_video(db, video_id=video_id)
    if db_video:
        db.delete(db_video)
        db.commit()
        return True
    return False
