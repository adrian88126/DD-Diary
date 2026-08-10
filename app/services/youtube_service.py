import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import json
import re
import time
from datetime import datetime, date, timedelta
from typing import Optional, List
from sqlalchemy import select
from app.extensions import db
from app.models.vtuber import VTuber
from app.models.video import Video
from app.services.vtuber_service import get_vtuber

def _upgrade_thumb_quality(url: str) -> str:
    """將 YouTube 縮圖 URL 升級為最高畫質 maxresdefault (1280x720)"""
    if not url:
        return url
    upgraded = re.sub(
        r'/(default|mqdefault|hqdefault|sddefault)\.jpg',
        '/maxresdefault.jpg',
        url
    )
    return upgraded

def resolve_youtube_channel_id(channel_input: str) -> str:
    if not channel_input:
        return None
    channel_input = channel_input.strip()
    
    # 1. 檢查是否直接是 Channel ID
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
            
    raise ValueError(f"無法解析 YouTube 頻道 ID。請確保輸入的是正確的 @Handle、頻道網址或 UC 開頭的 ID！(輸入內容: {channel_input})")

def fetch_youtube_channel_info(channel_url: str):
    channel_id = resolve_youtube_channel_id(channel_url)
        
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
        raise Exception(f"無法獲取頻道頁面: {e}")

    data_match = re.search(r'ytInitialData\s*=\s*(\{.*?\});', html)
    if not data_match:
        raise Exception("解析頻道資料失敗：找不到 ytInitialData")
        
    try:
        data = json.loads(data_match.group(1))
    except Exception as e:
        raise Exception(f"解析 JSON 失敗: {e}")
    
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
        "avatar_url": avatar_url,
        "banner_url": banner_url
    }

def parse_relative_date(text: str) -> Optional[date]:
    if not text:
        return None
    text = text.strip().lower()
    
    text = re.sub(r'^(streamed|直播於|發布於|直播時間：|直播結束於|已播完|預定發布時間：|發布時間：)\s*', '', text)
    
    m_exact = re.search(r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})', text)
    if m_exact:
        try:
            return date(int(m_exact.group(1)), int(m_exact.group(2)), int(m_exact.group(3)))
        except ValueError:
            pass

    m_zh = re.search(r'(\d{4})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日', text)
    if m_zh:
        try:
            return date(int(m_zh.group(1)), int(m_zh.group(2)), int(m_zh.group(3)))
        except ValueError:
            pass
            
    today = date.today()
    
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

def is_date_approximate(text: str) -> bool:
    if not text:
        return False
    text = text.lower()
    if re.search(r'\d{4}[/-]\d{1,2}[/-]\d{1,2}', text) or re.search(r'\d{4}\s*年\s*\d{1,2}\s*月\s*\d{1,2}\s*日', text):
        return False
    relative_keywords = ['day', '天', 'hour', '小時', 'week', '週', '星期', 'month', '月', 'year', '年', 'yesterday', '昨天', '前天', 'minute', '分鐘', 'second', '秒', '剛剛', 'ago', '前']
    for kw in relative_keywords:
        if kw in text:
            return True
    return False

def fetch_exact_youtube_date_helper(video_id: str) -> Optional[date]:
    info = fetch_single_video_info(video_id)
    return info.get("published_at") if info else None

def fetch_single_video_info(video_url_or_id: str) -> Optional[dict]:
    video_id = video_url_or_id
    if "youtube.com" in video_id or "youtu.be" in video_id:
        m = re.search(r'(?:v=|youtu\.be/|/v/|/embed/|/shorts/)([a-zA-Z0-9_-]{11})', video_id)
        if m:
            video_id = m.group(1)
            
    watch_url = f"https://www.youtube.com/watch?v={video_id}"
    try:
        req = urllib.request.Request(
            watch_url, 
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept-Language': 'zh-TW,zh;q=0.9,en;q=0.8'
            }
        )
        with urllib.request.urlopen(req, timeout=4.0) as response:
            html = response.read().decode('utf-8', errors='ignore')
            
            title = ""
            pub_date = None
            
            # Fetch Title from meta tags
            m_title = re.search(r'<meta\s+property="og:title"\s+content="([^"]+)"', html)
            if m_title:
                title = m_title.group(1)
            
            # Fetch Date
            data_match = re.search(r'ytInitialData\s*=\s*(\{.*?\});', html)
            if not data_match:
                data_match = re.search(r'window\["ytInitialData"\]\s*=\s*(\{.*?\});', html)
                
            if data_match:
                try:
                    data = json.loads(data_match.group(1))
                    contents = data.get("contents", {}).get("twoColumnWatchNextResults", {}).get(
                        "results", {}
                    ).get("results", {}).get("contents", [])
                    if contents:
                        primary_info = contents[0].get("videoPrimaryInfoRenderer", {})
                        date_text = primary_info.get("dateText", {}).get("simpleText", "")
                        if date_text:
                            clean_date = re.sub(r'^(串流直播日期：|發布日期：|直播時間：|直播日期：)\s*', '', date_text).strip()
                            parsed_date = parse_relative_date(clean_date)
                            if parsed_date:
                                pub_date = parsed_date
                except Exception:
                    pass
            
            if not pub_date:
                m = re.search(r'<meta[^>]*itemprop="datePublished"[^>]*content="(\d{4}-\d{2}-\d{2})', html)
                if not m:
                    m = re.search(r'<meta[^>]*itemprop="uploadDate"[^>]*content="(\d{4}-\d{2}-\d{2})', html)
                if m:
                    pub_date = datetime.strptime(m.group(1), "%Y-%m-%d").date()
                    
            return {
                "video_id": video_id,
                "title": title,
                "thumbnail_url": _upgrade_thumb_quality(f"https://img.youtube.com/vi/{video_id}/mqdefault.jpg"),
                "published_at": pub_date
            }
    except Exception:
        pass
    return None

