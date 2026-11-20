import re
from sqlalchemy import select, func, and_, or_
from app.extensions import db
from app.models.song import Song
from app.models.artist import Artist
from app.models.record import SingingRecord
from app.models.vtuber import VTuber
from app.models.video import Video
from app.models.clip import Clip, ClipAuthor
from app.models.association import song_artists, vtuber_songs, record_vtubers, clip_vtubers

SHARED_WIKIDATA_EXCLUDE = {"Q909655"}  # 鏡音連／鏡音鈴共享同一個組合 QID，不可合併


def _has_kana(s: str) -> bool:
    return bool(re.search(r"[\u3040-\u30ff]", s or ""))


def _has_cjk(s: str) -> bool:
    return bool(re.search(r"[\u4e00-\u9fff]", s or ""))


def _is_pure_ascii(s: str) -> bool:
    return bool(s) and not _has_kana(s) and not _has_cjk(s) and bool(re.search(r"[A-Za-z]", s))

# --- 1. 歌曲與歌手診斷 ---

def get_unknown_songs():
    """無原唱歌手關聯的歌曲"""
    subq = select(song_artists.c.song_id)
    stmt = select(Song).where(Song.id.not_in(subq)).order_by(Song.id.desc())
    return db.session.scalars(stmt).all()

def get_orphan_songs():
    """無任何演唱紀錄或點歌單引用的孤立歌曲"""
    subq_rec = select(SingingRecord.song_id)
    subq_vt = select(vtuber_songs.c.song_id)
    stmt = select(Song).where(
        and_(
            Song.id.not_in(subq_rec),
            Song.id.not_in(subq_vt)
        )
    ).order_by(Song.id.desc())
    return db.session.scalars(stmt).all()

def get_duplicate_songs():
    """標題完全相同的重複歌曲"""
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
        res[k].append({"id": s.id, "title": s.title_main, "artists": [a.name_main for a in s.artists]})
    return res

def get_duplicate_artists():
    """名稱完全相同的重複歌手"""
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
        res[k].append({"id": a.id, "name": a.name_main, "songs_count": len(a.songs)})
    return res


def get_wikidata_duplicate_artists():
    """依相同 Wikidata QID 偵測跨語言或別名重複歌手（排除合理共享條目）"""
    subq = (
        select(Artist.wikidata_id)
        .where(
            and_(
                Artist.wikidata_id.is_not(None),
                func.trim(Artist.wikidata_id) != "",
                Artist.wikidata_id.not_in(SHARED_WIKIDATA_EXCLUDE),
            )
        )
        .group_by(Artist.wikidata_id)
        .having(func.count(Artist.id) > 1)
    )
    dup_qids = db.session.scalars(subq).all()
    if not dup_qids:
        return {}

    artists = db.session.scalars(
        select(Artist)
        .where(Artist.wikidata_id.in_(dup_qids))
        .order_by(Artist.wikidata_id.asc(), Artist.id.asc())
    ).all()

    res = {}
    for a in artists:
        qid = (a.wikidata_id or "").strip()
        if qid not in res:
            res[qid] = []
        res[qid].append({
            "id": a.id,
            "name": a.name_main,
            "name_en": a.name_en or "",
            "name_ja": a.name_ja or "",
            "name_zh": a.name_zh or "",
            "songs_count": len(a.songs),
            "wikidata_id": qid,
        })
    return res

# --- 2. 切片與剪輯師診斷 ---

def get_untagged_clips():
    """標籤為空的切片"""
    stmt = select(Clip).where(or_(Clip.tags == None, Clip.tags == '')).order_by(Clip.id.desc())
    return db.session.scalars(stmt).all()

def get_unassigned_author_clips():
    """未關聯剪輯師作者的切片"""
    stmt = select(Clip).where(Clip.author_id == None).order_by(Clip.id.desc())
    return db.session.scalars(stmt).all()

def get_unassociated_vtuber_clips():
    """未標記任何出場主播的切片"""
    subq = select(clip_vtubers.c.clip_id)
    stmt = select(Clip).where(Clip.id.not_in(subq)).order_by(Clip.id.desc())
    return db.session.scalars(stmt).all()

def get_empty_clip_authors():
    """0 部切片的空白剪輯師帳號"""
    subq = select(Clip.author_id).where(Clip.author_id != None)
    stmt = select(ClipAuthor).where(ClipAuthor.id.not_in(subq)).order_by(ClipAuthor.id.desc())
    return db.session.scalars(stmt).all()

# --- 3. 演唱紀錄與時間軸診斷 ---

