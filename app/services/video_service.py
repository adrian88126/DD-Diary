from typing import Optional
from datetime import date, datetime
from sqlalchemy import select
from app.extensions import db
from app.models.video import Video


def _clean_video_data(data: dict) -> dict:
    cleaned = dict(data)
    cleaned.pop("has_timeline", None)  # 移除非實體欄位，避免 SQLAlchemy 報錯
    if "published_at" in cleaned:
        val = cleaned["published_at"]
        if isinstance(val, str):
            val = val.strip()
            if val:
                val = val.replace("/", "-")
                if "T" in val:
                    val = val.split("T")[0]
                elif " " in val:
                    val = val.split(" ")[0]
                try:
                    cleaned["published_at"] = datetime.strptime(val, "%Y-%m-%d").date()
                except ValueError:
                    cleaned["published_at"] = None
            else:
                cleaned["published_at"] = None
        elif isinstance(val, datetime):
            cleaned["published_at"] = val.date()
    if "vtuber_id" in cleaned:
        vid = cleaned["vtuber_id"]
        if vid == "" or vid is None or str(vid).strip() == "":
            cleaned["vtuber_id"] = None
        else:
            try:
                cleaned["vtuber_id"] = int(vid)
            except (ValueError, TypeError):
                cleaned["vtuber_id"] = None
    return cleaned


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
    cleaned = _clean_video_data(video_data)
    db_video = Video(**cleaned)
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
        cleaned = _clean_video_data(video_data)
        for key, val in cleaned.items():
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
