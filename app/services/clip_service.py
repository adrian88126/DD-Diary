from app.extensions import db
from app.models.clip import ClipAuthor, Clip
from app.models.vtuber import VTuber
from app.models.song import Song
from app.models.association import clip_vtubers
from sqlalchemy import select
from app.services.youtube_service import scrape_youtube_channel_videos, scrape_youtube_playlist_videos
from datetime import datetime

def get_clip_author(author_id):
    return db.session.scalar(select(ClipAuthor).where(ClipAuthor.id == author_id))

def get_clip_authors(skip=0, limit=100):
    return db.session.scalars(select(ClipAuthor).offset(skip).limit(limit)).all()

def create_clip_author(data):
    author = ClipAuthor(
        name=data.get("name"),
        youtube_channel_id=data.get("youtube_channel_id"),
        channel_url=data.get("channel_url")
    )
    db.session.add(author)
    db.session.commit()
    return author

def update_clip_author(author_id, data):
    author = get_clip_author(author_id)
    if author:
        if "name" in data:
            author.name = data["name"]
        if "youtube_channel_id" in data:
            author.youtube_channel_id = data["youtube_channel_id"]
        if "channel_url" in data:
            author.channel_url = data["channel_url"]
        db.session.commit()
    return author

def delete_clip_author(author_id):
    author = get_clip_author(author_id)
    if author:
        db.session.delete(author)
        db.session.commit()

def get_clip(clip_id):
    return db.session.scalar(select(Clip).where(Clip.id == clip_id))

def get_clips(author_id=None, vtuber_id=None, tag=None, skip=0, limit=100):
    stmt = select(Clip)
    if author_id:
        stmt = stmt.where(Clip.author_id == author_id)
    if tag:
        stmt = stmt.where(Clip.tags.like(f"%{tag}%"))
    if vtuber_id:
        stmt = stmt.join(Clip.vtubers).where(VTuber.id == vtuber_id)
        
    return db.session.scalars(stmt.offset(skip).limit(limit)).all()

def create_clip(data):
    clip = Clip(
        video_id=data.get("video_id"),
        title=data.get("title"),
        tags=data.get("tags"),
        published_at=data.get("published_at"),
        author_id=data.get("author_id"),
        song_id=data.get("song_id")
    )
    db.session.add(clip)
    
    vtuber_ids = data.get("vtuber_ids", [])
    if vtuber_ids:
        vtubers = db.session.scalars(select(VTuber).where(VTuber.id.in_(vtuber_ids))).all()
        clip.vtubers.extend(vtubers)
        
    db.session.commit()
    return clip

def update_clip(clip_id, data):
    clip = get_clip(clip_id)
    if clip:
        if "title" in data:
            clip.title = data["title"]
        if "tags" in data:
            clip.tags = data["tags"]
        if "published_at" in data:
            clip.published_at = data["published_at"]
        if "author_id" in data:
            clip.author_id = data["author_id"]
        if "song_id" in data:
            clip.song_id = data["song_id"]
            
        if "vtuber_ids" in data:
            vtuber_ids = data["vtuber_ids"]
            vtubers = db.session.scalars(select(VTuber).where(VTuber.id.in_(vtuber_ids))).all()
            clip.vtubers.clear()
            clip.vtubers.extend(vtubers)
            
        db.session.commit()
    return clip

def delete_clip(clip_id):
    clip = get_clip(clip_id)
    if clip:
        db.session.delete(clip)
        db.session.commit()

def bulk_delete_clips(clip_ids):
    if not clip_ids:
        return 0
    clips = db.session.scalars(select(Clip).where(Clip.id.in_(clip_ids))).all()
    count = len(clips)
    for c in clips:
        db.session.delete(c)
    db.session.commit()
    return count

def bulk_update_clips(clip_ids, update_data):
    if not clip_ids or not update_data:
        return 0
    clips = db.session.scalars(select(Clip).where(Clip.id.in_(clip_ids))).all()
    if not clips:
        return 0

    action_type = update_data.get("action_type")
    
    if action_type == "set_author":
        author_id = update_data.get("author_id")
        for c in clips:
            c.author_id = int(author_id) if author_id else None

    elif action_type == "set_tags":
        tags_input = update_data.get("tags", "")
        mode = update_data.get("tag_mode", "replace")
        new_tag_list = [t.strip() for t in tags_input.split(",") if t.strip()]

        for c in clips:
            current_tags = [t.strip() for t in (c.tags or "").split(",") if t.strip()]
            if mode == "replace":
                c.tags = ",".join(new_tag_list)
            elif mode == "append":
                for t in new_tag_list:
                    if t not in current_tags:
                        current_tags.append(t)
                c.tags = ",".join(current_tags)
            elif mode == "remove":
                current_tags = [t for t in current_tags if t not in new_tag_list]
                c.tags = ",".join(current_tags)

    elif action_type == "set_vtubers":
        vtuber_ids = update_data.get("vtuber_ids", [])
        mode = update_data.get("vtuber_mode", "replace")
        target_vtubers = db.session.scalars(select(VTuber).where(VTuber.id.in_(vtuber_ids))).all() if vtuber_ids else []
        
        for c in clips:
            if mode == "replace":
                c.vtubers.clear()
                c.vtubers.extend(target_vtubers)
            elif mode == "append":
                existing_vids = {v.id for v in c.vtubers}
                for v in target_vtubers:
                    if v.id not in existing_vids:
                        c.vtubers.append(v)

    elif action_type == "set_song":
        song_id = update_data.get("song_id")
        for c in clips:
            c.song_id = int(song_id) if song_id else None

    db.session.commit()
    return len(clips)

