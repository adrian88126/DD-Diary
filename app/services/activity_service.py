from sqlalchemy import select
from app.extensions import db
from app.models.activity import Activity
from datetime import date

def get_activities(
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
    return db.session.scalars(stmt.offset(skip).limit(limit).order_by(Activity.event_date.desc())).all()

def create_activity(activity_data: dict):
    db_activity = Activity(**activity_data)
    db.session.add(db_activity)
    db.session.commit()
    db.session.refresh(db_activity)
    return db_activity

def get_activity(activity_id: int):
    return db.session.scalars(select(Activity).where(Activity.id == activity_id)).first()

def update_activity(activity_id: int, activity_data: dict):
    db_activity = get_activity(activity_id)
    if db_activity:
        for key, val in activity_data.items():
            setattr(db_activity, key, val)
        db.session.commit()
        db.session.refresh(db_activity)
    return db_activity

def delete_activity(activity_id: int) -> bool:
    db_activity = get_activity(activity_id)
    if db_activity:
        db.session.delete(db_activity)
        db.session.commit()
        return True
    return False
