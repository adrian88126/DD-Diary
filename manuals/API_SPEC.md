# 📡 DDDiary — 後端 API 與管理端點規格書 (API_SPEC.md)

本文件定義 **DDDiary** 系統實際實作的公開 REST API（`/api/v1/*`）與後台操作端點（`/admin/*`），包含 HTTP Methods、權限安全機制與主要 Payload 格式。

> **認證與 CSRF 安全規範**：
> * 全後台 `/admin/*` 路由（受 `@admin_bp.before_request` `@login_required` 保護）以及所有寫入型、外部抓取代理 `/api/v1/*` 端點均要求登入驗證。
> * 全站已啟用 Flask-WTF `CSRFProtect`；後台介面由 `admin/layout.html` 自動於表單與同源非 GET `fetch` 請求夾帶 `csrf_token` / `X-CSRFToken`。
> * 登入介面 `/auth/login` 使用 `hmac.compare_digest` 比對環境變數帳密，並驗證 `next` 站內相對路徑防止 Open Redirect。

---

## 1. 公開讀取與後台代理 API (`/api/v1/*`)

> 註：公開 `GET` 列表端點均經過 `_parse_pagination()` 驗證，強制限制 `skip >= 0` 與 `1 <= limit <= 500`（預設 `100`）。

### A. 公開唯讀查詢端點 (`GET`)
* `GET /api/v1/vtubers?skip=0&limit=100`：取得主播精簡清單（`id`, `name_main`）。
* `GET /api/v1/songs?q=&song_type=&skip=0&limit=100`：依關鍵字與歌曲類型查詢歌曲（`id`, `title_main`, `song_type`）。
* `GET /api/v1/artists?skip=0&limit=100`：取得原唱歌手多語言與 Wikidata QID 清單：
```json
[
  {
    "id": 1,
    "name_main": "周杰倫",
    "name_en": "Jay Chou",
    "name_ja": "ジェイ・チョウ",
    "name_zh": "周杰倫",
    "name_romaji": "Zhou Jielun",
    "wikidata_id": "Q238819"
  }
]
```
* `GET /api/v1/videos?video_type=&vtuber_id=&skip=0&limit=100`：查詢影片與直播（`video_id`, `title`, `video_type`）。
* `GET /api/v1/records?vtuber_id=&video_id=&song_id=&skip=0&limit=100`：查詢歌唱歷史紀錄（`id`, `song_id`, `video_id`）。
* `GET /api/v1/activities?vtuber_id=&skip=0&limit=100`：查詢里程碑／活動紀錄（`id`, `title`, `activity_type`）。

### B. 需登入權限之 YouTube 抓取與快速建立端點 (`@login_required`)
* **取得主播 YouTube 頻道資訊**：`GET /api/v1/vtubers/fetch_youtube_info?channel_url=<url_or_handle>`
* **取得 YouTube 影片 oEmbed 資訊**：`GET /api/v1/videos/fetch_youtube_info?video_id=<11_char_id>`（嚴格驗證 `video_id` 格式為 `[A-Za-z0-9_-]{11}`，無效回 `400`）。
* **快速建立原唱歌手 (Quick Create Artist)**：`POST /api/v1/artists/quick_create`
  * Payload：`{ "name_main": "歌手名稱" }`（不分大小寫自動防重）
  * 回傳：`{ "success": true, "artist": { "id": 15, "name_main": "米津玄師" } }`
* **快速建立歌曲 (Quick Create Song)**：`POST /api/v1/songs/quick_create`
  * Payload：`{ "title_main": "歌名", "song_type": "cover", "artist_ids": [1] }`
  * 回傳：`{ "success": true, "is_new": true, "song": { "id": 5, "title_main": "歌名" } }`
* **快速建立剪輯師 (Quick Create Clip Author)**：`POST /api/v1/clip_authors/quick_create`
  * Payload：`{ "name": "作者名稱", "channel_url": "..." }`

---

## 2. 後台資源管理、行內編輯與時間軸 (`/admin/*`)

> 全數受 `@login_required` + `CSRFProtect` 保護；Service 層 `create_*` / `update_*` 皆設有欄位白名單，防範 Mass Assignment。