def get_duplicate_records():
    """同一影片、同一時間戳記重複登錄的演唱紀錄"""
    subq = (
        select(SingingRecord.video_id, SingingRecord.timestamp_seconds)
        .group_by(SingingRecord.video_id, SingingRecord.timestamp_seconds)
        .having(func.count(SingingRecord.id) > 1)
    )
    dup_pairs = db.session.execute(subq).fetchall()
    if not dup_pairs:
        return []
    
    records = []
    for vid, ts in dup_pairs:
        stmt = select(SingingRecord).where(
            and_(SingingRecord.video_id == vid, SingingRecord.timestamp_seconds == ts)
        ).order_by(SingingRecord.id.asc())
        recs = db.session.scalars(stmt).all()
        records.append({
            "video_id": vid,
            "timestamp": ts,
            "records": recs
        })
    return records

def get_invalid_timestamp_records():
    """時間戳記異常（負數或歌回直播 0 秒）的演唱紀錄，排除 MV 與 Short 合法 0 秒開唱"""
    stmt = (
        select(SingingRecord)
        .join(Video, SingingRecord.video_id == Video.video_id)
        .where(
            or_(
                SingingRecord.timestamp_seconds < 0,
                and_(
                    SingingRecord.timestamp_seconds <= 0,
                    Video.video_type == "stream_singing",
                ),
            )
        )
        .order_by(SingingRecord.id.desc())
    )
    return db.session.scalars(stmt).all()

# --- 4. 主播與影片資料完整性診斷 ---

def get_incomplete_vtubers():
    """缺少頻道 ID 的主播 (頭像因版權考量為選填，不列入缺失)"""
    stmt = select(VTuber).where(
        or_(
            VTuber.youtube_channel_id == None,
            VTuber.youtube_channel_id == ''
        )
    ).order_by(VTuber.id.asc())
    return db.session.scalars(stmt).all()

def get_orphan_videos():
    """未關聯任何主播的孤立影片"""
    stmt = select(Video).where(Video.vtuber_id == None).order_by(Video.video_id.desc())
    return db.session.scalars(stmt).all()

# --- 5. 全系統健康統計報告 (Overall Health Report) ---

def get_system_health_report():
    """取得全系統綜合健康檢測報告與分數 (100分制)"""
    dup_songs = get_duplicate_songs()
    dup_artists = get_duplicate_artists()
    wikidata_dup_artists = get_wikidata_duplicate_artists()
    orphan_songs = get_orphan_songs()
    unknown_songs = get_unknown_songs()
    
    untagged_clips = get_untagged_clips()
    unassigned_clips = get_unassigned_author_clips()
    unassoc_vt_clips = get_unassociated_vtuber_clips()
    empty_authors = get_empty_clip_authors()
    
    dup_records = get_duplicate_records()
    invalid_ts_records = get_invalid_timestamp_records()
    
    incomplete_vtubers = get_incomplete_vtubers()
    orphan_videos = get_orphan_videos()
    
    total_issues = (
        len(dup_songs) + len(dup_artists) + len(wikidata_dup_artists) + len(orphan_songs) +
        len(untagged_clips) + len(unassigned_clips) + len(unassoc_vt_clips) + len(empty_authors) +
        len(dup_records) + len(invalid_ts_records) +
        len(incomplete_vtubers) + len(orphan_videos)
    )
    
    # 計算健康分數 (100分扣除問題權重)
    deductions = (
        len(dup_songs) * 5 +
        len(dup_artists) * 4 +
        len(wikidata_dup_artists) * 4 +
        len(dup_records) * 5 +
        len(invalid_ts_records) * 3 +
        len(unassoc_vt_clips) * 2 +
        len(untagged_clips) * 1 +
        len(incomplete_vtubers) * 3
    )
    health_score = max(0, min(100, 100 - deductions))
    
    return {
        "health_score": health_score,
        "total_issues": total_issues,
        "songs": {
            "duplicate_songs": dup_songs,
            "duplicate_artists": dup_artists,
            "wikidata_duplicate_artists": wikidata_dup_artists,
            "orphan_songs": orphan_songs,
            "unknown_songs": unknown_songs
        },
        "clips": {
            "untagged_clips": untagged_clips,
            "unassigned_author_clips": unassigned_clips,
            "unassociated_vtuber_clips": unassoc_vt_clips,
            "empty_authors": empty_authors
        },
        "records": {
            "duplicate_records": dup_records,
            "invalid_timestamp_records": invalid_ts_records
        },
        "vtubers_videos": {
            "incomplete_vtubers": incomplete_vtubers,
            "orphan_videos": orphan_videos
        }
    }

# --- 6. 一鍵修復邏輯 (Auto-Fix Operations) ---

def auto_link_duplicates():
    """一鍵合併所有同名歌曲"""
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

