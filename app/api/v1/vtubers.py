from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from typing import List, Optional
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, date, timedelta
import re

from app.database import get_db
from app.schemas.vtuber import VTuber, VTuberCreate, VTuberPlaylistBatch
from app.schemas.link import VTuberLink, VTuberLinkCreate
from app.schemas.video import Video as SchemaVideo
from app.crud.vtuber import get_vtuber, get_vtubers, create_vtuber, create_vtuber_link, add_signature_song, add_vtuber_song, update_vtuber, delete_vtuber
from app.models.video import Video as DBVideo
from app.models.song import Song as DBSong
from app.models.artist import Artist as DBArtist
from app.crud.artist import create_artist
from app.schemas.artist import ArtistCreate

router = APIRouter()

@router.get("/", response_model=List[VTuber])
def read_vtubers(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return get_vtubers(db, skip=skip, limit=limit)

@router.get("/fetch_youtube_info")
def fetch_youtube_channel_info_endpoint(channel_url: str = Query(..., description="YouTube 頻道網址、@Handle 或 Channel ID")):
    try:
        channel_id = resolve_youtube_channel_id(channel_url)
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
        
    url = f"https://www.youtube.com/channel/{channel_id}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7"
    }

    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"無法獲取頻道頁面: {e}")

    data_match = re.search(r'ytInitialData\s*=\s*(\{.*?\});', html)
    if not data_match:
        raise HTTPException(status_code=500, detail="解析頻道資料失敗：找不到 ytInitialData")
        
    import json
    try:
        data = json.loads(data_match.group(1))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"解析 JSON 失敗: {e}")
    
    metadata = data.get('metadata', {}).get('channelMetadataRenderer', {})
    header = data.get('header', {})
    
    title = metadata.get('title', '')
    description = metadata.get('description', '')
    avatar_url = metadata.get('avatar', {}).get('thumbnails', [{}])[0].get('url', '')
    if avatar_url:
        avatar_url = re.sub(r'=s\d+-c', '=s900-c', avatar_url)
        
    banner_url = ""
    phr = header.get('pageHeaderRenderer', {})
    if phr:
        sources = phr.get('content', {}).get('pageHeaderViewModel', {}).get('banner', {}).get('imageBannerViewModel', {}).get('image', {}).get('sources', [])
        if sources:
            banner_url = sources[-1].get('url', '')
            
    if not banner_url:
        c4 = header.get('c4TabbedHeaderRenderer', {})
        banner_list = c4.get('banner', {}).get('thumbnails', [])
        if banner_list:
            banner_url = banner_list[-1].get('url', '')

    return {
        "channel_id": channel_id,
        "title": title,
        "description": description,
        "avatar_url": "",
        "banner_url": ""
    }

@router.get("/{vtuber_id}", response_model=VTuber)
def read_vtuber(vtuber_id: int, db: Session = Depends(get_db)):
    db_vtuber = get_vtuber(db, vtuber_id=vtuber_id)
    if not db_vtuber:
        raise HTTPException(status_code=404, detail="VTuber not found")
    return db_vtuber

