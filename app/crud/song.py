from sqlalchemy.orm import Session
from sqlalchemy import select, or_
from app.models.song import Song
from app.models.artist import Artist
from app.schemas.song import SongCreate

def get_song(db: Session, song_id: int):
    return db.scalars(select(Song).where(Song.id == song_id)).first()

def get_songs(
    db: Session, 
    q: str = None, 
    song_type: str = None, 
    vtuber_id: int = None, 
    is_signature: bool = None, 
    skip: int = 0, 
    limit: int = 100
):
    stmt = select(Song)
    
    # 支援多語系模糊搜尋與羅馬拼音搜尋
    if q:
        stmt = stmt.where(
            or_(
                Song.title_main.ilike(f"%{q}%"),
                Song.title_ja.ilike(f"%{q}%"),
                Song.title_zh.ilike(f"%{q}%"),
                Song.title_romaji.ilike(f"%{q}%")
            )
        )
    
    if song_type:
        stmt = stmt.where(Song.song_type == song_type)
        
    if vtuber_id is not None:
        if is_signature:
            # 過濾特定 VTuber 的常駐拿手歌
            stmt = stmt.where(Song.signature_vtubers.any(id=vtuber_id))
            
    return db.scalars(stmt.offset(skip).limit(limit).order_by(Song.id.desc())).all()

def create_song(db: Session, song: SongCreate):
    db_song = Song(
        title_main=song.title_main,
        title_ja=song.title_ja,
        title_zh=song.title_zh,
        title_romaji=song.title_romaji,
        song_type=song.song_type
    )
    if song.artist_ids:
        # 綁定原唱歌手
        artists = db.scalars(select(Artist).where(Artist.id.in_(song.artist_ids))).all()
        db_song.artists.extend(artists)
        
    db.add(db_song)
    db.commit()
    db.refresh(db_song)
    return db_song

def update_song(db: Session, song_id: int, song: SongCreate):
    db_song = get_song(db, song_id=song_id)
    if not db_song:
        return None
    db_song.title_main = song.title_main
    db_song.title_ja = song.title_ja
    db_song.title_zh = song.title_zh
    db_song.title_romaji = song.title_romaji
    db_song.song_type = song.song_type
    
    # 清空並重新指派原唱歌手
    db_song.artists.clear()
    if song.artist_ids:
        artists = db.scalars(select(Artist).where(Artist.id.in_(song.artist_ids))).all()
        db_song.artists.extend(artists)
        
    db.commit()
    db.refresh(db_song)
    return db_song

def delete_song(db: Session, song_id: int):
    db_song = get_song(db, song_id=song_id)
    if not db_song:
        return False
    db.delete(db_song)
    db.commit()
    return True

