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
from app.models.record import SingingRecord
from app.models.clip import Clip, ClipAuthor

from flask import render_template

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

def build_language_site(app, vtubers, songs_count, records_count, videos_count, lang, base_dir, share_dir, is_sub_lang=False):
    # Setup request context and force cookie to the selected lang so Flask-Babel/i18n loads correct language
    with app.test_request_context(environ_base={'HTTP_COOKIE': f'lang={lang}'}):
        
        print(f"🖥️ 正在預先渲染 [{lang}] 版本的各主播公開分享頁面...")
        
        for vt in vtubers:
            vt_id = vt.id
            vt_name = vt.name_main
            
            vt_videos = db.session.scalars(select(Video).where(Video.vtuber_id == vt_id).order_by(Video.published_at.desc(), Video.video_id.desc())).all()
            vt_activities = db.session.scalars(select(Activity).where(Activity.vtuber_id == vt_id).order_by(Activity.event_date.desc())).all()
            vt_records = db.session.scalars(select(SingingRecord).where(SingingRecord.singers.any(id=vt_id)).order_by(SingingRecord.id.desc())).all()
            
            vt_dict = {
                "id": vt.id,
                "name_main": vt.name_main,
                "name_ja": vt.name_ja,
                "name_zh": vt.name_zh,
                "name_romaji": vt.name_romaji,
                "description": vt.description,
                "avatar_url": vt.avatar_url,
                "banner_url": vt.banner_url,
                "theme_color": vt.theme_color,
                "social_links": vt.social_links
            }
            
            vt_clips = db.session.scalars(select(Clip).join(Clip.vtubers).where(VTuber.id == vt_id).order_by(Clip.id.desc())).all()
            clips_data = []
            clip_authors_map = {}
            for c in vt_clips:
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
            
            videos_data = [serialize_video(v) for v in vt_videos]
            activities_data = [serialize_activity(a) for a in vt_activities]
            records_data = [serialize_record(r) for r in vt_records]
            
            if is_sub_lang:
                static_link_zh = f"../../../share/{vt_id}/index.html"
                static_link_en = "./index.html"
                static_replace_old = 'href="/static/'
                static_replace_new = 'href="../../../static/'
                static_src_old = 'src="/static/'
                static_src_new = 'src="../../../static/'
            else:
                static_link_zh = "./index.html"
                static_link_en = f"../../en/share/{vt_id}/index.html"
                static_replace_old = 'href="/static/'
                static_replace_new = 'href="../../static/'
                static_src_old = 'src="/static/'
                static_src_new = 'src="../../static/'
                
            html_content = render_template('share/profile.html', 
                vtuber=vt, 
                vtuber_dict=vt_dict,
                videos=vt_videos,
                videos_data=videos_data,
                activities=vt_activities,
                activities_data=activities_data,
                records=vt_records,
                records_data=records_data,
                clips=vt_clips,
                clips_data=clips_data,
                all_clip_authors=all_clip_authors,
                is_static=True,
                static_link_zh=static_link_zh,
                static_link_en=static_link_en,
                lobby_url="../../index.html"
            )
            
            html_content = html_content.replace(static_replace_old, static_replace_new)
            html_content = html_content.replace(static_src_old, static_src_new)
            html_content = html_content.replace('href="/"', 'href="../../index.html"')
            
            # Paths logic
            all_paths = []
            if vt.name_romaji:
                cleaned_name = vt.name_romaji.strip().lower()
                all_paths.append(cleaned_name.replace(" ", "_"))
                all_paths.append(cleaned_name.replace(" ", "-"))
            all_paths.append(str(vt_id))
            
            unique_paths = []
            seen = set()
            for p in all_paths:
                if p not in seen:
                    seen.add(p)
                    unique_paths.append(p)
                    
            primary_path = unique_paths[0]
            primary_dir = os.path.join(share_dir, primary_path)
            os.makedirs(primary_dir, exist_ok=True)
            with open(os.path.join(primary_dir, "index.html"), "w", encoding="utf-8") as f:
                f.write(html_content)
                
            for alias_path in unique_paths[1:]:
                alias_dir = os.path.join(share_dir, alias_path)
                os.makedirs(alias_dir, exist_ok=True)
                redirect_html = f"""<!DOCTYPE html><html lang="zh-TW"><head><meta charset="UTF-8"><meta http-equiv="refresh" content="0;url=../{primary_path}/"><script>window.location.href="../{primary_path}/";</script><title>Redirecting...</title></head><body><p>Redirecting...</p></body></html>"""
                with open(os.path.join(alias_dir, "index.html"), "w", encoding="utf-8") as f:
                    f.write(redirect_html)
            
        print(f"✅ [{lang}] 主播分享頁面靜態渲染完成！")
        
        print(f"🖥️ 正在預先渲染 [{lang}] 網站首頁大廳 (Lobby)...")
        if is_sub_lang:
            static_link_zh = "../index.html"
            static_link_en = "./index.html"
            static_replace_old = 'href="/static/'
            static_replace_new = 'href="../static/'
            static_src_old = 'src="/static/'
            static_src_new = 'src="../static/'
            share_replace_old = 'href="/share/'
            share_replace_new = 'href="./share/'
        else:
            static_link_zh = "./index.html"
            static_link_en = "./en/index.html"
            static_replace_old = 'href="/static/'
            static_replace_new = 'href="./static/'
            static_src_old = 'src="/static/'
            static_src_new = 'src="./static/'
            share_replace_old = 'href="/share/'
            share_replace_new = 'href="./share/'

        lobby_html = render_template("main/lobby.html",
            vtubers=vtubers,
            total_songs=songs_count,
            total_records=records_count,
            total_videos=videos_count,
            is_static=True,
            static_link_zh=static_link_zh,
            static_link_en=static_link_en,
            lobby_url="index.html"
        )
        
        lobby_html = lobby_html.replace(static_replace_old, static_replace_new)
        lobby_html = lobby_html.replace(static_src_old, static_src_new)
        lobby_html = lobby_html.replace(share_replace_old, share_replace_new)
        
        with open(os.path.join(base_dir, "index.html"), "w", encoding="utf-8") as f:
            f.write(lobby_html)
        print(f"✅ [{lang}] 門戶大廳首頁渲染完成！")


