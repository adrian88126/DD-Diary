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
    db_path = os.path.abspath("vtuber_songs.db")
    db_snapshot = db_path + ".test_bak"
    if os.path.exists(db_path):
        shutil.copy2(db_path, db_snapshot)

    app = create_app()
    app.config["TESTING"] = True
    app.config["LOGIN_DISABLED"] = True
    client = app.test_client()

    try:
      with app.app_context():
        # 1. 測試各個公開頁面、API 與管理後台頁面 (HTTP GET 必須為 200)
        endpoints = [
            "/",
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
        ]

        for ep in endpoints:
            try:
                res = client.get(ep)
                if res.status_code != 200:
                    errors.append(f"GET {ep} 響應異常，狀態碼：{res.status_code}")
            except Exception as e:
                errors.append(f"GET {ep} 執行錯誤：{e}")

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
    finally:
        if os.path.exists(db_snapshot):
            try:
                shutil.move(db_snapshot, db_path)
            except Exception:
                pass

    return errors
