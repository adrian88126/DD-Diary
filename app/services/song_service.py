from sqlalchemy import select, or_
from app.extensions import db
from app.models.song import Song
from app.models.artist import Artist

def get_song(song_id: int):
    return db.session.scalars(select(Song).where(Song.id == song_id)).first()

def get_songs(
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
            
    return db.session.scalars(stmt.offset(skip).limit(limit).order_by(Song.id.desc())).all()

def create_song(song_data: dict):
    artist_ids = song_data.pop('artist_ids', [])
    db_song = Song(**song_data)
    
    if artist_ids:
        # 綁定原唱歌手
        artists = db.session.scalars(select(Artist).where(Artist.id.in_(artist_ids))).all()
        db_song.artists.extend(artists)
        
    db.session.add(db_song)
    db.session.commit()
    db.session.refresh(db_song)
    return db_song

def update_song(song_id: int, song_data: dict):
    db_song = get_song(song_id=song_id)
    if not db_song:
        return None
        
    artist_ids = song_data.pop('artist_ids', None)
    
    for key, val in song_data.items():
        setattr(db_song, key, val)
    
    if artist_ids is not None:
        # 清空並重新指派原唱歌手
        db_song.artists.clear()
        if artist_ids:
            artists = db.session.scalars(select(Artist).where(Artist.id.in_(artist_ids))).all()
            db_song.artists.extend(artists)
        
    db.session.commit()
    db.session.refresh(db_song)
    return db_song

def delete_song(song_id: int):
    db_song = get_song(song_id=song_id)
    if not db_song:
        return False
    db.session.delete(db_song)
    db.session.commit()
    return True
