import os
import sys
import shutil
import json

sys.stdout.reconfigure(encoding='utf-8')
from app import create_app
from app.extensions import db
from sqlalchemy import select

from app.models.vtuber import VTuber
from app.models.video import Video
from app.models.activity import Activity
from app.models.song import Song
from app.models.artist import Artist
from app.models.record import SingingRecord

from flask import render_template, url_for

def serialize_video(v):
    return {
        "video_id": v.video_id,
        "title": v.title,
        "published_at": v.published_at.isoformat() if v.published_at else None,
        "video_type": v.video_type,
        "thumbnail_url": v.thumbnail_url
    }

def serialize_activity(a):
    return {
        "id": a.id,
        "title": a.title,
        "event_date": a.event_date.isoformat() if a.event_date else None,
        "activity_type": a.activity_type,
        "link_url": a.link_url
    }

def serialize_record(r):
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
        
    return {
        "id": r.id,
        "song_id": r.song_id,
        "video_id": r.video_id,
        "timestamp_seconds": r.timestamp_seconds,
        "note": r.note,
        "song": song_dict,
        "video": video_dict
    }

def main():
    print("🚀 開始進行靜態網頁打包流程 (Flask 版)...")
    
    app = create_app()
    
    docs_dir = os.path.abspath("docs")
    static_dir = os.path.abspath("app/static")
    
    def remove_readonly(func, path, _):
        import stat
        try:
            os.chmod(path, stat.S_IWRITE)
            func(path)
        except Exception:
            pass

    # 1. 重建 docs/ 資料夾
    if os.path.exists(docs_dir):
        print(f"🗑️ 清空現有 docs 資料夾內容: {docs_dir}")
        for item in os.listdir(docs_dir):
            path = os.path.join(docs_dir, item)
            try:
                if os.path.isdir(path):
                    shutil.rmtree(path, onerror=remove_readonly)
                else:
                    import stat
                    os.chmod(path, stat.S_IWRITE)
                    os.remove(path)
            except Exception:
                pass
    else:
        print(f"📁 建立 docs 資料夾...")
        os.makedirs(docs_dir, exist_ok=True)
    
    # 2. 複製 app/static 內容到 docs/static/
    # 注意：我們將靜態檔案統一放在 docs/static 以對應 /static/... 的絕對路徑
    print("📂 複製靜態檔案資源...")
    docs_static = os.path.join(docs_dir, "static")
    shutil.copytree(static_dir, docs_static, dirs_exist_ok=True, ignore=shutil.ignore_patterns("*.bak"))
            
    # 3. 建立 docs/share/ 資料夾
    share_dir = os.path.join(docs_dir, "share")
    os.makedirs(share_dir, exist_ok=True)
    
    with app.test_request_context():
        # 設定 request 環境讓 url_for 產生相對根目錄的路徑
        # 例如: url_for('static', filename='css/base.css') -> /static/css/base.css
        
        # 取得所有資料
        vtubers = db.session.scalars(select(VTuber).order_by(VTuber.id.asc())).all()
        songs_count = db.session.query(Song).count()
        records_count = db.session.query(SingingRecord).count()
        videos_count = db.session.query(Video).count()
        
        # 5. 預先渲染 (Pre-render) 主播的靜態分享頁面
        print("🖥️ 正在預先渲染各主播的公開分享頁面...")
        
        for vt in vtubers:
            vt_id = vt.id
            vt_name = vt.name_main
            print(f"   -> 渲染主播: {vt_name} (ID: {vt_id})")
            
            # 獲取該主播關聯資料
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
            
            # 對於合唱，透過關聯查詢
            vt_records = db.session.scalars(
                select(SingingRecord)
                .where(SingingRecord.singers.any(id=vt_id))
                .order_by(SingingRecord.id.desc())
            ).all()
            
            vt_dict = {
                "id": vt.id,
                "name_main": vt.name_main,
                "theme_color": vt.theme_color,
                "social_links": vt.social_links
            }
            
            # 序列化成 JSON 字串供頁面預渲染
            vt_json_str = json.dumps(vt_dict, ensure_ascii=False)
            videos_json_str = json.dumps([serialize_video(v) for v in vt_videos], ensure_ascii=False)
            activities_json_str = json.dumps([serialize_activity(a) for a in vt_activities], ensure_ascii=False)
            records_json_str = json.dumps([serialize_record(r) for r in vt_records], ensure_ascii=False)
            
            # 渲染 HTML
            html_content = render_template('share/profile.html', 
                vtuber=vt, 
                vtuber_json=vt_json_str,
                videos_json=videos_json_str,
                activities_json=activities_json_str,
                records_json=records_json_str
            )
            
            # 如果我們要把靜態網站放上 GitHub Pages 且不在根網域
            # /static/... 這種絕對路徑可能會失效。
            # 所以我們要將 /static/ 替換為 ../../static/ (因為它在 docs/share/<id>/index.html)
            html_content = html_content.replace('href="/static/', 'href="../../static/')
            html_content = html_content.replace('src="/static/', 'src="../../static/')
            
            # 決定 Primary slug 與別名 (Aliases)
            all_paths = []
            if vt.name_romaji:
                cleaned_name = vt.name_romaji.strip().lower()
                all_paths.append(cleaned_name.replace(" ", "_"))
                all_paths.append(cleaned_name.replace(" ", "-"))
            all_paths.append(str(vt_id))
            
            # 去重並保留順序
            unique_paths = []
            seen = set()
            for p in all_paths:
                if p not in seen:
                    seen.add(p)
                    unique_paths.append(p)
                    
            primary_path = unique_paths[0]
            
            # 1. 寫入主要路徑 (Primary Slug) 完整頁面
            primary_dir = os.path.join(share_dir, primary_path)
            os.makedirs(primary_dir, exist_ok=True)
            with open(os.path.join(primary_dir, "index.html"), "w", encoding="utf-8") as f:
                f.write(html_content)
                
            # 2. 寫入別名路徑 (Alias Paths) 輕量級 HTML 重定向檔
            for alias_path in unique_paths[1:]:
                alias_dir = os.path.join(share_dir, alias_path)
                os.makedirs(alias_dir, exist_ok=True)
                redirect_html = f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta http-equiv="refresh" content="0;url=../{primary_path}/">
    <script>window.location.href="../{primary_path}/";</script>
    <title>Redirecting to {vt_name}...</title>