def fetch_and_tag_clips(author_id, limit=50):
    author = get_clip_author(author_id)
    if not author or not author.youtube_channel_id:
        return []

    existing_clips = db.session.scalars(select(Clip.video_id).where(Clip.author_id == author_id)).all()
    existing_video_ids = set(existing_clips)

    scraped_videos = scrape_youtube_channel_videos(author.youtube_channel_id, limit=limit)
    
    vtubers = db.session.scalars(select(VTuber)).all()
    songs = db.session.scalars(select(Song)).all()

    tag_rules = {
        '歌唱': ['歌回', '歌枠', '唱了', 'Singing', 'Cover', '唱歌', '歌ってみた', 'cover'],
        '連動': ['連動', '合作', 'Collab', 'collab', 'ft.', 'feat'],
        '雜談': ['雜談', '聊', 'Talk', 'talk', '閒聊'],
        'ASMR': ['ASMR', 'asmr'],
        '迷因': ['迷因', '梗', 'Meme', 'meme', 'Shorts', 'shorts'],
        '遊戲': ['遊戲', 'Game', 'game', 'Minecraft', 'APEX', 'Apex', 'FF14', '原神', 'マイクラ', 'ゲーム']
    }

    results = []
    for vid in scraped_videos:
        video_id = vid.get("video_id")
        if not video_id or video_id in existing_video_ids:
            continue
        
        title = vid.get("title", "")
        
        detected_tags = []
        for tag_name, keywords in tag_rules.items():
            if any(kw in title for kw in keywords):
                detected_tags.append(tag_name)
                
        detected_vtuber_ids = []
        for v in vtubers:
            names_to_check = [v.name_main, v.name_ja, v.name_zh, v.name_romaji]
            names_to_check = [n for n in names_to_check if n]
            if any(name in title for name in names_to_check):
                detected_vtuber_ids.append(v.id)
                
        detected_song_id = None
        for s in songs:
            song_titles = [s.title_main, s.title_ja, s.title_zh, s.title_romaji]
            song_titles = [t for t in song_titles if t]
            if any(t in title for t in song_titles):
                detected_song_id = s.id
                break
                
        results.append({
            "video_id": video_id,
            "title": title,
            "thumbnail_url": vid.get("thumbnail_url"),
            "published_at": vid.get("published_at"),
            "tags": ",".join(detected_tags) if detected_tags else "",
            "detected_vtuber_ids": detected_vtuber_ids,
            "detected_song_id": detected_song_id
        })
        
    return results

def import_clips(items):
    for item in items:
        # 1. 智慧處理 Song (支援數字 ID 或自訂新歌名)
        raw_song = item.get("song_id")
        song_id = None
        if raw_song:
            if isinstance(raw_song, int):
                song_id = raw_song
            elif isinstance(raw_song, str) and raw_song.isdigit():
                song_id = int(raw_song)
            elif isinstance(raw_song, str) and raw_song.strip():
                song_title = raw_song.strip()
                existing_song = db.session.scalars(select(Song).where(Song.title_main == song_title)).first()
                if existing_song:
                    song_id = existing_song.id
                else:
                    new_song = Song(title_main=song_title)
                    db.session.add(new_song)
                    db.session.flush()
                    song_id = new_song.id

        # 2. 智慧處理 Author (支援數字 ID 或自訂新剪輯者名稱)
        raw_author = item.get("author_id")
        author_id = None
        if raw_author:
            if isinstance(raw_author, int):
                author_id = raw_author
            elif isinstance(raw_author, str) and raw_author.isdigit():
                author_id = int(raw_author)
            elif isinstance(raw_author, str) and raw_author.strip():
                author_name = raw_author.strip()
                existing_author = db.session.scalars(select(ClipAuthor).where(ClipAuthor.name == author_name)).first()
                if existing_author:
                    author_id = existing_author.id
                else:
                    new_author = ClipAuthor(name=author_name)
                    db.session.add(new_author)
                    db.session.flush()
                    author_id = new_author.id

        clip = Clip(
            video_id=item.get("video_id"),
            title=item.get("title"),
            tags=item.get("tags"),
            published_at=item.get("published_at"),
            author_id=author_id,
            song_id=song_id
        )
        db.session.add(clip)
        db.session.flush()
        
        vtuber_ids = item.get("vtuber_ids", [])
        if vtuber_ids:
            vtubers = db.session.scalars(select(VTuber).where(VTuber.id.in_(vtuber_ids))).all()
            clip.vtubers.extend(vtubers)
            
    db.session.commit()

