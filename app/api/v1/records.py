from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import List, Optional
from app.database import get_db
from app.schemas.record import SingingRecord, SingingRecordCreate, BatchRecordItem
from app.crud.record import get_record, get_records, create_record, delete_record, update_record
from app.models.song import Song
from app.models.video import Video
from app.models.vtuber import VTuber
from app.models.record import SingingRecord as DBSingingRecord

router = APIRouter()

@router.get("/", response_model=List[SingingRecord])
def read_records(
    vtuber_id: Optional[int] = Query(None, description="篩選特定 VTuber 的演唱紀錄"),
    video_id: Optional[str] = Query(None, description="篩選特定影片中的演唱紀錄"),
    song_id: Optional[int] = Query(None, description="篩選特定歌曲的歷史演唱紀錄"),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    return get_records(
        db, vtuber_id=vtuber_id, video_id=video_id, 
        song_id=song_id, skip=skip, limit=limit
    )

@router.post("/", response_model=SingingRecord)
def create_new_record(record: SingingRecordCreate, db: Session = Depends(get_db)):
    return create_record(db=db, record=record)

@router.post("/batch", response_model=List[SingingRecord])
def create_records_batch(items: List[BatchRecordItem], db: Session = Depends(get_db)):
    """
    批量匯入演唱紀錄 (含 Auto-Resolution 自動關聯與建檔機制)
    - 歌曲找不到 -> 自動建立 Song
    - 直播影片找不到 -> 自動建立 Video
    - 主播找不到 -> 自動建立 VTuber
    """
    results = []
    
    for item in items:
        # 1. 尋找或建立歌曲
        song = db.scalars(select(Song).where(Song.title_main == item.song_title)).first()
        if not song:
            song = Song(
                title_main=item.song_title,
                title_romaji=item.song_title.lower(),
                song_type=item.song_type or "cover"
            )
            db.add(song)
            db.flush()
            
        # 2. 尋找或建立影音檔
        video = db.scalars(select(Video).where(Video.video_id == item.video_id)).first()
        if not video:
            # 如果時間軸為 0 則預設為 cover_mv
            v_type = "cover_mv" if item.timestamp_seconds == 0 else "stream_singing"
            video = Video(
                video_id=item.video_id,
                title=f"Imported Video {item.video_id}",
                video_type=v_type,
                published_at=None
            )
            db.add(video)
            db.flush()
            
        # 3. 尋找或建立 VTubers 演唱主播
        vtubers = []
        for name in item.singers:
            vt = db.scalars(select(VTuber).where(VTuber.name_main == name)).first()
            if not vt:
                vt = VTuber(
                    name_main=name,
                    name_romaji=name.lower(),
                    description="透過批量上傳自動建立的主播資料。"
                )
                db.add(vt)
                db.flush()
            vtubers.append(vt)
            
        # 4. 建立演唱紀錄並綁定多對多演唱者
        db_record = DBSingingRecord(
            song_id=song.id,
            video_id=video.video_id,
            timestamp_seconds=item.timestamp_seconds,
            note=item.note
        )
        db_record.singers.extend(vtubers)
        db.add(db_record)
        db.flush()
        
        results.append(db_record)
        
    db.commit()
    
    # 用生成的 IDs 重新讀取完整的關聯資料，確保 Pydantic 關係輸出正確
    ids = [r.id for r in results]
    refreshed_results = db.scalars(select(DBSingingRecord).where(DBSingingRecord.id.in_(ids))).all()
    return refreshed_results

@router.delete("/{record_id}")
def delete_existing_record(record_id: int, db: Session = Depends(get_db)):
    success = delete_record(db=db, record_id=record_id)
    if not success:
        raise HTTPException(status_code=404, detail="Record not found")
    return {"message": "Record deleted successfully"}

@router.put("/{record_id}", response_model=SingingRecord)
def update_existing_record(record_id: int, record: SingingRecordCreate, db: Session = Depends(get_db)):
    db_record = update_record(
        db=db,
        record_id=record_id,
        song_id=record.song_id,
        video_id=record.video_id,
        timestamp_seconds=record.timestamp_seconds,
        note=record.note,
        singer_ids=record.singer_ids
    )
    if not db_record:
        raise HTTPException(status_code=404, detail="Record not found")
    return db_record
