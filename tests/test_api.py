from app import create_app
from app.extensions import db
from app.services import (
    vtuber_service,
    artist_service,
    song_service,
    activity_service,
    video_service,
    clip_service,
)


def run_tests():
    print("🔍 [2/4] 開始後端 API、管理後台與全模組 CRUD 沙盒測試...")
    errors = []

    import os
    import shutil
    import tempfile
    from app.config import Config

    src_db_path = os.path.abspath("vtuber_songs.db")
    with tempfile.TemporaryDirectory() as tmpdir:
        test_db_path = os.path.join(tmpdir, "vtuber_songs_test.db")
        if os.path.exists(src_db_path):
            shutil.copy2(src_db_path, test_db_path)

        class TestConfig(Config):
            TESTING = True
            LOGIN_DISABLED = True
            WTF_CSRF_ENABLED = False
            SQLALCHEMY_DATABASE_URI = "sqlite:///" + test_db_path.replace("\\", "/")

        app = create_app(TestConfig)
        client = app.test_client()

        with app.app_context():
            # 1. 測試各個公開頁面、API 與管理後台頁面 (HTTP GET 必須為 200)
            endpoints = [
                "/",
                "/artists",
                "/share/1",
                "/api/v1/artists",
                "/api/v1/songs",
                "/api/v1/vtubers",
                "/api/v1/records",
                "/api/v1/activities",
                "/admin/dashboard",
                "/admin/vtubers",
                "/admin/songs",
                "/admin/artists",
                "/admin/videos",
                "/admin/singing_streams",
                "/admin/records",
                "/admin/activities",
                "/admin/clips",
                "/admin/clip_authors",
                "/admin/diagnostics",
                "/admin/backup/export",
                "/admin/artists/create",
            ]

            for ep in endpoints:
                try:
                    res = client.get(ep)
                    if res.status_code != 200:
                        errors.append(f"GET {ep} 響應異常，狀態碼：{res.status_code}")
                except Exception as e:
                    errors.append(f"GET {ep} 執行錯誤：{e}")

            # 1b. 驗證 /auth/logout 與舊 _form 路由導向不再報 500
            try:
                res_logout = client.get("/auth/logout")
                if res_logout.status_code != 302 or not (res_logout.headers.get("Location", "").endswith("/")):
                    errors.append(f"GET /auth/logout 導向異常：{res_logout.status_code} -> {res_logout.headers.get('Location')}")
                res_vt_create = client.get("/admin/vtubers/create")
                if res_vt_create.status_code != 302:
                    errors.append(f"GET /admin/vtubers/create 響應異常：{res_vt_create.status_code}")
            except Exception as e:
                errors.append(f"路由導向驗證失敗：{e}")

            # 2. 沙盒測試：VTuber 建立、更新與刪除
            temp_vt_id = None
            try:
                test_vt = vtuber_service.create_vtuber({
                    "name_main": "__TEST_AUTO_VTUBER__",
                    "description": "自動化測試專用沙盒主播"
                })
                if not test_vt or not test_vt.id:
                    errors.append("VTuber 沙盒建立失敗")
                else:
                    temp_vt_id = test_vt.id
                    vtuber_service.update_vtuber(temp_vt_id, {"name_zh": "測試主播更新"})
            except Exception as e:
                errors.append(f"VTuber CRUD 沙盒測試異常：{e}")
            finally:
                if temp_vt_id:
                    try:
                        vtuber_service.delete_vtuber(temp_vt_id)
                    except Exception:
                        db.session.rollback()

            # 3. 沙盒測試：歌手即時快速建立 API (Quick Create Artist) 與歌曲綁定 CRUD
            temp_art_id = None
            temp_song_id = None
            try:
                res = client.post("/api/v1/artists/quick_create", json={"name_main": "__TEST_QUICK_ARTIST__"})
                if res.status_code != 200:
                    errors.append(f"POST /api/v1/artists/quick_create 響應異常: {res.status_code}")
                else:
                    data = res.get_json()
                    if not data or not data.get("success") or not data.get("artist"):
                        errors.append("POST /api/v1/artists/quick_create 返回格式異常")
                    else:
                        temp_art_id = data["artist"]["id"]
                        updated_art = artist_service.update_artist(
                            temp_art_id, {"name_en": "__TEST_EN__", "wikidata_id": "Q99999999"}
                        )
                        if not updated_art or updated_art.name_en != "__TEST_EN__" or updated_art.wikidata_id != "Q99999999":
                            errors.append("Artist name_en / wikidata_id 欄位更新失敗")
                        art_list_res = client.get("/api/v1/artists?limit=5")
                        art_list_json = art_list_res.get_json()
                        if (
                            not isinstance(art_list_json, list)
                            or (art_list_json and ("name_en" not in art_list_json[0] or "wikidata_id" not in art_list_json[0]))
                        ):
                            errors.append("GET /api/v1/artists 回傳缺少 name_en 或 wikidata_id 欄位")

                # 測試歌曲建立與綁定剛建立的歌手
                test_song = song_service.create_song({
                    "title_main": "__TEST_AUTO_SONG__",
                    "song_type": "cover",
                    "artist_ids": [temp_art_id] if temp_art_id else []
                })
                if not test_song or not test_song.id:
                    errors.append("Song 沙盒建立失敗")
                else:
                    temp_song_id = test_song.id
                    song_service.update_song(temp_song_id, {"title_zh": "測試歌曲更新", "artist_ids": []})
            except Exception as e:
                errors.append(f"Artist / Song CRUD 沙盒測試異常：{e}")
            finally:
                if temp_song_id:
                    try:
                        song_service.delete_song(temp_song_id)
                    except Exception:
                        db.session.rollback()
                if temp_art_id:
                    try:
                        artist_service.delete_artist(temp_art_id)
                    except Exception:
                        db.session.rollback()

            # 4. 沙盒測試：活動大事紀 CRUD (特別驗證字串日期 'YYYY-MM-DD' 防呆轉換)
            temp_act_id = None
            try:
                test_act = activity_service.create_activity({
                    "vtuber_id": "1",
                    "title": "__TEST_AUTO_ACTIVITY__",
                    "description": "",
                    "event_date": "2026-09-30",
                    "activity_type": "milestone",
                    "link_url": ""
                })
                if not test_act or not test_act.id:
                    errors.append("Activity 沙盒建立失敗")
                else:
                    temp_act_id = test_act.id
                    activity_service.update_activity(temp_act_id, {"event_date": "2026-10-01"})
            except Exception as e:
                errors.append(f"Activity 字串日期與 CRUD 沙盒測試異常：{e}")
            finally:
                if temp_act_id:
                    try:
                        activity_service.delete_activity(temp_act_id)
                    except Exception:
                        db.session.rollback()

            # 5. 沙盒測試：影片建立、分類一鍵切換 API、批次分類切換與時間軸篩選保留
            temp_vid_id = "_TSTVID0001"  # 11 chars
            try:
                video_service.delete_video(temp_vid_id)
                test_vid = video_service.create_video({
                    "video_id": temp_vid_id,
                    "title": "__TEST_AUTO_VIDEO__",
                    "published_at": "2026-09-30",
                    "video_type": "stream_singing",
                    "vtuber_id": "1"
                })
                if not test_vid:
                    errors.append("Video 沙盒建立失敗")
                else:
                    # 測試單筆分類切換 API
                    res_chg = client.post(
                        f"/admin/videos/{temp_vid_id}/change_type",
                        json={"video_type": "stream_other"}
                    )
                    if res_chg.status_code != 200 or not (res_chg.get_json() or {}).get("success"):
                        errors.append(f"POST /admin/videos/<id>/change_type 失敗: {res_chg.status_code}")

                    # 測試批次分類切換 API
                    res_bulk = client.post(
                        "/admin/videos/bulk_change_type",
                        json={"video_ids": [temp_vid_id], "video_type": "stream_singing"}
                    )
                    if res_bulk.status_code != 200 or not (res_bulk.get_json() or {}).get("success"):
                        errors.append(f"POST /admin/videos/bulk_change_type 失敗: {res_bulk.status_code}")

                    # 測試時間軸頁面開啟與 return_url 篩選參數保留
                    ret_url = "/admin/singing_streams?sort=newest&vtuber_id=1"
                    res_tl = client.get(
                        f"/admin/videos/{temp_vid_id}/timeline",
                        query_string={"return_url": ret_url}
                    )
                    tl_html = res_tl.get_data(as_text=True)
                    if res_tl.status_code != 200:
                        errors.append(f"GET 時間軸編輯頁失敗: {res_tl.status_code}")
                    elif "/admin/singing_streams?sort=newest" not in tl_html:
                        errors.append("時間軸編輯頁未正確保留 return_url 篩選返回網址")
            except Exception as e:
                errors.append(f"Video / Timeline 沙盒測試異常：{e}")
            finally:
                try:
                    video_service.delete_video(temp_vid_id)
                except Exception:
                    db.session.rollback()

            # 6. 沙盒測試：剪輯師與切片 CRUD (含日期字串轉換)
            temp_author_id = None
            temp_clip_id = None
            temp_clip_vid = "_TSTCLP0001"  # 11 chars
            try:
                author = clip_service.create_clip_author({
                    "name": "__TEST_AUTO_CLIPPER__",
                    "youtube_channel_id": "UC_TEST_CLIPPER_ID",
                    "channel_url": "https://www.youtube.com/@test"
                })
                temp_author_id = author.id
                clip = clip_service.create_clip({
                    "video_id": temp_clip_vid,
                    "title": "__TEST_AUTO_CLIP__",
                    "tags": "歌唱",
                    "published_at": "2026-09-30",
                    "author_id": temp_author_id,
                    "vtuber_ids": [1]
                })
                temp_clip_id = clip.id
                clip_service.update_clip(temp_clip_id, {"published_at": "2026-10-01"})
            except Exception as e:
                errors.append(f"Clip / Author 沙盒測試異常：{e}")
            finally:
                if temp_clip_id:
                    try:
                        clip_service.delete_clip(temp_clip_id)
                    except Exception:
                        db.session.rollback()
                if temp_author_id:
                    try:
                        clip_service.delete_clip_author(temp_author_id)
                    except Exception:
                        db.session.rollback()

            db.session.remove()
            db.engine.dispose()

        # 7. 驗證啟用 CSRF 與權限驗證後的正/負向安全性測試
        import io
        import re
        import sqlite3
        from app.models.artist import Artist
        from app.models.vtuber import VTuber

        class CsrfTestConfig(Config):
            TESTING = True
            LOGIN_DISABLED = False
            WTF_CSRF_ENABLED = True
            SQLALCHEMY_DATABASE_URI = "sqlite:///" + test_db_path.replace("\\", "/")

        csrf_app = create_app(CsrfTestConfig)
        with csrf_app.app_context():
            csrf_client = csrf_app.test_client()

            # 7a. 未登入存取後台與受保護 API 應被攔截
            res_unauth_dash = csrf_client.get("/admin/dashboard")
            if res_unauth_dash.status_code != 302 or "/auth/login" not in res_unauth_dash.headers.get("Location", ""):
                errors.append(f"未登入存取 /admin/dashboard 未導向登入頁：{res_unauth_dash.status_code}")

            res_unauth_fetch = csrf_client.get("/api/v1/videos/fetch_youtube_info?video_id=dQw4w9WgXcQ")
            if res_unauth_fetch.status_code not in (302, 401):
                errors.append(f"未登入呼叫 fetch_youtube_info 未被攔截：{res_unauth_fetch.status_code}")

            # 取得登入頁 CSRF Token
            login_res = csrf_client.get("/auth/login")
            login_html = login_res.get_data(as_text=True)
            token_match = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', login_html)
            if login_res.status_code != 200 or not token_match:
                errors.append("啟用 CSRF 時 GET /auth/login 缺少 csrf_token 表單欄位")
                token_val = ""
            else:
                token_val = token_match.group(1)

            if token_val:
                res_unauth_quick = csrf_client.post(
                    "/api/v1/artists/quick_create",
                    json={"name_main": "__UNAUTH_ARTIST__"},
                    headers={"X-CSRFToken": token_val},
                )
                if res_unauth_quick.status_code not in (302, 401):
                    errors.append(f"未登入呼叫 /api/v1/artists/quick_create 未被攔截：{res_unauth_quick.status_code}")

            # 7b. 公開 API 分頁上限防呆 (limit <= 500)
            res_cap = csrf_client.get("/api/v1/artists?limit=999999&skip=-5")
            if res_cap.status_code != 200 or len(res_cap.get_json() or []) > 500:
                errors.append(f"GET /api/v1/artists 分頁上限防護失效：status={res_cap.status_code}")

            # 7c. 模擬真實管理員登入後的 CSRF、輸入驗證、Mass Assignment 與還原防呆
            if token_val:
                res_login = csrf_client.post(
                    "/auth/login",
                    data={
                        "username": Config.ADMIN_USERNAME,
                        "password": Config.ADMIN_PASSWORD,
                        "csrf_token": token_val,
                    },
                )
                if res_login.status_code != 302 or "/admin/dashboard" not in res_login.headers.get("Location", ""):
                    errors.append(f"正確帳密與 CSRF Token 登入失敗：{res_login.status_code}")
                else:
                    dash_html = csrf_client.get("/admin/artists").get_data(as_text=True)
                    meta_m = re.search(r'<meta\s+name="csrf-token"\s+content="([^"]+)"', dash_html)
                    session_csrf = meta_m.group(1) if meta_m else token_val

                    # 缺 CSRF Token 寫入必須回 400
                    res_no_csrf = csrf_client.post(
                        "/admin/artists/create",
                        data={"name_main": "__NO_CSRF_ARTIST__"},
                    )
                    if res_no_csrf.status_code != 400:
                        errors.append(f"已登入但未附帶 CSRF Token 應回 400，實得：{res_no_csrf.status_code}")

                    # 無效 YouTube video_id 格式必須回 400
                    res_bad_vid = csrf_client.get("/api/v1/videos/fetch_youtube_info?video_id=../../bad")
                    if res_bad_vid.status_code != 400:
                        errors.append(f"無效 video_id 應回 400，實得：{res_bad_vid.status_code}")

                    # 建立暫存歌手並驗證 Mass Assignment (id=999999) 被過濾
                    created_id = None
                    try:
                        res_create = csrf_client.post(
                            "/admin/artists/create",
                            data={"name_main": "__TEST_SEC_ARTIST__", "csrf_token": session_csrf},
                        )
                        if res_create.status_code != 302:
                            errors.append(f"附帶 CSRF 建立歌手失敗：{res_create.status_code}")
                        sec_artist = db.session.scalars(
                            db.select(Artist).where(Artist.name_main == "__TEST_SEC_ARTIST__")
                        ).first()
                        if not sec_artist:
                            errors.append("CSRF 建立歌手後於資料庫查無該筆資料")
                        else:
                            created_id = sec_artist.id
                            res_inline = csrf_client.post(
                                f"/admin/artists/{created_id}/inline_edit",
                                data={"id": "999999", "name_en": "SecTest", "csrf_token": session_csrf},
                            )
                            inline_json = res_inline.get_json() or {}
                            db.session.expire_all()
                            reloaded = db.session.get(Artist, created_id)
                            if (
                                res_inline.status_code != 200
                                or not inline_json.get("success")
                                or reloaded is None
                                or reloaded.id != created_id
                                or reloaded.name_en != "SecTest"
                                or db.session.get(Artist, 999999) is not None
                            ):
                                errors.append("inline_edit Mass Assignment 白名單過濾驗證失敗")
                    finally:
                        if created_id is not None:
                            csrf_client.post(
                                f"/admin/artists/{created_id}/delete",
                                data={"csrf_token": session_csrf},
                            )

                    # backup_import 非 SQLite 與缺資料表 SQLite 皆不可破壞現有資料庫
                    res_bad_file = csrf_client.post(
                        "/admin/backup/import",
                        data={
                            "csrf_token": session_csrf,
                            "backup_file": (io.BytesIO(b"not a sqlite file"), "bad.db"),
                        },
                        content_type="multipart/form-data",
                        follow_redirects=True,
                    )
                    if "非有效的 SQLite" not in res_bad_file.get_data(as_text=True):
                        errors.append("backup_import 未攔截非 SQLite 檔案")

                    empty_sqlite_path = os.path.join(tmpdir, "incomplete.db")
                    econn = sqlite3.connect(empty_sqlite_path)
                    econn.execute("CREATE TABLE dummy (x INTEGER)")
                    econn.commit()
                    econn.close()
                    with open(empty_sqlite_path, "rb") as ef:
                        empty_bytes = ef.read()
                    res_missing_tbl = csrf_client.post(
                        "/admin/backup/import",
                        data={
                            "csrf_token": session_csrf,
                            "backup_file": (io.BytesIO(empty_bytes), "incomplete.db"),
                        },
                        content_type="multipart/form-data",
                        follow_redirects=True,
                    )
                    if "缺少必要資料表" not in res_missing_tbl.get_data(as_text=True):
                        errors.append("backup_import 未攔截缺少必要資料表的 SQLite 檔案")

                    if db.session.scalar(db.select(db.func.count()).select_from(VTuber)) == 0:
                        errors.append("backup_import 拒收無效備份後卻誤傷原資料庫")

            db.session.remove()
            db.engine.dispose()

    return errors
