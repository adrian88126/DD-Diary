import json
from sqlalchemy import select, insert, and_
from app.extensions import db
from app.models.vtuber import VTuber
from app.models.link import VTuberLink
from app.models.song import Song
from app.models.association import vtuber_songs

def get_vtuber(vtuber_id: int):
    return db.session.scalars(select(VTuber).where(VTuber.id == vtuber_id)).first()

def get_vtuber_by_name(name: str):
    return db.session.scalars(select(VTuber).where(VTuber.name_main == name)).first()

def get_vtubers(skip: int = 0, limit: int = 100):
    return db.session.scalars(select(VTuber).offset(skip).limit(limit)).all()

def sync_vtuber_links_from_social_links(db_vtuber: VTuber):
    # 先清除該主播現有的所有 VTuberLink
    db.session.query(VTuberLink).filter(VTuberLink.vtuber_id == db_vtuber.id).delete()
    
    if not db_vtuber.social_links:
        db.session.commit()
        return

    if db_vtuber.social_links.strip().startswith("["):
        try:
            links_data = json.loads(db_vtuber.social_links)
            for item in links_data:
                platform = item.get("platform", "link")
                url = item.get("url", "")
                if url:
                    db_link = VTuberLink(vtuber_id=db_vtuber.id, platform=platform, url=url)
                    db.session.add(db_link)
            db.session.commit()
            return
        except Exception as e:
            print(f"Error parsing JSON social_links: {e}")
        
    lines = db_vtuber.social_links.strip().split("\n")
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        platform = "link"
        url = line
        
        # 1. 支援 "平台,網址" 格式
        if "," in line:
            parts = line.split(",", 1)
            p_candidate = parts[0].strip()
            u_candidate = parts[1].strip()
            if u_candidate.startswith("http://") or u_candidate.startswith("https://"):
                platform = p_candidate
                url = u_candidate
                
        # 2. 自動識別平台
        if url.startswith("http://") or url.startswith("https://"):
            url_lower = url.lower()
            if "twitter.com" in url_lower or "x.com" in url_lower:
                if platform == "link": platform = "Twitter"
            elif "youtube.com" in url_lower or "youtu.be" in url_lower:
                if platform == "link": platform = "YouTube"
            elif "twitch.tv" in url_lower:
                if platform == "link": platform = "Twitch"
            elif "facebook.com" in url_lower:
                if platform == "link": platform = "Facebook"
            elif "instagram.com" in url_lower:
                if platform == "link": platform = "Instagram"
            elif "bilibili.com" in url_lower:
                if platform == "link": platform = "Bilibili"
                
            db_link = VTuberLink(vtuber_id=db_vtuber.id, platform=platform, url=url)
            db.session.add(db_link)
            
    db.session.commit()

def create_vtuber(vtuber_data: dict):
    db_vtuber = VTuber(**vtuber_data)
    db.session.add(db_vtuber)
    db.session.commit()
    db.session.refresh(db_vtuber)
    
    sync_vtuber_links_from_social_links(db_vtuber)
    db.session.refresh(db_vtuber)
    return db_vtuber

def create_vtuber_link(vtuber_id: int, platform: str, url: str):
    db_link = VTuberLink(vtuber_id=vtuber_id, platform=platform, url=url)
    db.session.add(db_link)
    db.session.commit()
    db.session.refresh(db_link)
    return db_link

def add_vtuber_song(vtuber_id: int, song_id: int, association_type: str = "signature"):
    """在 vtuber_songs 中綁定歌曲，支援 signature (常駐) 或 requestable (點歌)"""
    vtuber = get_vtuber(vtuber_id)
    song = db.session.scalars(select(Song).where(Song.id == song_id)).first()
    if vtuber and song:
        # 檢查是否已存在
        stmt = select(vtuber_songs).where(
            and_(
                vtuber_songs.c.vtuber_id == vtuber_id,
                vtuber_songs.c.song_id == song_id,
                vtuber_songs.c.association_type == association_type
            )
        )
        exists = db.session.execute(stmt).first()
        if not exists:
            db.session.execute(
                insert(vtuber_songs).values(
                    vtuber_id=vtuber_id,
                    song_id=song_id,
                    association_type=association_type
                )
            )
            db.session.commit()
            db.session.refresh(vtuber)
    return vtuber

def add_signature_song(vtuber_id: int, song_id: int):
    """相容舊的常駐歌單綁定呼叫"""
    return add_vtuber_song(vtuber_id, song_id, association_type="signature")

def update_vtuber(vtuber_id: int, vtuber_data: dict):
    db_vtuber = get_vtuber(vtuber_id)
    if db_vtuber:
        has_social_links = "social_links" in vtuber_data
        for key, val in vtuber_data.items():
            setattr(db_vtuber, key, val)
        db.session.commit()
        
        if has_social_links:
            sync_vtuber_links_from_social_links(db_vtuber)
        db.session.refresh(db_vtuber)
    return db_vtuber

def delete_vtuber(vtuber_id: int):
    db_vtuber = get_vtuber(vtuber_id)
    if db_vtuber:
        db.session.delete(db_vtuber)
        db.session.commit()
        return True
    return False
