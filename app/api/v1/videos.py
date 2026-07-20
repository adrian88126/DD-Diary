from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.schemas.video import Video, VideoCreate
from app.crud.video import get_video, get_videos, create_video, update_video_type, delete_video, update_video

router = APIRouter()

@router.get("/", response_model=List[Video])
def read_videos(
    video_type: Optional[str] = Query(None, description="過濾影片類型"),
    vtuber_id: Optional[int] = Query(None, description="過濾發布的主播 ID"),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    db_videos = get_videos(db, video_type=video_type, vtuber_id=vtuber_id, skip=skip, limit=limit)
    return db_videos

import urllib.request
import json
import re

def extract_youtube_id(url_or_id: str) -> str:
    url_or_id = url_or_id.strip()
    # 剛好 11 碼且符合字元集
    if len(url_or_id) == 11 and re.match(r"^[a-zA-Z0-9_-]{11}$", url_or_id):
        return url_or_id
        
    # 常見 YouTube 網址規則正則匹配
    patterns = [
        r"v=([a-zA-Z0-9_-]{11})",
        r"youtu\.be/([a-zA-Z0-9_-]{11})",
        r"embed/([a-zA-Z0-9_-]{11})",
        r"live/([a-zA-Z0-9_-]{11})",
        r"shorts/([a-zA-Z0-9_-]{11})"
    ]
    for pattern in patterns:
        m = re.search(pattern, url_or_id)
        if m:
            return m.group(1)
            
    # 支援手動複製 v=5_VDwjHuIIM 後半截或包含參數的狀況
    if "v=" in url_or_id:
        parts = url_or_id.split("v=")
        if len(parts) > 1:
            potential_id = parts[1][:11]
            if len(potential_id) == 11 and re.match(r"^[a-zA-Z0-9_-]{11}$", potential_id):
                return potential_id
                
    return ""

@router.get("/fetch_youtube_info")
def fetch_youtube_info(video_id: str = Query(..., description="YouTube 影片 ID 或 完整網址")):
    extracted_id = extract_youtube_id(video_id)
    if not extracted_id:
        raise HTTPException(status_code=400, detail="無法解析的 YouTube 影片 ID 或網址")
        
    res_data = {
        "video_id": extracted_id,
        "title": "",
        "author_name": "",
        "published_date": "",
        "thumbnail_url": f"https://img.youtube.com/vi/{extracted_id}/hqdefault.jpg"
    }
    
    # 1. 抓取 oEmbed 取得標題與封面
    oembed_url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={extracted_id}&format=json"
    try:
        req = urllib.request.Request(
            oembed_url, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        )
        with urllib.request.urlopen(req, timeout=3.0) as response:
            if response.status == 200:
                data = json.loads(response.read().decode('utf-8'))
                res_data["title"] = data.get("title", "")
                res_data["author_name"] = data.get("author_name", "")
                res_data["thumbnail_url"] = data.get("thumbnail_url", res_data["thumbnail_url"])
    except Exception:
        pass
        
    # 2. 抓取影片網頁 HTML 取得 Google SEO 發布日期 (如 <meta itemprop="datePublished" content="2025-12-30">)
    watch_url = f"https://www.youtube.com/watch?v={extracted_id}"
    try:
        req = urllib.request.Request(
            watch_url, 
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept-Language': 'zh-TW,zh;q=0.9,en;q=0.8'
            }
        )
        with urllib.request.urlopen(req, timeout=4.0) as response:
            html = response.read().decode('utf-8')
            m = re.search(r'<meta[^>]*itemprop="datePublished"[^>]*content="(\d{4}-\d{2}-\d{2})', html)
            if not m:
                m = re.search(r'<meta[^>]*itemprop="uploadDate"[^>]*content="(\d{4}-\d{2}-\d{2})', html)
            if m:
                res_data["published_date"] = m.group(1)
    except Exception:
        pass
        
    return res_data

@router.get("/{video_id}", response_model=Video)
def read_video(video_id: str, db: Session = Depends(get_db)):
    db_video = get_video(db, video_id=video_id)
    if not db_video:
        raise HTTPException(status_code=404, detail="Video not found")
    return db_video

@router.post("/", response_model=Video)
def create_new_video(video: VideoCreate, db: Session = Depends(get_db)):
    db_video = get_video(db, video_id=video.video_id)
    if db_video:
        raise HTTPException(status_code=400, detail="Video already exists")
    return create_video(db=db, video=video)

@router.patch("/{video_id}/type", response_model=Video)
def modify_video_type(
    video_id: str,
    video_type: str = Query(..., description="修改後的影片類型"),
    db: Session = Depends(get_db)
):
    db_video = update_video_type(db, video_id=video_id, video_type=video_type)
    if not db_video:
        raise HTTPException(status_code=404, detail="Video not found")
    return db_video

@router.delete("/{video_id}")
def delete_existing_video(video_id: str, db: Session = Depends(get_db)):
    success = delete_video(db=db, video_id=video_id)
    if not success:
        raise HTTPException(status_code=404, detail="Video not found")
    return {"message": "Video deleted successfully"}

@router.put("/{video_id}", response_model=Video)
def update_existing_video(video_id: str, video: VideoCreate, db: Session = Depends(get_db)):
    db_video = update_video(
        db=db,
        video_id=video_id,
        title=video.title,
        published_at=video.published_at,
        video_type=video.video_type,
        thumbnail_url=video.thumbnail_url,
        vtuber_id=video.vtuber_id
    )
    if not db_video:
        raise HTTPException(status_code=404, detail="Video not found")
    return db_video


