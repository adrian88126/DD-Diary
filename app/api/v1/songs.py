from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.schemas.song import Song, SongCreate
from app.crud.song import get_song, get_songs, create_song, update_song, delete_song

router = APIRouter()

@router.get("/", response_model=List[Song])
def read_songs(
    q: Optional[str] = Query(None, description="模糊搜尋歌名（支援中文、日文、拼音等）"),
    song_type: Optional[str] = Query(None, description="原創或翻唱篩選 (original/cover)"),
    vtuber_id: Optional[int] = Query(None, description="篩選特定 VTuber 關聯的歌曲"),
    is_signature: Optional[bool] = Query(None, description="是否僅篩選該 VTuber 的常駐拿手歌單（需提供 vtuber_id）"),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    return get_songs(
        db, q=q, song_type=song_type, vtuber_id=vtuber_id, 
        is_signature=is_signature, skip=skip, limit=limit
    )

@router.get("/{song_id}", response_model=Song)
def read_song(song_id: int, db: Session = Depends(get_db)):
    db_song = get_song(db, song_id=song_id)
    if not db_song:
        raise HTTPException(status_code=404, detail="Song not found")
    return db_song

@router.post("/", response_model=Song)
def create_new_song(song: SongCreate, db: Session = Depends(get_db)):
    return create_song(db=db, song=song)

@router.put("/{song_id}", response_model=Song)
def update_existing_song(song_id: int, song: SongCreate, db: Session = Depends(get_db)):
    db_song = update_song(db=db, song_id=song_id, song=song)
    if not db_song:
        raise HTTPException(status_code=404, detail="Song not found")
    return db_song

@router.delete("/{song_id}")
def delete_existing_song(song_id: int, db: Session = Depends(get_db)):
    success = delete_song(db=db, song_id=song_id)
    if not success:
        raise HTTPException(status_code=404, detail="Song not found")
    return {"message": "Song deleted successfully"}