def auto_link_duplicate_artists():
    """一鍵合併所有同名歌手"""
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


def auto_merge_wikidata_duplicate_artists():
    """依相同 Wikidata QID 合併跨語言或別名重複歌手，保留多語言名稱並轉移歌曲關聯"""
    dup_groups = get_wikidata_duplicate_artists()
    cleaned_count = 0
    merged_groups = []

    for qid, items in dup_groups.items():
        ids = [it["id"] for it in items]
        artists = db.session.scalars(
            select(Artist).where(Artist.id.in_(ids))
        ).all()
        if len(artists) <= 1:
            continue

        # 主保留筆優先順序：關聯歌曲數最多 -> 含漢字中文 -> ID 較小
        artists.sort(
            key=lambda a: (
                -len(a.songs),
                0 if (_has_cjk(a.name_main) and not _has_kana(a.name_main)) else 1,
                a.id,
            )
        )
        canonical = artists[0]
        duplicates = artists[1:]

        merged_names = []
        for dup in duplicates:
            merged_names.append(f"{dup.id}:{dup.name_main}")

            # 互補多語言欄位（不覆蓋主筆既有值、不重複填入主名稱）
            c_main_lower = (canonical.name_main or "").strip().lower()
            d_main = (dup.name_main or "").strip()

            if not (canonical.name_en or "").strip():
                cand_en = (dup.name_en or "").strip() or (d_main if _is_pure_ascii(d_main) else "")
                if cand_en and cand_en.lower() != c_main_lower:
                    canonical.name_en = cand_en

            if not (canonical.name_ja or "").strip():
                cand_ja = (dup.name_ja or "").strip() or (d_main if _has_kana(d_main) else "")
                if cand_ja and cand_ja.lower() != c_main_lower:
                    canonical.name_ja = cand_ja

            if not (canonical.name_zh or "").strip():
                cand_zh = (dup.name_zh or "").strip() or (
                    d_main if (_has_cjk(d_main) and not _has_kana(d_main)) else ""
                )
                if cand_zh and cand_zh.lower() != c_main_lower:
                    canonical.name_zh = cand_zh

            if not (canonical.name_romaji or "").strip() and (dup.name_romaji or "").strip():
                canonical.name_romaji = dup.name_romaji.strip()

            # 安全轉移 song_artists 關聯（透過 ORM 集合避免 UnitOfWork StaleDataError）
            for song in list(dup.songs):
                if song not in canonical.songs:
                    canonical.songs.append(song)
            dup.songs.clear()
            db.session.flush()
            db.session.delete(dup)
            db.session.flush()
            cleaned_count += 1

        merged_groups.append({
            "wikidata_id": qid,
            "canonical": f"{canonical.id}:{canonical.name_main}",
            "merged": merged_names,
            "name_en": canonical.name_en or "",
            "name_ja": canonical.name_ja or "",
            "name_zh": canonical.name_zh or "",
        })

    db.session.commit()
    return {"cleaned_count": cleaned_count, "merged_groups": merged_groups}

def auto_fix_untagged_clips():
    """一鍵為無標籤切片掃描標題並自動補上 AI/關鍵字標籤"""
    tag_rules = {
        '歌唱': ['歌回', '歌枠', '唱了', 'Singing', 'Cover', '唱歌', '歌ってみた', 'cover'],
        '連動': ['連動', '合作', 'Collab', 'collab', 'ft.', 'feat'],
        '雜談': ['雜談', '聊', 'Talk', 'talk', '閒聊'],
        'ASMR': ['ASMR', 'asmr'],
        '迷因': ['迷因', '梗', 'Meme', 'meme', 'Shorts', 'shorts'],
        '遊戲': ['遊戲', 'Game', 'game', 'Minecraft', 'APEX', 'Apex', 'FF14', '原神', 'マイクラ', 'ゲーム']
    }
    
    clips = get_untagged_clips()
    fixed_count = 0
    
    for c in clips:
        matched = [t for t, kws in tag_rules.items() if any(kw in (c.title or '') for kw in kws)]
        if matched:
            c.tags = ",".join(matched)
            fixed_count += 1
            
    db.session.commit()
    return {"fixed_count": fixed_count}

def auto_clean_duplicate_records():
    """一鍵清理重複演唱紀錄（保留最早一筆，刪除多餘的）"""
    dup_pairs = get_duplicate_records()
    deleted_count = 0
    
    for item in dup_pairs:
        recs = item["records"]
        if len(recs) > 1:
            for extra in recs[1:]:
                db.session.delete(extra)
                deleted_count += 1
                
    db.session.commit()
    return {"deleted_count": deleted_count}