def resolve_youtube_channel_id(channel_input: str) -> str:
    if not channel_input:
        return None
    channel_input = channel_input.strip()
    
    # 1. 檢查是否直接是 Channel ID (e.g., UCkiM6bCVlAGRkRm9R_CKbng)
    if re.match(r"^UC[a-zA-Z0-9_-]{22}$", channel_input):
        return channel_input
        
    # 2. 檢查是否是 /channel/UC... 格式網址
    match_cid = re.search(r"youtube\.com/channel/(UC[a-zA-Z0-9_-]+)", channel_input, re.IGNORECASE)
    if match_cid:
        return match_cid.group(1)
        
    # 3. 檢查是否包含 @handle 
    match_handle = re.search(r"(@[a-zA-Z0-9_\.\-]+)", channel_input)
    if match_handle:
        handle = match_handle.group(1)
        try:
            req = urllib.request.Request(
                f"https://www.youtube.com/{handle}",
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                html = resp.read().decode('utf-8', errors='ignore')
                match = re.search(r'youtube\.com/channel/(UC[a-zA-Z0-9_-]+)', html)
                if match:
                    return match.group(1)
        except Exception as e:
            print(f"Error resolving YouTube handle {handle}: {e}")
            
    raise HTTPException(
        status_code=400,
        detail=f"無法解析 YouTube 頻道 ID。請確保輸入的是正確的 @Handle、頻道網址或 UC 開頭的 ID！(輸入內容: {channel_input})"
    )

@router.post("/", response_model=VTuber)
def create_new_vtuber(vtuber: VTuberCreate, db: Session = Depends(get_db)):
    if vtuber.youtube_channel_id:
        vtuber.youtube_channel_id = resolve_youtube_channel_id(vtuber.youtube_channel_id)
    return create_vtuber(db=db, vtuber=vtuber)

@router.put("/{vtuber_id}", response_model=VTuber)
def update_vtuber_details(vtuber_id: int, vtuber: VTuberCreate, db: Session = Depends(get_db)):
    db_vtuber = get_vtuber(db, vtuber_id=vtuber_id)
    if not db_vtuber:
        raise HTTPException(status_code=404, detail="VTuber not found")
    if vtuber.youtube_channel_id:
        vtuber.youtube_channel_id = resolve_youtube_channel_id(vtuber.youtube_channel_id)
    return update_vtuber(db=db, vtuber_id=vtuber_id, vtuber_data=vtuber.model_dump())

@router.delete("/{vtuber_id}")
def delete_vtuber_by_id(vtuber_id: int, db: Session = Depends(get_db)):
    db_vtuber = get_vtuber(db, vtuber_id=vtuber_id)
    if not db_vtuber:
        raise HTTPException(status_code=404, detail="VTuber not found")
    success = delete_vtuber(db, vtuber_id)
    return {"success": success}

@router.post("/{vtuber_id}/links", response_model=VTuberLink)
def create_link_for_vtuber(vtuber_id: int, link: VTuberLinkCreate, db: Session = Depends(get_db)):
    db_vtuber = get_vtuber(db, vtuber_id=vtuber_id)
    if not db_vtuber:
        raise HTTPException(status_code=404, detail="VTuber not found")
    return create_vtuber_link(db=db, vtuber_id=vtuber_id, platform=link.platform, url=link.url)

@router.post("/{vtuber_id}/signatures/{song_id}", response_model=VTuber)
def add_signature(vtuber_id: int, song_id: int, db: Session = Depends(get_db)):
    db_vtuber = add_signature_song(db, vtuber_id=vtuber_id, song_id=song_id)
    if not db_vtuber:
        raise HTTPException(status_code=404, detail="VTuber or Song not found")
    return db_vtuber

@router.post("/{vtuber_id}/songs/batch", response_model=VTuber)
def associate_songs_batch_to_vtuber(
    vtuber_id: int,
    payload: VTuberPlaylistBatch,
    db: Session = Depends(get_db)
):
    """
    批次將多首歌曲關聯至主播的歌單 (點歌歌單 / 常駐歌單)
    支援一行一首歌，或「歌名 [Tab/雙空格] 歌手名」的格式
    """
    db_vtuber = get_vtuber(db, vtuber_id=vtuber_id)
    if not db_vtuber:
        raise HTTPException(status_code=404, detail="VTuber not found")
        
    association_type = payload.association_type
    if association_type not in ["signature", "requestable"]:
        raise HTTPException(status_code=400, detail="Invalid association_type")
        
    for line in payload.raw_lines:
        line = line.strip()
        if not line:
            continue
            
        # 智慧解析歌名與歌手
        # 支援 \t (Tab) 或是兩個以上的空白字元作為分隔
        parts = re.split(r'\t|\s{2,}', line)
        if len(parts) >= 2:
            song_name = parts[0].strip()
            artist_name = parts[1].strip()
        else:
            song_name = line.strip()
            artist_name = None
            
        if not song_name:
            continue
            
        # 1. 處理歌手 (若有提供且庫中沒有，則建立)
        target_artist = None
        if artist_name:
            # 歌手查重 (大小寫不敏感)
            target_artist = db.scalars(
                select(DBArtist).where(func.lower(DBArtist.name_main) == func.lower(artist_name))
            ).first()
            
            if not target_artist:
                # 建立新原唱歌手
                target_artist = create_artist(db, ArtistCreate(name_main=artist_name))
                
        # 2. 處理歌曲
        # 尋找歌曲 (大小寫不敏感)
        db_song = db.scalars(
            select(DBSong).where(func.lower(DBSong.title_main) == func.lower(song_name))
        ).first()
        
        if not db_song:
            # 歌曲不存在，自動建立一首新歌
            db_song = DBSong(
                title_main=song_name,
                song_type="cover"  # 預設為翻唱
            )
            if target_artist:
                db_song.artists.append(target_artist)
            db.add(db_song)
            db.flush() # 取得 id
        else:
            # 歌曲存在，若有提供歌手且該歌還沒有關聯此歌手，則補上關聯
            if target_artist and target_artist not in db_song.artists:
                db_song.artists.append(target_artist)
                db.flush()
            
        # 3. 建立與 VTuber 歌單關聯
        add_vtuber_song(db, vtuber_id=vtuber_id, song_id=db_song.id, association_type=association_type)
        
    db.commit()
    db.refresh(db_vtuber)
    return db_vtuber

@router.post("/{vtuber_id}/songs/{song_id}", response_model=VTuber)
def associate_song_to_vtuber(
    vtuber_id: int, 
    song_id: int, 
    association_type: str = Query("signature", description="歌單類型: signature (常駐) 或 requestable (點歌)"), 
    db: Session = Depends(get_db)
):
    """
    將歌曲關聯至主播的歌單 (支援常駐拿手歌或點歌歌單)
    """
    if association_type not in ["signature", "requestable"]:
        raise HTTPException(status_code=400, detail="Invalid association_type. Must be 'signature' or 'requestable'")
        
    db_vtuber = add_vtuber_song(db, vtuber_id=vtuber_id, song_id=song_id, association_type=association_type)
    if not db_vtuber:
        raise HTTPException(status_code=404, detail="VTuber or Song not found")
    return db_vtuber

def parse_relative_date(text: str) -> Optional[date]:
    if not text:
        return None
    text = text.strip().lower()
    
    # 移除常見前綴
    text = re.sub(r'^(streamed|直播於|發布於|直播時間：|直播結束於|已播完|預定發布時間：|發布時間：)\s*', '', text)
    
    # 精準日期格式: YYYY/M/D 或 YYYY-MM-DD
    m_exact = re.search(r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})', text)
    if m_exact:
        try:
            return date(int(m_exact.group(1)), int(m_exact.group(2)), int(m_exact.group(3)))
        except ValueError:
            pass
            
    today = date.today()
    
    # 支援相對時間
    m_day = re.search(r'(\d+)\s*(day|天)', text)
    if m_day:
        return today - timedelta(days=int(m_day.group(1)))
        
    m_hour = re.search(r'(\d+)\s*(hour|小時)', text)
    if m_hour:
        return today
        
    m_week = re.search(r'(\d+)\s*(?:個)?\s*(?:week|週|星期)', text)
    if m_week:
        return today - timedelta(weeks=int(m_week.group(1)))
        
    m_month = re.search(r'(\d+)\s*(?:個)?\s*(?:month|月)', text)
    if m_month:
        return today - timedelta(days=int(m_month.group(1)) * 30)
        
    m_year = re.search(r'(\d+)\s*(?:個)?\s*(?:year|年)', text)
    if m_year:
        return today - timedelta(days=int(m_year.group(1)) * 365)
        
    if 'yesterday' in text or '昨天' in text:
        return today - timedelta(days=1)
    if '前天' in text:
        return today - timedelta(days=2)
    if 'minute' in text or '分鐘' in text or 'second' in text or '秒' in text or '剛剛' in text:
        return today
        
    return None

