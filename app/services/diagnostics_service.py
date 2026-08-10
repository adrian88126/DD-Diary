from sqlalchemy import select, func, and_
from app.extensions import db
from app.models.song import Song
from app.models.artist import Artist
from app.models.record import SingingRecord
from app.models.association import song_artists, vtuber_songs

def get_unknown_songs():
    subq = select(song_artists.c.song_id)
    stmt = select(Song).where(Song.id.not_in(subq)).order_by(Song.id.desc())
    return db.session.scalars(stmt).all()

def get_duplicate_songs():
    subq = (
        select(func.lower(Song.title_main))
        .group_by(func.lower(Song.title_main))
        .having(func.count(Song.id) > 1)
    )
    duplicate_titles = db.session.scalars(subq).all()
    
    if not duplicate_titles:
        return {}
        
    stmt_songs = select(Song).where(func.lower(Song.title_main).in_(duplicate_titles)).order_by(Song.title_main)
    songs = db.session.scalars(stmt_songs).all()
    
    res = {}
    for s in songs:
        k = s.title_main.lower()
        if k not in res:
            res[k] = []
        res[k].append(str(s.id))
    return res

def auto_link_duplicates():
    subq = (
        select(func.lower(Song.title_main))
        .group_by(func.lower(Song.title_main))
        .having(func.count(Song.id) > 1)
    )
    duplicate_titles = db.session.scalars(subq).all()
    
    cleaned_count = 0
    for title in duplicate_titles:
        songs = db.session.scalars(
            select(Song).where(func.lower(Song.title_main) == title).order_by(Song.id.asc())
        ).all()
        
        if len(songs) <= 1:
            continue
            
        canonical = songs[0]
        duplicates = songs[1:]
        
        for dup in duplicates:
            db.session.query(SingingRecord).filter(SingingRecord.song_id == dup.id).update(
                {"song_id": canonical.id}
            )
            
            dup_mappings = db.session.execute(
                select(vtuber_songs).where(vtuber_songs.c.song_id == dup.id)
            ).fetchall()
            
            for m in dup_mappings:
                exists = db.session.execute(
                    select(vtuber_songs).where(
                        and_(
                            vtuber_songs.c.vtuber_id == m.vtuber_id,
                            vtuber_songs.c.song_id == canonical.id,
                            vtuber_songs.c.association_type == m.association_type
                        )
                    )
                ).first()
                
                if exists:
                    db.session.execute(
                        vtuber_songs.delete().where(
                            and_(
                                vtuber_songs.c.vtuber_id == m.vtuber_id,
                                vtuber_songs.c.song_id == dup.id,
                                vtuber_songs.c.association_type == m.association_type
                            )
                        )
                    )
                else:
                    db.session.execute(
                        vtuber_songs.update()
                        .where(
                            and_(
                                vtuber_songs.c.vtuber_id == m.vtuber_id,
                                vtuber_songs.c.song_id == dup.id,
                                vtuber_songs.c.association_type == m.association_type
                            )
                        )
                        .values(song_id=canonical.id)
                    )
            
            for artist in dup.artists:
                if artist not in canonical.artists:
                    canonical.artists.append(artist)
            
            dup.artists.clear()
            db.session.delete(dup)
            cleaned_count += 1
            
    db.session.commit()
    return {"cleaned_count": cleaned_count}

def get_duplicate_artists():
    subq = (
        select(func.lower(Artist.name_main))
        .group_by(func.lower(Artist.name_main))
        .having(func.count(Artist.id) > 1)
    )
    duplicate_names = db.session.scalars(subq).all()
    
    if not duplicate_names:
        return {}
        
    stmt_artists = select(Artist).where(func.lower(Artist.name_main).in_(duplicate_names)).order_by(Artist.name_main)
    artists = db.session.scalars(stmt_artists).all()
    
    res = {}
    for a in artists:
        k = a.name_main.lower()
        if k not in res:
            res[k] = []
        res[k].append(str(a.id))
    return res

def auto_link_duplicate_artists():
    subq = (
        select(func.lower(Artist.name_main))
        .group_by(func.lower(Artist.name_main))
        .having(func.count(Artist.id) > 1)
    )
    duplicate_names = db.session.scalars(subq).all()
    
    cleaned_count = 0
    for name in duplicate_names:
        artists = db.session.scalars(
            select(Artist).where(func.lower(Artist.name_main) == name).order_by(Artist.id.asc())
        ).all()
        
        if len(artists) <= 1:
            continue
            
        canonical = artists[0]
        duplicates = artists[1:]
        
        for dup in duplicates:
            dup_mappings = db.session.execute(
                select(song_artists).where(song_artists.c.artist_id == dup.id)
            ).fetchall()
            
            for m in dup_mappings:
                exists = db.session.execute(
                    select(song_artists).where(
                        and_(
                            song_artists.c.song_id == m.song_id,
                            song_artists.c.artist_id == canonical.id
                        )
                    )
                ).first()
                
                if exists:
                    db.session.execute(
                        song_artists.delete().where(
                            and_(
                                song_artists.c.song_id == m.song_id,
                                song_artists.c.artist_id == dup.id
                            )
                        )
                    )
                else:
                    db.session.execute(
                        song_artists.update()
                        .where(
                            and_(
                                song_artists.c.song_id == m.song_id,
                                song_artists.c.artist_id == dup.id
                            )
                        )
                        .values(artist_id=canonical.id)
                    )
            
            db.session.delete(dup)
            cleaned_count += 1
            
    db.session.commit()
    return {"cleaned_count": cleaned_count}
