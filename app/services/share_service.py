from sqlalchemy import select
from sqlalchemy.orm import selectinload, joinedload
from app.extensions import db
from app.models.vtuber import VTuber
from app.models.video import Video
from app.models.activity import Activity
from app.models.song import Song
from app.models.record import SingingRecord
from app.models.clip import Clip


def serialize_video(v: Video) -> dict:
    return {
        "video_id": v.video_id,
        "title": v.title,
        "published_at": v.published_at.isoformat() if v.published_at else None,
        "video_type": v.video_type,
        "thumbnail_url": v.thumbnail_url,
    }


def serialize_activity(a: Activity) -> dict:
    return {
        "id": a.id,
        "title": a.title,
        "event_date": a.event_date.isoformat() if a.event_date else None,
        "activity_type": a.activity_type,
        "link_url": a.link_url,
    }


def serialize_record(r: SingingRecord) -> dict:
    song_dict = None
    if r.song:
        artists_data = [
            {
                "id": a.id,
                "name_main": a.name_main,
                "name_en": a.name_en,
                "name_ja": a.name_ja,
                "name_zh": a.name_zh,
                "name_romaji": a.name_romaji,
                "wikidata_id": a.wikidata_id,
            }
            for a in r.song.artists
        ] if r.song.artists else []
        song_dict = {
            "id": r.song.id,
            "title_main": r.song.title_main,
            "song_type": r.song.song_type,
            "artists": artists_data,
        }

    video_dict = None
    if r.video:
        video_dict = {
            "title": r.video.title,
            "published_at": r.video.published_at.isoformat() if r.video.published_at else None,
        }

    return {
        "id": r.id,
        "song_id": r.song_id,
        "video_id": r.video_id,
        "timestamp_seconds": r.timestamp_seconds,
        "note": r.note,
        "song": song_dict,
        "video": video_dict,
    }


def get_vtuber_profile_payload(vtuber: VTuber) -> dict:
    """共用彙整單一主播公開專頁所需全部資料（Flask 路由與靜態打包共用）。"""
    vt_id = vtuber.id

    vt_videos = db.session.scalars(
        select(Video)
        .where(Video.vtuber_id == vt_id)
        .order_by(Video.published_at.desc(), Video.video_id.desc())
    ).all()
    vt_activities = db.session.scalars(
        select(Activity)
        .where(Activity.vtuber_id == vt_id)
        .order_by(Activity.event_date.desc())
    ).all()
    vt_records = db.session.scalars(
        select(SingingRecord)
        .where(SingingRecord.singers.any(id=vt_id))
        .options(
            joinedload(SingingRecord.video),
            joinedload(SingingRecord.song).selectinload(Song.artists),
        )
        .order_by(SingingRecord.id.desc())
    ).all()
    vt_clips = db.session.scalars(
        select(Clip)
        .join(Clip.vtubers)
        .where(VTuber.id == vt_id)
        .options(joinedload(Clip.author), joinedload(Clip.song))
        .order_by(Clip.id.desc())
    ).all()

    clips_data = []
    clip_authors_map = {}
    for c in vt_clips:
        author_name = c.author.name if c.author else "未知剪輯師"
        author_id = c.author.id if c.author else 0
        if c.author:
            clip_authors_map[c.author.id] = c.author.name

        clips_data.append({
            "id": c.id,
            "video_id": c.video_id,
            "title": c.title,
            "tags": c.tags or "",
            "published_at": c.published_at.isoformat() if c.published_at else None,
            "author_id": author_id,
            "author_name": author_name,
            "song_title": c.song.title_main if c.song else None,
            "thumbnail_url": f"https://img.youtube.com/vi/{c.video_id}/mqdefault.jpg",
        })

    all_clip_authors = [{"id": aid, "name": aname} for aid, aname in clip_authors_map.items()]
    videos_data = [serialize_video(v) for v in vt_videos if v.video_type != "clip"]
    activities_data = [serialize_activity(a) for a in vt_activities]
    records_data = [serialize_record(r) for r in vt_records]

    vtuber_dict = {
        "id": vtuber.id,
        "name_main": vtuber.name_main,
        "name_ja": vtuber.name_ja,
        "name_zh": vtuber.name_zh,
        "name_romaji": vtuber.name_romaji,
        "description": vtuber.description,
        "avatar_url": vtuber.avatar_url,
        "banner_url": vtuber.banner_url,
        "theme_color": vtuber.theme_color,
        "social_links": vtuber.social_links,
    }

    return {
        "vtuber_dict": vtuber_dict,
        "videos_data": videos_data,
        "activities_data": activities_data,
        "records_data": records_data,
        "clips_data": clips_data,
        "all_clip_authors": all_clip_authors,
    }
