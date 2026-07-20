from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models.activity import Activity
from app.schemas.activity import ActivityCreate
from datetime import date

def get_activities(
    db: Session,
    vtuber_id: int = None,
    start_date: date = None,
    end_date: date = None,
    activity_type: str = None,
    skip: int = 0,
    limit: int = 100
):
    stmt = select(Activity)
    if vtuber_id is not None:
        stmt = stmt.where(Activity.vtuber_id == vtuber_id)
    if start_date:
        stmt = stmt.where(Activity.event_date >= start_date)
    if end_date:
        stmt = stmt.where(Activity.event_date <= end_date)
    if activity_type:
        stmt = stmt.where(Activity.activity_type == activity_type)
    return db.scalars(stmt.offset(skip).limit(limit).order_by(Activity.event_date.desc())).all()

def create_activity(db: Session, activity: ActivityCreate):
    db_activity = Activity(**activity.model_dump())
    db.add(db_activity)
    db.commit()
    db.refresh(db_activity)
    return db_activity

def get_activity(db: Session, activity_id: int):
    return db.scalars(select(Activity).where(Activity.id == activity_id)).first()

def update_activity(
    db: Session,
    activity_id: int,
    title: str,
    event_date: date,
    activity_type: str,
    link_url: str = None,
    description: str = None,
    vtuber_id: int = None
):
    db_activity = get_activity(db, activity_id)
    if db_activity:
        db_activity.title = title
        db_activity.event_date = event_date
        db_activity.activity_type = activity_type
        db_activity.link_url = link_url
        db_activity.description = description
        db_activity.vtuber_id = vtuber_id
        db.commit()
        db.refresh(db_activity)
    return db_activity

def delete_activity(db: Session, activity_id: int) -> bool:
    db_activity = get_activity(db, activity_id)
    if db_activity:
        db.delete(db_activity)
        db.commit()
        return True
    return False