def main():
    print("🚀 開始進行靜態網頁打包流程 (支援多國語系中英雙語)...")
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
    print("📂 複製靜態檔案資源...")
    docs_static = os.path.join(docs_dir, "static")
    shutil.copytree(static_dir, docs_static, dirs_exist_ok=True, ignore=shutil.ignore_patterns("*.bak"))
            
    # 3. 建立 zh (預設根目錄) 與 en 目錄
    share_dir_zh = os.path.join(docs_dir, "share")
    en_dir = os.path.join(docs_dir, "en")
    share_dir_en = os.path.join(en_dir, "share")
    
    os.makedirs(share_dir_zh, exist_ok=True)
    os.makedirs(share_dir_en, exist_ok=True)
    
    with app.app_context():
        # Get overall data
        vtubers = db.session.scalars(select(VTuber).order_by(VTuber.id.asc())).all()
        songs_count = db.session.query(Song).count()
        records_count = db.session.query(SingingRecord).count()
        videos_count = db.session.query(Video).count()
        
    # Build Default Chinese Site (Root)
    build_language_site(app, vtubers, songs_count, records_count, videos_count, lang='zh', base_dir=docs_dir, share_dir=share_dir_zh, is_sub_lang=False)
    
    # Build English Site (/en/)
    build_language_site(app, vtubers, songs_count, records_count, videos_count, lang='en', base_dir=en_dir, share_dir=share_dir_en, is_sub_lang=True)
        
    print("\n🎉 靜態雙語打包流程全部成功結束！成品已輸出至 docs/ 目錄。")
    print("\n📌 推薦的 GitHub 推播步驟：")
    print("----------------------------------------")
    print("git add .")
    print("git commit -m \"Update static pages (Dual Language)\"")
    print("git push")
    print("----------------------------------------")

if __name__ == "__main__":
    main()
