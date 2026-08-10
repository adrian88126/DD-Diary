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
        
    normalized_id = identifier.replace("-", "_").lower()
    
    vtuber = db.session.scalars(select(VTuber).where(func.lower(VTuber.name_romaji) == normalized_id)).first()
    if vtuber:
        return vtuber
        
    vtuber = db.session.scalars(select(VTuber).where(func.lower(VTuber.name_romaji).like(f"%{normalized_id}%"))).first()
    return vtuber

@share_bp.route('/<identifier>')
def profile(identifier):
    vtuber = get_vtuber_by_identifier(identifier)
    if not vtuber:
        abort(404)
        
    videos = get_videos(vtuber_id=vtuber.id, limit=2000)
    activities = get_activities(vtuber_id=vtuber.id, limit=2000)
    records = get_records(vtuber_id=vtuber.id, limit=2000)
    
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
        vtuber_json=json.dumps(vtuber_dict),
        videos_json=json.dumps(videos_data),
        activities_json=json.dumps(activities_data),
        records_json=json.dumps(records_data)
    )
