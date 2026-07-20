from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models.record import SingingRecord
from app.models.vtuber import VTuber
from app.schemas.record import SingingRecordCreate

def get_record(db: Session, record_id: int):
    return db.scalars(select(SingingRecord).where(SingingRecord.id == record_id)).first()

def get_records(
    db: Session,
    vtuber_id: int = None,
    video_id: str = None,
    song_id: int = None,
    skip: int = 0,
    limit: int = 100
):
    stmt = select(SingingRecord)
    
    if vtuber_id is not None:
        # 過濾包含該位 VTuber 的演唱紀錄 (包括獨唱與合唱)
        stmt = stmt.where(SingingRecord.singers.any(id=vtuber_id))
    if video_id is not None:
        stmt = stmt.where(SingingRecord.video_id == video_id)
    if song_id is not None:
        stmt = stmt.where(SingingRecord.song_id == song_id)
        
    return db.scalars(stmt.offset(skip).limit(limit).order_by(SingingRecord.id.desc())).all()

def create_record(db: Session, record: SingingRecordCreate):
    db_record = SingingRecord(
        song_id=record.song_id,
        video_id=record.video_id,
        timestamp_seconds=record.timestamp_seconds,
        note=record.note
    )
    if record.singer_ids:
        # 綁定參與合唱的主播
        singers = db.scalars(select(VTuber).where(VTuber.id.in_(record.singer_ids))).all()
        db_record.singers.extend(singers)
        
    db.add(db_record)
    db.commit()
    db.refresh(db_record)
    return db_record

def update_record(
    db: Session,
    record_id: int,
    song_id: int,
    video_id: str,
    timestamp_seconds: int,
    note: str = None,
    singer_ids: list = None
):
    db_record = get_record(db, record_id=record_id)
    if db_record:
        db_record.song_id = song_id
        db_record.video_id = video_id
        db_record.timestamp_seconds = timestamp_seconds
        db_record.note = note
        
        # 更新多對多歌手關聯
        if singer_ids is not None:
            db_record.singers.clear()
            singers = db.scalars(select(VTuber).where(VTuber.id.in_(singer_ids))).all()
            db_record.singers.extend(singers)
            
        db.commit()
        db.refresh(db_record)
    return db_record

def delete_record(db: Session, record_id: int) -> bool:
    db_record = get_record(db, record_id=record_id)
    if db_record:
        db.delete(db_record)
        db.commit()
        return True
    return False
