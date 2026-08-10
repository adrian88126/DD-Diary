from typing import Optional
from datetime import date
from sqlalchemy import select
from app.extensions import db
from app.models.video import Video

def get_video(video_id: str):
    return db.session.scalars(select(Video).where(Video.video_id == video_id)).first()

def get_videos(video_type: str = None, vtuber_id: int = None, skip: int = 0, limit: int = 100):
    stmt = select(Video)
    if video_type:
        stmt = stmt.where(Video.video_type == video_type)
    if vtuber_id:
        stmt = stmt.where(Video.vtuber_id == vtuber_id)
    return db.session.scalars(stmt.offset(skip).limit(limit).order_by(Video.published_at.desc())).all()

def create_video(video_data: dict):
    video_data.pop("has_timeline", None) # 移除非實體欄位，避免 SQLAlchemy 報錯
    db_video = Video(**video_data)
    db.session.add(db_video)
    db.session.commit()
    db.session.refresh(db_video)
    return db_video

def update_video_type(video_id: str, video_type: str):
    db_video = get_video(video_id)
    if db_video:
        db_video.video_type = video_type
        db.session.commit()
        db.session.refresh(db_video)
    return db_video

def update_video(video_id: str, video_data: dict):
    db_video = get_video(video_id)
    if db_video:
        for key, val in video_data.items():
            setattr(db_video, key, val)
        db.session.commit()
        db.session.refresh(db_video)
    return db_video

def delete_video(video_id: str) -> bool:
    db_video = get_video(video_id=video_id)
    if db_video:
        db.session.delete(db_video)
        db.session.commit()
        return True
    return False