def scrape_youtube_channel_videos(channel_id: str, tab: str = "streams", limit: Optional[int] = None) -> list:
    """
    透過抓取 YouTube 頻道對應分頁，搭配 InnerTube browse API 分頁技術，
    取得指定數量的影片與直播項目。若 limit 為 None 則抓取所有。
    """
    import json
    import time
    
    url = f"https://www.youtube.com/channel/{channel_id}/{tab}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7"
    }
    
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            html = response.read().decode('utf-8', errors='ignore')
    except Exception as e:
        print(f"Error fetching channel tab page {tab} for {channel_id}: {e}")
        return []
        
    # 提取 INNERTUBE_API_KEY
    api_key_match = re.search(r'"INNERTUBE_API_KEY"\s*:\s*"([^"]+)"', html)
    api_key = api_key_match.group(1) if api_key_match else None
    
    # 提取 ytInitialData
    data_match = re.search(r'ytInitialData\s*=\s*(\{.*?\});', html)
    if not data_match:
        data_match = re.search(r'window\["ytInitialData"\]\s*=\s*(\{.*?\});', html)
        
    if not data_match:
        print(f"ytInitialData not found for tab {tab}")
        return []
        
    try:
        yt_data = json.loads(data_match.group(1))
    except Exception as e:
        print(f"Failed to parse ytInitialData JSON: {e}")
        return []
        
    videos = []
    seen_video_ids = set()
    continuation_token = None
    
    # 智慧解析項目與尋找選取分頁下的 Continuation Token
    tabs = yt_data.get('contents', {}).get('twoColumnBrowseResultsRenderer', {}).get('tabs', [])
    content_node = None
    for t in tabs:
        tr = t.get('tabRenderer', {})
        if tr.get('selected', False):
            content_node = tr.get('content', {})
            break
            
    if not content_node:
        content_node = yt_data

    def parse_lockup_view_model(d):
        nonlocal continuation_token
        if isinstance(d, dict):
            if 'lockupViewModel' in d:
                lvm = d['lockupViewModel']
                vid = lvm.get('contentId')
                if vid and vid not in seen_video_ids:
                    seen_video_ids.add(vid)
                    
                    title = lvm.get('metadata', {}).get('lockupMetadataViewModel', {}).get('title', {}).get('content', '')
                    thumb_url = f"https://img.youtube.com/vi/{vid}/mqdefault.jpg"
                    
                    # 遍歷所有 metadata 欄位，尋找可以成功解析日期的文字
                    pub_date = None
                    metadata_rows = lvm.get('metadata', {}).get('lockupMetadataViewModel', {}).get('metadata', {}).get('contentMetadataViewModel', {}).get('metadataRows', [])
                    if metadata_rows:
                        for row in metadata_rows:
                            parts = row.get('metadataParts', [])
                            for part in parts:
                                txt = part.get('text', {}).get('content', '')
                                if txt:
                                    parsed = parse_relative_date(txt)
                                    if parsed:
                                        pub_date = parsed
                                        break
                            if pub_date:
                                break
                            
                    videos.append({
                        "video_id": vid,
                        "title": title,
                        "thumbnail_url": thumb_url,
                        "published_at": pub_date
                    })
            
            for k in ["videoRenderer", "gridVideoRenderer"]:
                if k in d:
                    vr = d[k]
                    vid = vr.get("videoId")
                    if vid and vid not in seen_video_ids:
                        seen_video_ids.add(vid)
                        title = ""
                        if "title" in vr:
                            runs = vr["title"].get("runs", [])
                            if runs:
                                title = runs[0].get("text", "")
                        thumb_url = f"https://img.youtube.com/vi/{vid}/mqdefault.jpg"
                        pub_date = None
                        if "publishedTimeText" in vr:
                            pub_date = parse_relative_date(vr["publishedTimeText"].get("simpleText", ""))
                        videos.append({
                            "video_id": vid,
                            "title": title,
                            "thumbnail_url": thumb_url,
                            "published_at": pub_date
                        })
                        
            if "continuationItemRenderer" in d:
                cir = d["continuationItemRenderer"]
                continuation_endpoint = cir.get("continuationEndpoint", {})
                if continuation_endpoint:
                    continuation_command = continuation_endpoint.get("continuationCommand", {})
                    if continuation_command:
                        continuation_token = continuation_command.get("token")
                        
            for v in d.values():
                parse_lockup_view_model(v)
        elif isinstance(d, list):
            for x in d:
                parse_lockup_view_model(x)

    parse_lockup_view_model(content_node)
    
    page = 1
    while continuation_token and api_key and (limit is None or len(videos) < limit):
        time.sleep(0.3)
        browse_url = f"https://www.youtube.com/youtubei/v1/browse?key={api_key}"
        post_data = {
            "context": {
                "client": {
                    "clientName": "WEB",
                    "clientVersion": "2.20240101.01.00",
                    "hl": "zh-TW",
                    "gl": "TW"
                }
            },
            "continuation": continuation_token
        }
        
        req_post = urllib.request.Request(
            browse_url,
            data=json.dumps(post_data).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
        )
        
        try:
            with urllib.request.urlopen(req_post, timeout=15) as resp:
                resp_data = json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            print(f"Error calling InnerTube browse API on page {page} for {channel_id}: {e}")
            break
            
        continuation_token = None
        parse_lockup_view_model(resp_data)
        page += 1
        
    if limit is not None:
        return videos[:limit]
    return videos

