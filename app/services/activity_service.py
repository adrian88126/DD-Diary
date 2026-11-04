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

def _clean_activity_data(data: dict) -> dict:
    cleaned = dict(data)
    # 處理 event_date: 字串轉 datetime.date 物件
    if 'event_date' in cleaned:
        val = cleaned['event_date']
        if isinstance(val, str):
            val = val.strip()
            if val:
                from datetime import datetime
                val = val.replace('/', '-')
                if 'T' in val:
                    val = val.split('T')[0]
                cleaned['event_date'] = datetime.strptime(val, '%Y-%m-%d').date()
            else:
                from datetime import date
                cleaned['event_date'] = date.today()
        elif hasattr(val, 'date') and not isinstance(val, date):
            cleaned['event_date'] = val.date()

    # 處理 vtuber_id
    if 'vtuber_id' in cleaned:
        vid = cleaned['vtuber_id']
        if vid == '' or vid is None or str(vid).strip() == '':
            cleaned['vtuber_id'] = None
        else:
            try:
                cleaned['vtuber_id'] = int(vid)
            except (ValueError, TypeError):
                cleaned['vtuber_id'] = None

    # 清除空字串為 None
    for field in ['description', 'link_url']:
        if field in cleaned and cleaned[field] == '':
            cleaned[field] = None

    return cleaned

def create_activity(activity_data: dict):
    cleaned = _clean_activity_data(activity_data)
    db_activity = Activity(**cleaned)
    db.session.add(db_activity)
    db.session.commit()
    db.session.refresh(db_activity)
    return db_activity

def get_activity(activity_id: int):
    return db.session.scalars(select(Activity).where(Activity.id == activity_id)).first()

def update_activity(activity_id: int, activity_data: dict):
    db_activity = get_activity(activity_id)
    if db_activity:
        cleaned = _clean_activity_data(activity_data)
        for key, val in cleaned.items():
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
