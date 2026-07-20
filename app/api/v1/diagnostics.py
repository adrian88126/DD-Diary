from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select, func, and_
from typing import List

from app.database import get_db
from app.models.song import Song
from app.models.artist import Artist
from app.models.record import SingingRecord
from app.models.association import song_artists, vtuber_songs
from app.schemas.song import Song as SchemaSong
from app.schemas.artist import Artist as SchemaArtist

router = APIRouter()

@router.get("/unknown_songs", response_model=List[SchemaSong])
def get_unknown_songs(db: Session = Depends(get_db)):
    # 尋找在 song_artists 中沒有任何歌手記錄的歌曲
    subq = select(song_artists.c.song_id)
    stmt = select(Song).where(Song.id.not_in(subq)).order_by(Song.id.desc())
    return db.scalars(stmt).all()

@router.get("/duplicate_songs")
def get_duplicate_songs(db: Session = Depends(get_db)):
    # 尋找名稱（小寫）相同且存在多筆的重複歌曲
    subq = (
        select(func.lower(Song.title_main))
        .group_by(func.lower(Song.title_main))
        .having(func.count(Song.id) > 1)
    )
    duplicate_titles = db.scalars(subq).all()
    
    if not duplicate_titles:
        return []
        
    stmt_songs = select(Song).where(func.lower(Song.title_main).in_(duplicate_titles)).order_by(Song.title_main)
    return db.scalars(stmt_songs).all()

@router.post("/auto_link_duplicates")
def auto_link_duplicates(db: Session = Depends(get_db)):
    # 自動整併同名重複歌曲：將其點歌單/常駐歌單以及歷史演唱紀錄對齊至 ID 最小的 canonical 歌曲，並清理重複項目
    subq = (
        select(func.lower(Song.title_main))
        .group_by(func.lower(Song.title_main))
        .having(func.count(Song.id) > 1)
    )
    duplicate_titles = db.scalars(subq).all()
    
    cleaned_count = 0
    for title in duplicate_titles:
        songs = db.scalars(
            select(Song).where(func.lower(Song.title_main) == title).order_by(Song.id.asc())
        ).all()
        
        if len(songs) <= 1:
            continue
            
        canonical = songs[0]
        duplicates = songs[1:]
        
        for dup in duplicates:
            # 1. 將歷史演唱紀錄關聯對齊至 canonical 歌曲
            db.query(SingingRecord).filter(SingingRecord.song_id == dup.id).update(
                {"song_id": canonical.id}
            )
            
            # 2. 將 vtuber_songs (常駐/點歌單) 對齊至 canonical
            dup_mappings = db.execute(
                select(vtuber_songs).where(vtuber_songs.c.song_id == dup.id)
            ).fetchall()
            
            for m in dup_mappings:
                exists = db.execute(
                    select(vtuber_songs).where(
                        and_(
                            vtuber_songs.c.vtuber_id == m.vtuber_id,
                            vtuber_songs.c.song_id == canonical.id,
                            vtuber_songs.c.association_type == m.association_type
                        )
                    )
                ).first()
                
                if exists:
                    # 若已存在 canonical 與該主播之關係，直接刪除重複的 dup 關係
                    db.execute(
                        vtuber_songs.delete().where(
                            and_(
                                vtuber_songs.c.vtuber_id == m.vtuber_id,
                                vtuber_songs.c.song_id == dup.id,
                                vtuber_songs.c.association_type == m.association_type
                            )
                        )
                    )
                else:
                    # 否則將關係更新為指向 canonical 歌曲
                    db.execute(
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
            
            # 3. 繼承歌手關係（若 canonical 還沒有的話）
            for artist in dup.artists:
                if artist not in canonical.artists:
                    canonical.artists.append(artist)
            
            # 4. 刪除該首重複的歌曲（ cascade 會自動清理關聯的 song_artists 等）
            dup.artists.clear()
            db.delete(dup)
            cleaned_count += 1
            
    db.commit()
    return {"cleaned_count": cleaned_count}

@router.get("/duplicate_artists", response_model=List[SchemaArtist])
def get_duplicate_artists(db: Session = Depends(get_db)):
    # 尋找名稱（小寫）相同且存在多筆的重複歌手
    subq = (
        select(func.lower(Artist.name_main))
        .group_by(func.lower(Artist.name_main))
        .having(func.count(Artist.id) > 1)
    )
    duplicate_names = db.scalars(subq).all()
    
    if not duplicate_names:
        return []
        
    stmt_artists = select(Artist).where(func.lower(Artist.name_main).in_(duplicate_names)).order_by(Artist.name_main)
    return db.scalars(stmt_artists).all()

@router.post("/auto_link_duplicate_artists")
def auto_link_duplicate_artists(db: Session = Depends(get_db)):
    # 自動整併同名重複歌手：將其歌曲關係搬移至 ID 最小的 canonical 歌手，並清理重複項目
    subq = (
        select(func.lower(Artist.name_main))
        .group_by(func.lower(Artist.name_main))
        .having(func.count(Artist.id) > 1)
    )
    duplicate_names = db.scalars(subq).all()
    
    cleaned_count = 0
    for name in duplicate_names:
        artists = db.scalars(
            select(Artist).where(func.lower(Artist.name_main) == name).order_by(Artist.id.asc())
        ).all()
        
        if len(artists) <= 1:
            continue
            
        canonical = artists[0]
        duplicates = artists[1:]
        
        for dup in duplicates:
            # 1. 搬移/更新 song_artists 關聯
            dup_mappings = db.execute(
                select(song_artists).where(song_artists.c.artist_id == dup.id)
            ).fetchall()
            
            for m in dup_mappings:
                exists = db.execute(
                    select(song_artists).where(
                        and_(
                            song_artists.c.song_id == m.song_id,
                            song_artists.c.artist_id == canonical.id
                        )
                    )
                ).first()
                
                if exists:
                    # 已經存在關聯，則直接刪除該 dup 關聯
                    db.execute(
                        song_artists.delete().where(
                            and_(
                                song_artists.c.song_id == m.song_id,
                                song_artists.c.artist_id == dup.id
                            )
                        )
                    )
                else:
                    # 否則，將關聯更新為指向 canonical 歌手
                    db.execute(
                        song_artists.update()
                        .where(
                            and_(
                                song_artists.c.song_id == m.song_id,
                                song_artists.c.artist_id == dup.id
                            )
                        )
                        .values(artist_id=canonical.id)
                    )
            
            # 2. 刪除重複的歌手
            db.delete(dup)
            cleaned_count += 1
            
    db.commit()
    return {"cleaned_count": cleaned_count}