</head>
<body>
    <p>Redirecting to <a href="../{primary_path}/">../{primary_path}/</a></p>
</body>
</html>"""
                with open(os.path.join(alias_dir, "index.html"), "w", encoding="utf-8") as f:
                    f.write(redirect_html)
            
        print("✅ 主播分享頁面靜態渲染完成！")
        
        # 6. 預先渲染門戶首頁大廳 (Lobby) docs/index.html
        print("🖥️ 正在預先渲染網站首頁大廳 (Lobby)...")
        lobby_html = render_template("main/lobby.html",
            vtubers=vtubers,
            total_songs=songs_count,
            total_records=records_count,
            total_videos=videos_count
        )
        # 替換靜態資源路徑 (根目錄下，所以用 ./static/ 即可)
        lobby_html = lobby_html.replace('href="/static/', 'href="./static/')
        lobby_html = lobby_html.replace('src="/static/', 'src="./static/')
        lobby_html = lobby_html.replace('href="/share/', 'href="./share/')
        
        with open(os.path.join(docs_dir, "index.html"), "w", encoding="utf-8") as f:
            f.write(lobby_html)
        print("✅ 門戶大廳首頁渲染完成！")
        
        print("\n🎉 靜態打包流程全部成功結束！成品已輸出至 docs/ 目錄。")
        print("\n📌 推薦的 GitHub 推播步驟：")
        print("----------------------------------------")
        print("git add .")
        print("git commit -m \"Update static pages\"")
        print("git push")
        print("----------------------------------------")
        print("只要您的 GitHub 專案有將 Pages 指定到 /docs 目錄，即可自動更新！")

if __name__ == "__main__":
    main()