def scrape_youtube_channel_videos(channel_id: str, tab: str = "streams", limit: Optional[int] = None) -> list:
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
        
    api_key_match = re.search(r'"INNERTUBE_API_KEY"\s*:\s*"([^"]+)"', html)
    api_key = api_key_match.group(1) if api_key_match else None
    
    data_match = re.search(r'ytInitialData\s*=\s*(\{.*?\});', html)
    if not data_match:
        data_match = re.search(r'window\["ytInitialData"\]\s*=\s*(\{.*?\});', html)
        
    if not data_match:
        return []
        
    try:
        yt_data = json.loads(data_match.group(1))
    except Exception:
        return []
        
    videos = []
    seen_video_ids = set()
    continuation_token = None
    
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
                    
                    pub_date = None
                    is_approx = False
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
                                        is_approx = is_date_approximate(txt)
                                        break
                            if pub_date:
                                break
                            
                    videos.append({
                        "video_id": vid,
                        "title": title,
                        "thumbnail_url": thumb_url,
                        "published_at": pub_date,
                        "is_approximate": is_approx
                    })
                    
            if 'shortsLockupViewModel' in d:
                slvm = d['shortsLockupViewModel']
                vid = slvm.get('onTap', {}).get('innertubeCommand', {}).get('reelWatchEndpoint', {}).get('videoId')
                if not vid:
                    vid = slvm.get('onTap', {}).get('innertubeCommand', {}).get('watchEndpoint', {}).get('videoId')
                
                if vid and vid not in seen_video_ids:
                    seen_video_ids.add(vid)
                    title = slvm.get('overlayMetadata', {}).get('primaryText', {}).get('content', '')
                    thumb_url = f"https://img.youtube.com/vi/{vid}/mqdefault.jpg"
                    
                    videos.append({
                        "video_id": vid,
                        "title": title,
                        "thumbnail_url": thumb_url,
                        "published_at": None,
                        "is_approximate": False
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
                        is_approx = False
                        if "publishedTimeText" in vr:
                            txt = vr["publishedTimeText"].get("simpleText", "")
                            pub_date = parse_relative_date(txt)
                            is_approx = is_date_approximate(txt)
                        videos.append({
                            "video_id": vid,
                            "title": title,
                            "thumbnail_url": thumb_url,
                            "published_at": pub_date,
                            "is_approximate": is_approx
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
        except Exception:
            break
            
        continuation_token = None
        parse_lockup_view_model(resp_data)
        page += 1
        
    if limit is not None:
        return videos[:limit]
    return videos

def sync_vtuber_youtube(
    vtuber_id: int,
    limit: Optional[int] = None,
    tab: str = "streams"
):
    db_vtuber = get_vtuber(vtuber_id)
    if not db_vtuber:
        raise ValueError("VTuber not found")
    if not db_vtuber.youtube_channel_id:
        raise ValueError("此主播尚未設定 YouTube Channel ID，無法執行同步爬取！")
        
    rss_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={db_vtuber.youtube_channel_id}"
    
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
                        iso_str = published_el.text.replace('Z', '+00:00')
                        dt = datetime.fromisoformat(iso_str)
                        
                        from datetime import timezone
                        tz_tw = timezone(timedelta(hours=8))
                        dt_tw = dt.astimezone(tz_tw)
                        pub_date = dt_tw.date()
                    except Exception:
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

    scraped_videos = []
    if tab == "all":
        scraped_videos.extend(scrape_youtube_channel_videos(db_vtuber.youtube_channel_id, "streams", limit))
        scraped_videos.extend(scrape_youtube_channel_videos(db_vtuber.youtube_channel_id, "videos", limit))
        scraped_videos.extend(scrape_youtube_channel_videos(db_vtuber.youtube_channel_id, "shorts", limit))
    else:
        scraped_videos.extend(scrape_youtube_channel_videos(db_vtuber.youtube_channel_id, tab, limit))
        
    all_videos_map = {}
    
    for v in scraped_videos:
        all_videos_map[v["video_id"]] = {
            "video_id": v["video_id"],
            "title": v["title"],
            "thumbnail_url": v["thumbnail_url"],
            "published_at": v["published_at"],
            "is_approximate": v.get("is_approximate", False)
        }
        
    for v in rss_videos:
        vid = v["video_id"]
        if vid in all_videos_map:
            all_videos_map[vid]["published_at"] = v["published_at"]
            all_videos_map[vid]["is_approximate"] = False
            if v["thumbnail_url"]:
                all_videos_map[vid]["thumbnail_url"] = v["thumbnail_url"]
        else:
            if limit is None or len(all_videos_map) < limit:
                v["is_approximate"] = False
                all_videos_map[vid] = v
            
    from datetime import date as date_type
    today = date_type.today()
    SCHEDULE_KEYWORDS = ["週表", "周表", "schedule", "予定", "今週", "来週"]
    latest_schedule_thumb = None
    latest_schedule_date = None

    synced_entries = []
    for vid, v_info in all_videos_map.items():
        title = v_info["title"]
        thumb_url = v_info["thumbnail_url"]
        pub_date = v_info["published_at"]
        is_approx = v_info.get("is_approximate", False)

        exact_date = fetch_exact_youtube_date_helper(vid)
        if exact_date:
            pub_date = exact_date

        lower_title = title.lower()
        is_schedule = False
        if any(k in title for k in SCHEDULE_KEYWORDS):
            is_schedule = True
        elif pub_date and (pub_date - today).days > 180:
            is_schedule = True

        db_video = db.session.scalars(select(Video).where(Video.video_id == vid)).first()
        if not db_video:
            if is_schedule:
                v_type = "schedule"
            elif any(k in lower_title for k in ["#short", "#shorts", "shorts"]):
                v_type = "short"
            elif any(k in lower_title for k in ["歌", "live", "mv", "cover", "original", "singing", "翻唱", "原創"]):
                v_type = "stream_singing"
            else:
                v_type = "stream_other"

            db_video = Video(
                video_id=vid,
                title=title,
                published_at=pub_date,
                video_type=v_type,
                thumbnail_url=thumb_url,
                vtuber_id=vtuber_id
            )
            db.session.add(db_video)
            db.session.flush()
        else:
            if is_schedule and db_video.video_type != "schedule":
                db_video.video_type = "schedule"
            elif any(k in lower_title for k in ["#short", "#shorts", "shorts"]) and db_video.video_type in ["stream_singing", "stream_other", "other"]:
                db_video.video_type = "short"
                
            if db_video.vtuber_id is None:
                db_video.vtuber_id = vtuber_id
            if thumb_url:
                db_video.thumbnail_url = thumb_url
            if pub_date:
                db_video.published_at = pub_date
            db.session.flush()

        if is_schedule and thumb_url:
            if latest_schedule_date is None or (pub_date and pub_date > latest_schedule_date):
                latest_schedule_thumb = thumb_url
                latest_schedule_date = pub_date

        synced_entries.append(db_video)

    if latest_schedule_thumb:
        db_vtuber.schedule_image_url = _upgrade_thumb_quality(latest_schedule_thumb)

    db.session.commit()

    synced_ids = [v.video_id for v in synced_entries]
    results = db.session.scalars(select(Video).where(Video.video_id.in_(synced_ids))).all()
    return results

def sync_vtuber_schedule(vtuber_id: int):
    db_vtuber = get_vtuber(vtuber_id)
    if not db_vtuber:
        raise ValueError("VTuber not found")

    SCHEDULE_KEYWORDS = ["週表", "周表", "schedule", "予定", "今週", "来週"]
    today = date.today()

    all_videos = db.session.scalars(
        select(Video).where(Video.vtuber_id == vtuber_id)
    ).all()

    latest_thumb = None
    latest_date = None
    updated_count = 0

    for v in all_videos:
        title = v.title or ""
        is_schedule = False

        if any(k in title for k in SCHEDULE_KEYWORDS):
            is_schedule = True
        elif v.published_at and (v.published_at - today).days > 180:
            is_schedule = True
            
        if is_schedule:
            if v.video_type != "schedule":
                v.video_type = "schedule"
                updated_count += 1
            if v.thumbnail_url:
                if latest_date is None or (v.published_at and v.published_at > latest_date):
                    latest_thumb = v.thumbnail_url
                    latest_date = v.published_at

    schedule_updated = False
    if latest_thumb:
        db_vtuber.schedule_image_url = _upgrade_thumb_quality(latest_thumb)
        schedule_updated = True

    db.session.commit()

    return {
        "success": True,
        "schedule_videos_found": updated_count + (1 if schedule_updated and updated_count == 0 else 0),
        "type_corrected": updated_count,
        "schedule_image_updated": schedule_updated,
        "schedule_image_url": latest_thumb
    }