@router.post("/{vtuber_id}/sync_youtube", response_model=List[SchemaVideo])
def sync_vtuber_youtube(
    vtuber_id: int,
    limit: Optional[int] = Query(None, description="限制爬取的影片數量，若為 None 則爬取所有"),
    tab: str = Query("streams", description="爬取的分頁類型: streams (直播), videos (影音), all (兩者)"),
    db: Session = Depends(get_db)
):
    """
    爬取同步該主播的直播與影音。
    除了讀取 YouTube RSS XML (最新 15 部) 之外，也會直接爬取該頻道的 Videos (影片) 與 Streams (直播) 頁面，
    支援分頁與筆數限制。
    """
    db_vtuber = get_vtuber(db, vtuber_id=vtuber_id)
    if not db_vtuber:
        raise HTTPException(status_code=404, detail="VTuber not found")
    if not db_vtuber.youtube_channel_id:
        raise HTTPException(
            status_code=400, 
            detail="此主播尚未設定 YouTube Channel ID，無法執行同步爬取！"
        )
        
    rss_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={db_vtuber.youtube_channel_id}"
    
    # 1. 抓取 RSS Feed
    rss_videos = []
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        req = urllib.request.Request(rss_url, headers=headers)
        with urllib.request.urlopen(req, timeout=12) as response:
            xml_data = response.read()
        
        root = ET.fromstring(xml_data)
        ns = {
            'feed': 'http://www.w3.org/2005/Atom',
            'yt': 'http://www.youtube.com/xml/schemas/2015',
            'media': 'http://search.yahoo.com/mrss/'
        }
        for entry in root.findall('feed:entry', ns):
            v_id_el = entry.find('yt:videoId', ns)
            title_el = entry.find('feed:title', ns)
            published_el = entry.find('feed:published', ns)
            
            media_group = entry.find('media:group', ns)
            thumb_url = None
            if media_group is not None:
                thumb_el = media_group.find('media:thumbnail', ns)
                if thumb_el is not None:
                    thumb_url = thumb_el.attrib.get('url')
                    
            if v_id_el is not None and title_el is not None:
                vid = v_id_el.text
                title = title_el.text
                pub_date = None
                if published_el is not None and published_el.text:
                    try:
                        date_part = published_el.text.split('T')[0]
                        pub_date = datetime.strptime(date_part, "%Y-%m-%d").date()
                    except:
                        pass
                rss_videos.append({
                    "video_id": vid,
                    "title": title,
                    "thumbnail_url": thumb_url,
                    "published_at": pub_date
                })
    except Exception as e:
        print(f"RSS sync warning for {db_vtuber.name_main}: {e}")

    # 2. 爬取 YouTube 頻道 Videos & Streams 頁面 (擴展抓取深度)
    scraped_videos = []
    if tab == "all":
        scraped_videos.extend(scrape_youtube_channel_videos(db_vtuber.youtube_channel_id, "streams", limit))
        scraped_videos.extend(scrape_youtube_channel_videos(db_vtuber.youtube_channel_id, "videos", limit))
    else:
        scraped_videos.extend(scrape_youtube_channel_videos(db_vtuber.youtube_channel_id, tab, limit))
        
    # 3. 資料查重與欄位融合
    all_videos_map = {}
    
    for v in scraped_videos:
        all_videos_map[v["video_id"]] = {
            "video_id": v["video_id"],
            "title": v["title"],
            "thumbnail_url": v["thumbnail_url"],
            "published_at": v["published_at"]
        }
        
    for v in rss_videos:
        vid = v["video_id"]
        if vid in all_videos_map:
            all_videos_map[vid]["published_at"] = v["published_at"]
            if v["thumbnail_url"]:
                all_videos_map[vid]["thumbnail_url"] = v["thumbnail_url"]
        else:
            if limit is None or len(all_videos_map) < limit:
                all_videos_map[vid] = v
            
    # 4. 批次寫入資料庫
    synced_entries = []
    for vid, v_info in all_videos_map.items():
        title = v_info["title"]
        thumb_url = v_info["thumbnail_url"]
        pub_date = v_info["published_at"]
        
        db_video = db.scalars(select(DBVideo).where(DBVideo.video_id == vid)).first()
        if not db_video:
            lower_title = title.lower()
            if any(k in lower_title for k in ["歌", "live", "mv", "cover", "original", "singing", "翻唱", "原創"]):
                v_type = "stream_singing"
            else:
                v_type = "stream_other"
                
            db_video = DBVideo(
                video_id=vid,
                title=title,
                published_at=pub_date,
                video_type=v_type,
                thumbnail_url=thumb_url,
                vtuber_id=vtuber_id
            )
            db.add(db_video)
            db.flush()
        else:
            if db_video.vtuber_id is None:
                db_video.vtuber_id = vtuber_id
            if not db_video.thumbnail_url and thumb_url:
                db_video.thumbnail_url = thumb_url
            if not db_video.published_at and pub_date:
                db_video.published_at = pub_date
            db.flush()
            
        synced_entries.append(db_video)
        
    db.commit()
    
    synced_ids = [v.video_id for v in synced_entries]
    results = db.scalars(select(DBVideo).where(DBVideo.video_id.in_(synced_ids))).all()
    return results