def fetch_and_tag_playlist_clips(playlist_url, author_id=None, limit=200):
    """從 YouTube 播放清單抓取影片並執行智慧標籤分析，支援每部影片獨立作者識別"""
    playlist_data = scrape_youtube_playlist_videos(playlist_url, limit=limit)
    if not playlist_data or not playlist_data.get('videos'):
        return {"playlist_title": "", "channel_name": "", "channel_id": "", "clips": []}

    # 取得已存在的 clip video_ids 避免重複匯入
    existing_clips = db.session.scalars(select(Clip.video_id)).all()
    existing_video_ids = set(existing_clips)

    vtubers = db.session.scalars(select(VTuber)).all()
    songs = db.session.scalars(select(Song)).all()
    all_authors = list(db.session.scalars(select(ClipAuthor)).all())

    tag_rules = {
        '歌唱': ['歌回', '歌枠', '唱了', 'Singing', 'Cover', '唱歌', '歌ってみた', 'cover'],
        '連動': ['連動', '合作', 'Collab', 'collab', 'ft.', 'feat'],
        '雜談': ['雜談', '聊', 'Talk', 'talk', '閒聊'],
        'ASMR': ['ASMR', 'asmr'],
        '迷因': ['迷因', '梗', 'Meme', 'meme', 'Shorts', 'shorts'],
        '遊戲': ['遊戲', 'Game', 'game', 'Minecraft', 'APEX', 'Apex', 'FF14', '原神', 'マイクラ', 'ゲーム']
    }

    # 播放清單預設作者（若使用者指定，或由播放清單作者推導）
    default_author_id = author_id
    default_author_name = ""
    if default_author_id:
        author = get_clip_author(default_author_id)
        if author:
            default_author_name = author.name

    results = []
    for vid in playlist_data.get('videos', []):
        video_id = vid.get("video_id")
        if not video_id or video_id in existing_video_ids:
            continue

        title = vid.get("title", "")

        # 1. 智慧標籤
        detected_tags = []
        for tag_name, keywords in tag_rules.items():
            if any(kw in title for kw in keywords):
                detected_tags.append(tag_name)

        # 2. 智慧主播識別
        detected_vtuber_ids = []
        for v in vtubers:
            names_to_check = [v.name_main, v.name_ja, v.name_zh, v.name_romaji]
            names_to_check = [n for n in names_to_check if n]
            if any(name in title for name in names_to_check):
                detected_vtuber_ids.append(v.id)

        # 3. 智慧歌曲識別
        detected_song_id = None
        for s in songs:
            song_titles = [s.title_main, s.title_ja, s.title_zh, s.title_romaji]
            song_titles = [t for t in song_titles if t]
            if any(t in title for t in song_titles):
                detected_song_id = s.id
                break

        # 4. 智慧個別影片作者識別
        v_channel_id = vid.get("channel_id", "")
        v_channel_name = vid.get("channel_name", "")
        v_author_id = default_author_id
        v_author_name = default_author_name

        if not v_author_id:
            # 優先比對該部影片的頻道資訊
            target_cid = v_channel_id or playlist_data.get('channel_id', '')
            target_cname = v_channel_name or playlist_data.get('channel_name', '')
            
            if target_cid or target_cname:
                for a in all_authors:
                    if (target_cid and a.youtube_channel_id == target_cid) or \
                       (target_cname and a.name == target_cname):
                        v_author_id = a.id
                        v_author_name = a.name
                        break
                        
                # 若尚未存在，為該部影片自動建立剪輯師
                if not v_author_id and target_cname:
                    try:
                        new_author = ClipAuthor(
                            name=target_cname,
                            youtube_channel_id=target_cid,
                            channel_url=f"https://www.youtube.com/channel/{target_cid}" if target_cid else ""
                        )
                        db.session.add(new_author)
                        db.session.flush()
                        v_author_id = new_author.id
                        v_author_name = target_cname
                        all_authors.append(new_author)
                    except Exception:
                        db.session.rollback()

        results.append({
            "video_id": video_id,
            "title": title,
            "thumbnail_url": vid.get("thumbnail_url"),
            "published_at": vid.get("published_at"),
            "duration": vid.get("duration", ""),
            "channel_name": v_channel_name,
            "tags": ",".join(detected_tags) if detected_tags else "",
            "detected_vtuber_ids": detected_vtuber_ids,
            "detected_song_id": detected_song_id,
            "author_id": v_author_id,
            "author_name": v_author_name,
        })

    db.session.commit()

    return {
        "playlist_title": playlist_data.get("playlist_title", ""),
        "playlist_id": playlist_data.get("playlist_id", ""),
        "channel_name": playlist_data.get("channel_name", ""),
        "channel_id": playlist_data.get("channel_id", ""),
        "author_id": default_author_id,
        "author_name": default_author_name,
        "clips": results,
    }
