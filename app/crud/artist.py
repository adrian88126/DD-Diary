from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models.artist import Artist
from app.schemas.artist import ArtistCreate

def get_artist(db: Session, artist_id: int):
    return db.scalars(select(Artist).where(Artist.id == artist_id)).first()

def get_artists(db: Session, skip: int = 0, limit: int = 100):
    return db.scalars(select(Artist).offset(skip).limit(limit)).all()

def create_artist(db: Session, artist: ArtistCreate):
    # 歌手重複檢查 (不分大小寫)
    from sqlalchemy import func
    existing = db.scalars(
        select(Artist).where(func.lower(Artist.name_main) == func.lower(artist.name_main))
    ).first()
    if existing:
        return existing
        
    db_artist = Artist(**artist.model_dump())
    db.add(db_artist)
    db.commit()
    db.refresh(db_artist)
    return db_artist


def update_artist(db: Session, artist_id: int, artist: ArtistCreate):
    db_artist = get_artist(db, artist_id=artist_id)
    if not db_artist:
        return None
    db_artist.name_main = artist.name_main
    db_artist.name_ja = artist.name_ja
    db_artist.name_zh = artist.name_zh
    db_artist.name_romaji = artist.name_romaji
    db.commit()
    db.refresh(db_artist)
    return db_artist

def delete_artist(db: Session, artist_id: int):
    db_artist = get_artist(db, artist_id=artist_id)
    if not db_artist:
        return False
    db.delete(db_artist)
    db.commit()
    return True

