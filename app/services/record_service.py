from sqlalchemy import select
from app.extensions import db
from app.models.record import SingingRecord
from app.models.vtuber import VTuber
from app.models.song import Song
from sqlalchemy import func

def get_record(record_id: int):
    return db.session.scalars(select(SingingRecord).where(SingingRecord.id == record_id)).first()

def get_records(
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
        
    return db.session.scalars(stmt.offset(skip).limit(limit).order_by(SingingRecord.id.desc())).all()

def create_record(record_data: dict):
    singer_ids = record_data.pop('singer_ids', [])
    db_record = SingingRecord(**record_data)
    
    if singer_ids:
        # 綁定參與合唱的主播
        singers = db.session.scalars(select(VTuber).where(VTuber.id.in_(singer_ids))).all()
        db_record.singers.extend(singers)
        
    db.session.add(db_record)
    db.session.commit()
    db.session.refresh(db_record)
    return db_record

def update_record(record_id: int, record_data: dict):
    db_record = get_record(record_id=record_id)
    if db_record:
        singer_ids = record_data.pop('singer_ids', None)
        
        for key, val in record_data.items():
            setattr(db_record, key, val)
        
        # 更新多對多歌手關聯
        if singer_ids is not None:
            db_record.singers.clear()
            if singer_ids:
                singers = db.session.scalars(select(VTuber).where(VTuber.id.in_(singer_ids))).all()
                db_record.singers.extend(singers)
            
        db.session.commit()
        db.session.refresh(db_record)
    return db_record

def delete_record(record_id: int) -> bool:
    db_record = get_record(record_id=record_id)
    if db_record:
        db.session.delete(db_record)
        db.session.commit()
        return True
    return False

def batch_create_timeline(video_id: str, items: list, singer_ids: list = None):
    created_count = 0
    
    for item in items:
        title = item.get("title", "").strip()
        timestamp = item.get("timestamp_seconds")
        
        if not title or timestamp is None:
            continue
            
        # 尋找歌曲，忽略大小寫
        db_song = db.session.scalars(
            select(Song).where(func.lower(Song.title_main) == title.lower())
        ).first()
        
        # 若無該首歌曲，自動新增
        if not db_song:
            db_song = Song(title_main=title, song_type="cover")
            db.session.add(db_song)
            db.session.flush() # 取得新增後的 ID
            
        # 檢查是否已經有同秒數的紀錄
        existing_record = db.session.scalars(
            select(SingingRecord).where(
                SingingRecord.video_id == video_id,
                SingingRecord.song_id == db_song.id,
                SingingRecord.timestamp_seconds == timestamp
            )
        ).first()
        
        if not existing_record:
            new_record = SingingRecord(
                video_id=video_id,
                song_id=db_song.id,
                timestamp_seconds=timestamp
            )
            
            if singer_ids:
                singers = db.session.scalars(select(VTuber).where(VTuber.id.in_(singer_ids))).all()
                new_record.singers.extend(singers)
                
            db.session.add(new_record)
            created_count += 1
            
    db.session.commit()
    return created_count
