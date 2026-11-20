from sqlalchemy import select, func
from sqlalchemy.orm import selectinload, joinedload
from app.extensions import db
from app.models.artist import Artist
from app.models.association import song_artists
from app.models.record import SingingRecord
from app.models.song import Song
from app.models.vtuber import VTuber

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


def get_active_artist_count() -> int:
    """回傳全站至少擁有一筆演唱紀錄的原唱歌手數量"""
    stmt = (
        select(func.count(func.distinct(song_artists.c.artist_id)))
        .select_from(
            song_artists.join(SingingRecord, song_artists.c.song_id == SingingRecord.song_id)
        )
    )
    return db.session.scalar(stmt) or 0


def get_artist_catalog_data() -> dict:
    """彙整所有至少有一筆演唱紀錄的原唱歌手、收錄歌曲與各主播演唱明細"""
    vtubers = db.session.scalars(select(VTuber).order_by(VTuber.id.asc())).all()
    vtubers_data = [
        {
            "id": vt.id,
            "name_main": vt.name_main,
            "theme_color": vt.theme_color or "#a78bfa",
            "share_slug": (
                vt.name_romaji.strip().lower().replace(" ", "_")
                if vt.name_romaji and vt.name_romaji.strip()
                else str(vt.id)
            ),
            "avatar_url": vt.avatar_url or "",
        }
        for vt in vtubers
    ]

    artists = db.session.scalars(
        select(Artist).options(
            selectinload(Artist.songs)
            .selectinload(Song.singing_records)
            .joinedload(SingingRecord.video),
            selectinload(Artist.songs)
            .selectinload(Song.singing_records)
            .selectinload(SingingRecord.singers),
        )
    ).all()

    artists_list = []
    for artist in artists:
        songs_list = []
        artist_vtuber_ids = set()
        total_records = 0

        for song in artist.songs:
            if not song.singing_records:
                continue

            records_list = []
            for rec in song.singing_records:
                video_vt_id = rec.video.vtuber_id if rec.video else None
                singer_ids = [v.id for v in rec.singers] if rec.singers else []
                if video_vt_id is not None and video_vt_id in singer_ids:
                    owner_vtuber_id = video_vt_id
                elif singer_ids:
                    owner_vtuber_id = singer_ids[0]
                else:
                    owner_vtuber_id = video_vt_id

                if owner_vtuber_id is not None:
                    artist_vtuber_ids.add(owner_vtuber_id)

                date_str = ""
                video_title = ""
                if rec.video:
                    video_title = rec.video.title or ""
                    if rec.video.published_at:
                        date_str = rec.video.published_at.isoformat()[:10]

                records_list.append({
                    "id": rec.id,
                    "video_id": rec.video_id,
                    "t": rec.timestamp_seconds or 0,
                    "vtuber_id": owner_vtuber_id,
                    "date": date_str,
                    "video_title": video_title,
                    "note": rec.note or "",
                })

            if not records_list:
                continue

            records_list.sort(key=lambda item: (item["date"], item["id"]), reverse=True)
            total_records += len(records_list)
            songs_list.append({
                "id": song.id,
                "title_main": song.title_main,
                "song_type": song.song_type or "cover",
                "record_count": len(records_list),
                "records": records_list,
            })

        if not songs_list:
            continue

        songs_list.sort(key=lambda item: (-item["record_count"], item["title_main"]))
        artists_list.append({
            "id": artist.id,
            "name_main": artist.name_main,
            "name_en": artist.name_en or "",
            "name_ja": artist.name_ja or "",
            "name_zh": artist.name_zh or "",
            "name_romaji": artist.name_romaji or "",
            "wikidata_id": artist.wikidata_id or "",
            "song_count": len(songs_list),
            "record_count": total_records,
            "vtuber_ids": sorted(artist_vtuber_ids),
            "songs": songs_list,
        })

    artists_list.sort(key=lambda item: (-item["record_count"], -item["song_count"], item["name_main"]))
    return {
        "vtubers": vtubers_data,
        "artists": artists_list,
    }
