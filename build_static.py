import os
import sys
import shutil
import json

sys.stdout.reconfigure(encoding='utf-8')
from sqlalchemy import select
from jinja2 import Environment, FileSystemLoader

from app.database import SessionLocal
from app.models.vtuber import VTuber as DBVTuber
from app.models.video import Video as DBVideo
from app.models.activity import Activity as DBActivity
from app.models.song import Song as DBSong
from app.models.artist import Artist as DBArtist
from app.models.record import SingingRecord as DBRecord

from app.schemas.vtuber import VTuber as SchemaVTuber
from app.schemas.video import Video as SchemaVideo
from app.schemas.activity import Activity as SchemaActivity
from app.schemas.song import Song as SchemaSong
from app.schemas.artist import Artist as SchemaArtist
from app.schemas.record import SingingRecord as SchemaRecord

from app.crud.record import get_records
from fastapi.encoders import jsonable_encoder

def main():
    print("🚀 開始進行靜態網頁打包流程...")
    
    docs_dir = os.path.abspath("docs")
    static_dir = os.path.abspath("app/static")
    templates_dir = os.path.abspath("app/templates")
    
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
    
    # 2. 複製 app/static 內容到 docs/
    print("📂 複製靜態檔案資源...")
    for item in os.listdir(static_dir):
        if item.endswith(".bak"):
            continue
        s = os.path.join(static_dir, item)
        d = os.path.join(docs_dir, item)
        if os.path.isdir(s):
            shutil.copytree(s, d, dirs_exist_ok=True, ignore=shutil.ignore_patterns("*.bak"))
        else:
            if item == "index.html":
                d = os.path.join(docs_dir, "catalog.html")
            shutil.copy2(s, d)
            
    # 3. 建立 docs/data/ 與 docs/share/ 資料夾
    data_dir = os.path.join(docs_dir, "data")
    share_dir = os.path.join(docs_dir, "share")
    os.makedirs(data_dir, exist_ok=True)
    os.makedirs(share_dir, exist_ok=True)
    
    db = SessionLocal()
    try:
        # 4. 匯出全部資料表為 JSON 格式檔案
        print("💾 正在匯出資料表至 JSON 快取...")
        
        songs = db.scalars(select(DBSong).order_by(DBSong.id.desc())).all()
        artists = db.scalars(select(DBArtist).order_by(DBArtist.id.desc())).all()
        vtubers = db.scalars(select(DBVTuber).order_by(DBVTuber.id.asc())).all()
        videos = db.scalars(select(DBVideo).order_by(DBVideo.published_at.desc())).all()
        records = get_records(db, limit=1000000)
        activities = db.scalars(select(DBActivity).order_by(DBActivity.event_date.desc())).all()
        
        songs_data = jsonable_encoder([SchemaSong.model_validate(s) for s in songs])
        artists_data = jsonable_encoder([SchemaArtist.model_validate(a) for a in artists])
        vtubers_data = jsonable_encoder([SchemaVTuber.model_validate(v) for v in vtubers])
        videos_data = jsonable_encoder([SchemaVideo.model_validate(v) for v in videos])
        records_data = jsonable_encoder([SchemaRecord.model_validate(r) for r in records])
        activities_data = jsonable_encoder([SchemaActivity.model_validate(a) for a in activities])
        
        with open(os.path.join(data_dir, "songs.json"), "w", encoding="utf-8") as f:
            json.dump(songs_data, f, ensure_ascii=False, indent=2)
        with open(os.path.join(data_dir, "artists.json"), "w", encoding="utf-8") as f:
            json.dump(artists_data, f, ensure_ascii=False, indent=2)
        with open(os.path.join(data_dir, "vtubers.json"), "w", encoding="utf-8") as f:
            json.dump(vtubers_data, f, ensure_ascii=False, indent=2)
        with open(os.path.join(data_dir, "videos.json"), "w", encoding="utf-8") as f:
            json.dump(videos_data, f, ensure_ascii=False, indent=2)
        with open(os.path.join(data_dir, "records.json"), "w", encoding="utf-8") as f:
            json.dump(records_data, f, ensure_ascii=False, indent=2)
        with open(os.path.join(data_dir, "activities.json"), "w", encoding="utf-8") as f:
            json.dump(activities_data, f, ensure_ascii=False, indent=2)
            
        print("✅ JSON 數據快取匯出完成！")
        
        # 5. 預先渲染 (Pre-render) 主播的靜態分享頁面
        print("🖥️ 正在預先渲染各主播的公開分享頁面...")
        
        env = Environment(loader=FileSystemLoader(templates_dir))
        template = env.get_template("share_profile.html")
        
        for vt in vtubers:
            vt_id = vt.id
            vt_name = vt.name_main
            print(f"   -> 渲染主播: {vt_name} (ID: {vt_id})")
            
            # 獲取該主播關聯資料
            vt_videos = db.scalars(
                select(DBVideo)
                .where(DBVideo.vtuber_id == vt_id)
                .order_by(DBVideo.published_at.desc(), DBVideo.video_id.desc())
            ).all()
            
            vt_activities = db.scalars(
                select(DBActivity)
                .where(DBActivity.vtuber_id == vt_id)
                .order_by(DBActivity.event_date.desc())
            ).all()
            
            vt_records = get_records(db, vtuber_id=vt_id, limit=2000)
            
            # 匯出專屬的主播歌唱紀錄 JSON 快取檔 (供按需/非同步載入)
            vt_records_schema = jsonable_encoder([SchemaRecord.model_validate(r) for r in vt_records])
            with open(os.path.join(data_dir, f"records_vtuber_{vt_id}.json"), "w", encoding="utf-8") as f:
                json.dump(vt_records_schema, f, ensure_ascii=False, indent=2)

            # 序列化成 JSON 字串供頁面預渲染
            vt_json_str = json.dumps(jsonable_encoder(SchemaVTuber.model_validate(vt)), ensure_ascii=False)
            videos_json_str = json.dumps(jsonable_encoder([SchemaVideo.model_validate(v) for v in vt_videos]), ensure_ascii=False)
            activities_json_str = json.dumps(jsonable_encoder([SchemaActivity.model_validate(a) for a in vt_activities]), ensure_ascii=False)
            records_json_str = json.dumps(vt_records_schema, ensure_ascii=False)
            
            # 渲染 HTML (用於分享子目錄，路徑為二層，例如 share/taotaotaotie_ch/)
            html_content = template.render(
                vtuber=vt,
                static_prefix="../../",
                vtuber_json=vt_json_str,
                videos_json=videos_json_str,
                activities_json=activities_json_str,
                records_json=records_json_str
            )
            
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
        
        # 6. 預先渲染 (Pre-render) 門戶首頁大廳 (Lobby) docs/index.html
        print("🖥️ 正在預先渲染網站首頁大廳 (Lobby)...")
        lobby_template = env.get_template("lobby.html")
        lobby_html = lobby_template.render(vtubers=vtubers)
        with open(os.path.join(docs_dir, "index.html"), "w", encoding="utf-8") as f:
            f.write(lobby_html)
        print("✅ 門戶大廳首頁渲染完成！")
        
        print("\n🎉 靜態打包流程全部成功結束！成品已輸出至 docs/ 目錄。")
        
    finally:
        db.close()

if __name__ == "__main__":
    main()
