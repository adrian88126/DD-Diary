from sqlalchemy import select, func
from app.extensions import db
from app.models.artist import Artist

def get_artist(artist_id: int):
    return db.session.scalars(select(Artist).where(Artist.id == artist_id)).first()

def get_artists(skip: int = 0, limit: int = 100):
    return db.session.scalars(select(Artist).offset(skip).limit(limit)).all()

def create_artist(artist_data: dict):
    # 歌手重複檢查 (不分大小寫)
    existing = db.session.scalars(
        select(Artist).where(func.lower(Artist.name_main) == func.lower(artist_data.get('name_main', '')))
    ).first()
    if existing:
        return existing
        
    db_artist = Artist(**artist_data)
    db.session.add(db_artist)
    db.session.commit()
    db.session.refresh(db_artist)
    return db_artist

def update_artist(artist_id: int, artist_data: dict):
    db_artist = get_artist(artist_id=artist_id)
    if not db_artist:
        return None
        
    for key, val in artist_data.items():
        setattr(db_artist, key, val)
        
    db.session.commit()
    db.session.refresh(db_artist)
    return db_artist

def delete_artist(artist_id: int):
    db_artist = get_artist(artist_id=artist_id)
    if not db_artist:
        return False
    db.session.delete(db_artist)
    db.session.commit()
    return True
