from sqlalchemy.orm import Session
from sqlalchemy import select, insert, and_
from app.models.vtuber import VTuber
from app.models.link import VTuberLink
from app.models.song import Song
from app.models.association import vtuber_songs
from app.schemas.vtuber import VTuberCreate
from app.schemas.link import VTuberLinkCreate

def get_vtuber(db: Session, vtuber_id: int):
    return db.scalars(select(VTuber).where(VTuber.id == vtuber_id)).first()

def get_vtuber_by_name(db: Session, name: str):
    return db.scalars(select(VTuber).where(VTuber.name_main == name)).first()

def get_vtubers(db: Session, skip: int = 0, limit: int = 100):
    return db.scalars(select(VTuber).offset(skip).limit(limit)).all()

def sync_vtuber_links_from_social_links(db: Session, db_vtuber: VTuber):
    # 先清除該主播現有的所有 VTuberLink
    db.query(VTuberLink).filter(VTuberLink.vtuber_id == db_vtuber.id).delete()
    
    if not db_vtuber.social_links:
        db.commit()
        return

    import json
    if db_vtuber.social_links.strip().startswith("["):
        try:
            links_data = json.loads(db_vtuber.social_links)
            for item in links_data:
                platform = item.get("platform", "link")
                url = item.get("url", "")
                if url:
                    db_link = VTuberLink(vtuber_id=db_vtuber.id, platform=platform, url=url)
                    db.add(db_link)
            db.commit()
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
            db.add(db_link)
            
    db.commit()

def create_vtuber(db: Session, vtuber: VTuberCreate):
    db_vtuber = VTuber(**vtuber.model_dump())
    db.add(db_vtuber)
    db.commit()
    db.refresh(db_vtuber)
    
    sync_vtuber_links_from_social_links(db, db_vtuber)
    db.refresh(db_vtuber)
    return db_vtuber

def create_vtuber_link(db: Session, vtuber_id: int, platform: str, url: str):
    db_link = VTuberLink(vtuber_id=vtuber_id, platform=platform, url=url)
    db.add(db_link)
    db.commit()
    db.refresh(db_link)
    return db_link

def add_vtuber_song(db: Session, vtuber_id: int, song_id: int, association_type: str = "signature"):
    """在 vtuber_songs 中綁定歌曲，支援 signature (常駐) 或 requestable (點歌)"""
    vtuber = get_vtuber(db, vtuber_id)
    song = db.scalars(select(Song).where(Song.id == song_id)).first()
    if vtuber and song:
        # 檢查是否已存在
        stmt = select(vtuber_songs).where(
            and_(
                vtuber_songs.c.vtuber_id == vtuber_id,
                vtuber_songs.c.song_id == song_id,
                vtuber_songs.c.association_type == association_type
            )
        )
        exists = db.execute(stmt).first()
        if not exists:
            db.execute(
                insert(vtuber_songs).values(
                    vtuber_id=vtuber_id,
                    song_id=song_id,
                    association_type=association_type
                )
            )
            db.commit()
            db.refresh(vtuber)
    return vtuber

def add_signature_song(db: Session, vtuber_id: int, song_id: int):
    """相容舊的常駐歌單綁定呼叫"""
    return add_vtuber_song(db, vtuber_id, song_id, association_type="signature")

def update_vtuber(db: Session, vtuber_id: int, vtuber_data: dict):
    db_vtuber = get_vtuber(db, vtuber_id)
    if db_vtuber:
        has_social_links = "social_links" in vtuber_data
        for key, val in vtuber_data.items():
            setattr(db_vtuber, key, val)
        db.commit()
        
        if has_social_links:
            sync_vtuber_links_from_social_links(db, db_vtuber)
        db.refresh(db_vtuber)
    return db_vtuber

def delete_vtuber(db: Session, vtuber_id: int):
    db_vtuber = get_vtuber(db, vtuber_id)
    if db_vtuber:
        db.delete(db_vtuber)
        db.commit()
        return True
    return False
