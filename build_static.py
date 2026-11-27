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
from app.models.song import Song
from app.models.record import SingingRecord

from app.services.artist_service import get_artist_catalog_data
from app.services.share_service import get_vtuber_profile_payload

from flask import render_template


def build_language_site(
    app,
    vtubers,
    vtuber_payloads,
    songs_count,
    records_count,
    videos_count,
    total_artists,
    lang,
    base_dir,
    share_dir,
    is_sub_lang=False,
):
    with app.test_request_context(environ_base={'HTTP_COOKIE': f'lang={lang}'}):
        print(f"🖥️ 正在預先渲染 [{lang}] 版本的各主播公開分享頁面...")

        for vt in vtubers:
            vt_id = vt.id
            payload = vtuber_payloads[vt_id]

            if is_sub_lang:
                static_link_zh = f"../../../share/{vt_id}/index.html"
                static_link_en = "./index.html"
                static_replace_old = 'href="/static/'
                static_replace_new = 'href="../../../static/'
                static_src_old = 'src="/static/'
                static_src_new = 'src="../../../static/'
                static_vtuber_data_url = f"../../../static/data/vtuber_{vt_id}.js"
            else:
                static_link_zh = "./index.html"
                static_link_en = f"../../en/share/{vt_id}/index.html"
                static_replace_old = 'href="/static/'
                static_replace_new = 'href="../../static/'
                static_src_old = 'src="/static/'
                static_src_new = 'src="../../static/'
                static_vtuber_data_url = f"../../static/data/vtuber_{vt_id}.js"

            html_content = render_template(
                'share/profile.html',
                vtuber=vt,
                vtuber_dict=payload["vtuber_dict"],
                videos_data=[],
                activities_data=[],
                records_data=[],
                clips=payload["clips_data"],
                clips_data=[],
                all_clip_authors=payload["all_clip_authors"],
                is_static=True,
                static_link_zh=static_link_zh,
                static_link_en=static_link_en,
                lobby_url="../../index.html",
                artists_page_url="../../artists/index.html",
                static_vtuber_data_url=static_vtuber_data_url,
            )

            html_content = html_content.replace(static_replace_old, static_replace_new)
            html_content = html_content.replace(static_src_old, static_src_new)
            html_content = html_content.replace('href="/"', 'href="../../index.html"')

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

            redirect_html_lang = 'en' if lang == 'en' else 'zh-Hant'
            for alias_path in unique_paths[1:]:
                alias_dir = os.path.join(share_dir, alias_path)
                os.makedirs(alias_dir, exist_ok=True)
                redirect_html = (
                    f'<!DOCTYPE html><html lang="{redirect_html_lang}"><head><meta charset="UTF-8">'
                    f'<meta http-equiv="refresh" content="0;url=../{primary_path}/">'
                    f'<script>window.location.href="../{primary_path}/";</script>'
                    f'<title>Redirecting...</title></head><body><p>Redirecting...</p></body></html>'
                )
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

        lobby_html = render_template(
            "main/lobby.html",
            vtubers=vtubers,
            total_songs=songs_count,
            total_records=records_count,
            total_videos=videos_count,
            total_artists=total_artists,
            is_static=True,
            static_link_zh=static_link_zh,
            static_link_en=static_link_en,
            lobby_url="index.html",
            artists_url="./artists/index.html",
        )

        lobby_html = lobby_html.replace(static_replace_old, static_replace_new)
        lobby_html = lobby_html.replace(static_src_old, static_src_new)
        lobby_html = lobby_html.replace(share_replace_old, share_replace_new)

        with open(os.path.join(base_dir, "index.html"), "w", encoding="utf-8") as f:
            f.write(lobby_html)
        print(f"✅ [{lang}] 門戶大廳首頁渲染完成！")

        print(f"🎵 正在預先渲染 [{lang}] 原唱歌手歌單專頁 (/artists)...")
        artists_dir = os.path.join(base_dir, "artists")
        os.makedirs(artists_dir, exist_ok=True)
        if is_sub_lang:
            art_static_zh = "../../artists/index.html"
            art_static_en = "./index.html"
            art_static_prefix = "../../static/"
            art_data_url = "../../static/data/artist_catalog.js"
        else:
            art_static_zh = "./index.html"
            art_static_en = "../en/artists/index.html"
            art_static_prefix = "../static/"
            art_data_url = "../static/data/artist_catalog.js"

        artists_html = render_template(
            "main/artists.html",
            catalog_data={"vtubers": [], "artists": []},
            is_static=True,
            static_link_zh=art_static_zh,
            static_link_en=art_static_en,
            lobby_url="../index.html",
            artists_url="./index.html",
            static_data_url=art_data_url,
            share_base_url="../share/",
        )
        artists_html = artists_html.replace('href="/static/', f'href="{art_static_prefix}')
        artists_html = artists_html.replace('src="/static/', f'src="{art_static_prefix}')
        with open(os.path.join(artists_dir, "index.html"), "w", encoding="utf-8") as f:
            f.write(artists_html)
        print(f"✅ [{lang}] 原唱歌手歌單專頁渲染完成！")


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
        print("📁 建立 docs 資料夾...")
        os.makedirs(docs_dir, exist_ok=True)

    print("📂 複製靜態檔案資源 (排除備份檔、舊版遺骸與後台專用資源)...")
    docs_static = os.path.join(docs_dir, "static")
    static_css_dir = os.path.join(static_dir, "css")
    static_js_dir = os.path.join(static_dir, "js")

    def _ignore_static(src, names):
        ignored = {n for n in names if n.endswith(".bak")}
        abs_src = os.path.abspath(src)
        if abs_src == static_dir:
            ignored |= {"share.css", "template.csv", "template.json"} & set(names)
        elif abs_src == static_css_dir:
            ignored |= {"admin.css"} & set(names)
        elif abs_src == static_js_dir:
            ignored |= {"admin.js", "portal.js", "config.js", "state.js"} & set(names)
        return list(ignored)

    shutil.copytree(static_dir, docs_static, dirs_exist_ok=True, ignore=_ignore_static)

    share_dir_zh = os.path.join(docs_dir, "share")
    en_dir = os.path.join(docs_dir, "en")
    share_dir_en = os.path.join(en_dir, "share")

    os.makedirs(share_dir_zh, exist_ok=True)
    os.makedirs(share_dir_en, exist_ok=True)

    data_dir = os.path.join(docs_static, "data")
    os.makedirs(data_dir, exist_ok=True)

    vtuber_payloads = {}
    with app.app_context():
        vtubers = db.session.scalars(select(VTuber).order_by(VTuber.id.asc())).all()
        songs_count = db.session.query(Song).count()
        records_count = db.session.query(SingingRecord).count()
        videos_count = db.session.query(Video).count()
        catalog_data = get_artist_catalog_data()
        total_artists = len(catalog_data.get("artists", []))

        for vt in vtubers:
            payload = get_vtuber_profile_payload(vt)
            vtuber_payloads[vt.id] = payload
            vt_js_path = os.path.join(data_dir, f"vtuber_{vt.id}.js")
            vt_data_bundle = {
                "vtuber": payload["vtuber_dict"],
                "videos": payload["videos_data"],
                "activities": payload["activities_data"],
                "records": payload["records_data"],
                "clips": payload["clips_data"],
            }
            with open(vt_js_path, "w", encoding="utf-8") as f:
                f.write("window.VTUBER_PROFILE_DATA = ")
                json.dump(vt_data_bundle, f, ensure_ascii=False, separators=(",", ":"))
                f.write(";\n")
            print(f"📦 已輸出主播資料檔：vtuber_{vt.id}.js")

    catalog_js_path = os.path.join(data_dir, "artist_catalog.js")
    with open(catalog_js_path, "w", encoding="utf-8") as f:
        f.write("window.ARTIST_CATALOG_DATA = ")
        json.dump(catalog_data, f, ensure_ascii=False, separators=(",", ":"))
        f.write(";\n")
    print(f"📦 已輸出共用歌手歌單資料檔：{catalog_js_path} ({total_artists} 位歌手)")

    build_language_site(
        app, vtubers, vtuber_payloads, songs_count, records_count, videos_count, total_artists,
        lang='zh', base_dir=docs_dir, share_dir=share_dir_zh, is_sub_lang=False,
    )
    build_language_site(
        app, vtubers, vtuber_payloads, songs_count, records_count, videos_count, total_artists,
        lang='en', base_dir=en_dir, share_dir=share_dir_en, is_sub_lang=True,
    )

    robots_path = os.path.join(docs_dir, "robots.txt")
    with open(robots_path, "w", encoding="utf-8", newline="\n") as f:
        f.write("User-agent: *\nAllow: /\n")
    print("🤖 已生成 docs/robots.txt")

    print("\n🎉 靜態雙語打包流程全部成功結束！成品已輸出至 docs/ 目錄。")


if __name__ == "__main__":
    main()
