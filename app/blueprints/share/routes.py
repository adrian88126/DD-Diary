import json
from flask import render_template, abort
from sqlalchemy import select, func
from app.blueprints.share import share_bp
from app.extensions import db
from app.models.vtuber import VTuber
from app.services.video_service import get_videos
from app.services.activity_service import get_activities
from app.services.record_service import get_records

def get_vtuber_by_identifier(identifier: str):
    if identifier.isdigit():
        return db.session.scalars(select(VTuber).where(VTuber.id == int(identifier))).first()
        
    ident_lower = identifier.lower()
    
    # 1. Exact match
    vtuber = db.session.scalars(select(VTuber).where(func.lower(VTuber.name_romaji) == ident_lower)).first()
    if vtuber: return vtuber
    
    # 2. Match with spaces instead of hyphens/underscores
    ident_spaced = ident_lower.replace("-", " ").replace("_", " ")
    vtuber = db.session.scalars(select(VTuber).where(func.lower(VTuber.name_romaji) == ident_spaced)).first()
    if vtuber: return vtuber
    
    # 3. Match with underscores instead of hyphens
    ident_underscored = ident_lower.replace("-", "_").replace(" ", "_")
    vtuber = db.session.scalars(select(VTuber).where(func.lower(VTuber.name_romaji) == ident_underscored)).first()
    if vtuber: return vtuber
    
    # 4. Fallback LIKE search
    vtuber = db.session.scalars(select(VTuber).where(func.lower(VTuber.name_romaji).like(f"%{ident_lower}%"))).first()
    return vtuber

@share_bp.route('/<identifier>')
def profile(identifier):
    vtuber = get_vtuber_by_identifier(identifier)
    if not vtuber:
        abort(404)
        
    videos = get_videos(vtuber_id=vtuber.id, limit=2000)
    activities = get_activities(vtuber_id=vtuber.id, limit=2000)
    records = get_records(vtuber_id=vtuber.id, limit=2000)
    
    # 查詢與該主播關聯的切片
    clips = vtuber.clips if hasattr(vtuber, 'clips') else []
    clips_data = []
    clip_authors_map = {}
    for c in clips:
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
            "thumbnail_url": f"https://img.youtube.com/vi/{c.video_id}/mqdefault.jpg"
        })

    all_clip_authors = [{"id": aid, "name": aname} for aid, aname in clip_authors_map.items()]
    
    videos_data = [{"video_id": v.video_id, "title": v.title, "published_at": v.published_at.isoformat() if v.published_at else None, "video_type": v.video_type, "thumbnail_url": v.thumbnail_url} for v in videos]
    activities_data = [{"id": a.id, "title": a.title, "event_date": a.event_date.isoformat() if a.event_date else None, "activity_type": a.activity_type, "link_url": a.link_url} for a in activities]
    records_data = []
    for r in records:
        song_dict = None
        if r.song:
            artists_data = [{"name_main": a.name_main} for a in r.song.artists] if r.song.artists else []
            song_dict = {
                "id": r.song.id,
                "title_main": r.song.title_main,
                "song_type": r.song.song_type,
                "artists": artists_data
            }
        
        video_dict = None
        if r.video:
            video_dict = {
                "title": r.video.title,
                "published_at": r.video.published_at.isoformat() if r.video.published_at else None
            }
            
        records_data.append({
            "id": r.id,
            "song_id": r.song_id,
            "video_id": r.video_id,
            "timestamp_seconds": r.timestamp_seconds,
            "note": r.note,
            "song": song_dict,
            "video": video_dict
        })
    
    vtuber_dict = {
        "id": vtuber.id,
        "name_main": vtuber.name_main,
        "theme_color": vtuber.theme_color,
        "social_links": vtuber.social_links
    }

    return render_template('share/profile.html', 
        vtuber=vtuber, 
        clips=clips_data,
        all_clip_authors=all_clip_authors,
        vtuber_dict=vtuber_dict,
        videos_data=videos_data,
        activities_data=activities_data,
        records_data=records_data,
        clips_data=clips_data,
        vtuber_json=json.dumps(vtuber_dict),
        videos_json=json.dumps(videos_data),
        activities_json=json.dumps(activities_data),
        records_json=json.dumps(records_data),
        clips_json=json.dumps(clips_data)
    )