### A. 核心資源管理頁面與操作
* **VTuber 主播**：`GET /admin/vtubers`、`POST /admin/vtubers/create`、`POST /admin/vtubers/<id>/edit`、`POST /admin/vtubers/<id>/delete`、`POST /admin/vtubers/<id>/inline_edit`、`POST /admin/vtubers/bulk_delete`、`POST /admin/vtubers/<id>/sync_youtube`
* **歌曲 (Songs)**：`GET /admin/songs`、`POST /admin/songs/create`、`POST /admin/songs/<id>/edit`、`POST /admin/songs/<id>/delete`、`POST /admin/songs/<id>/inline_edit`、`POST /admin/songs/bulk_delete`
* **歌手 (Artists)**：`GET /admin/artists`、`POST /admin/artists/create`、`POST /admin/artists/<id>/edit`、`POST /admin/artists/<id>/delete`、`POST /admin/artists/<id>/inline_edit`、`POST /admin/artists/bulk_delete`
* **影片與歌回 (Videos)**：`GET /admin/videos`、`GET /admin/singing_streams`、`POST /admin/videos/create`、`POST /admin/videos/<id>/edit`、`POST /admin/videos/<id>/delete`、`POST /admin/videos/<id>/inline_edit`、`POST /admin/videos/bulk_delete`、`POST /admin/videos/bulk_type`、`POST /admin/videos/sync_all`、`GET /admin/videos/fetch_info`
* **演唱紀錄 (Records)**：`GET /admin/records`、`POST /admin/records/create`、`POST /admin/records/<id>/edit`、`POST /admin/records/<id>/delete`、`POST /admin/records/<id>/inline_edit`、`POST /admin/records/bulk_delete`
* **活動／里程碑 (Activities)**：`GET /admin/activities`、`POST /admin/activities/create`、`POST /admin/activities/<id>/edit`、`POST /admin/activities/<id>/delete`、`POST /admin/activities/<id>/inline_edit`、`POST /admin/activities/bulk_delete`

### B. 影片分類切換與時間軸儲存
* `POST /admin/videos/<id>/change_type`：就地變更影片類型（JSON：`{"video_type": "stream_other" | "short" | "cover_mv" | "original_mv" | "schedule"}`）。
* `POST /admin/videos/bulk_change_type`：批次變更影片類型（JSON：`{"video_ids": [...], "video_type": "..."}`）。
* `POST /admin/videos/<id>/convert_to_short` / `POST /admin/videos/bulk_convert_to_short`：單筆／批次將影片轉為 Short 短影音。
* `GET /admin/videos/<id>/timeline`：開啟指定影片時間軸編輯頁（支援 `return_url` 保留原篩選頁狀態）。
* `POST /admin/videos/<id>/timeline/save`：儲存前端解析完成之歌曲時間軸陣列並自動建立／綁定缺失歌曲與 `singing_records`。

---

## 3. 系統自檢、健康診斷與備份還原 (`/admin/diagnostics`, `/admin/backup/*`)

* `GET /admin/diagnostics`：全方位系統健康評分儀表板，展示四大維度異常診斷報告。
* `POST /admin/diagnostics/auto_link_duplicates`：一鍵合併所有同名重複歌曲，並自動轉移演唱紀錄與點歌關係。
* `POST /admin/diagnostics/auto_link_duplicate_artists`：一鍵合併所有同名重複歌手，並自動更新歌曲外鍵。
* `POST /admin/diagnostics/auto_merge_wikidata_artists`：一鍵合併共享相同 Wikidata QID 的跨語系同義歌手（如日／中／英譯名），並彙整多語名稱欄位與歌曲關聯（排除官方共用 QID，如 `Q909655`）。
* `POST /admin/diagnostics/auto_fix_untagged_clips`：一鍵為所有無標籤切片執行關鍵字智慧自動補標籤。
* `POST /admin/diagnostics/auto_clean_duplicate_records`：一鍵清理同一秒數重複登錄的演唱紀錄。
* `POST /admin/diagnostics/run_system_tests`：於獨立子行程執行全系統 4 大自動化測試套件 (`run_tests.py --json`)，回傳通過狀態、耗時與錯誤明細 JSON。
* `GET /admin/backup/export`：一鍵匯出下載當前完整 SQLite 資料庫檔案（`vtuber_songs_backup_<timestamp>.db`）。
* `POST /admin/backup/import`：上傳還原 SQLite 資料庫檔案（`multipart/form-data`，欄位名 `backup_file`，上限 50 MB）。系統先於暫存檔驗證 SQLite 檔頭、`PRAGMA integrity_check` 與 5 張核心表結構皆通過後，才自動建立 `backups/pre_restore_*.db` 安全快照並完成原子替換。

---

## 4. Clips (精選切片與剪輯師管理)

* **剪輯師管理**：`GET /admin/clip_authors`、`POST /admin/clip_authors/create`、`POST /admin/clip_authors/<id>/edit`、`POST /admin/clip_authors/<id>/delete`、`POST /admin/clip_authors/<id>/sync`、`GET /admin/clip_authors/fetch_info`
* **切片與播放清單匯入**：`GET /admin/clips`、`POST /admin/clips/create`、`POST /admin/clips/<id>/edit`、`POST /admin/clips/<id>/delete`、`POST /admin/clips/import`、`GET /admin/clips/fetch_info`、`GET/POST /admin/clips/playlist_import`
* **批次刪除切片 (`POST /admin/clips/bulk_delete`)**：Payload `{"ids": [1, 2, 3]}`，回傳 `{"success": true, "count": 3}`。
* **批次修改切片屬性 (`POST /admin/clips/bulk_edit`)**：支援 `set_author`、`set_tags`（`append` / `overwrite` / `remove`）、`set_vtubers`、`set_song`，回傳 `{"success": true, "count": 3}`。
