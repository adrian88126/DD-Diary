# 📡 DDDiary — 後端 API 規格書 (API_SPEC.md)

本文件定義 **DDDiary** 系統所提供的後端 RESTful API 規格、URL 路由、請求方法（HTTP Methods）、Payload 參數格式以及回傳範例。

---

## 1. 歌手 (Artists) API

### A. 新增歌手
* **Method & URL**：`POST /api/v1/artists`
* **請求 Payload (JSON)**：
```json
{
  "name_main": "周杰倫",
  "name_ja": "ジェイ・チョウ",
  "name_zh": "周杰倫",
  "name_romaji": "Jay Chou"
}
```
* **回傳範例 (201 Created)**：
```json
{
  "id": 1,
  "name_main": "周杰倫",
  "name_ja": "ジェイ・チョウ",
  "name_zh": "周杰倫",
  "name_romaji": "Jay Chou"
}
```

### B. 修改歌手
* **Method & URL**：`PUT /api/v1/artists/<id>` 或 `POST /admin/artists/<id>/edit`

### C. 刪除歌手
* **Method & URL**：`DELETE /api/v1/artists/<id>` 或 `POST /admin/artists/<id>/delete`

---

## 2. 歌曲 (Songs) API

### A. 新增歌曲
* **Method & URL**：`POST /api/v1/songs`
* **請求 Payload (JSON)**：
```json
{
  "title_main": "晴天",
  "title_ja": "",
  "title_zh": "晴天",
  "song_type": "original",
  "artist_ids": [1]
}
```

### B. 快速建立歌曲 (Quick Create)
* **Method & URL**：`POST /api/v1/songs/quick_create`
* **請求 Payload (JSON)**：`{ "title_main": "歌名" }`
* **回傳範例**：`{ "success": true, "is_new": true, "song": { "id": 5, "title_main": "歌名" } }`

### C. 修改歌曲
* **Method & URL**：`PUT /api/v1/songs/<id>` 或 `POST /admin/songs/<id>/edit`

### D. 刪除歌曲
* **Method & URL**：`DELETE /api/v1/songs/<id>` 或 `POST /admin/songs/<id>/delete`

---

## 3. VTuber 主播 API

### A. 新增主播
* **Method & URL**：`POST /api/v1/vtubers`
* **請求 Payload (JSON)**：
```json
{
  "name_main": "滔滔饕餮",
  "name_romaji": "taotaotaotie_ch",
  "name_ja": "",
  "name_zh": "滔滔饕餮",
  "youtube_channel_id": "UCxxxxxx",
  "theme_color": "#00e676",
  "signature_song_ids": [1, 2],
  "requestable_song_ids": [3, 4]
}
```

### B. 同步 YouTube 影片 (Sync Videos)
* **Method & URL**：`POST /api/v1/vtubers/<id>/sync-youtube` 或 `POST /admin/vtubers/<id>/sync`
* **說明**：觸發爬蟲或 YouTube Data API 抓取該頻道最新影片存檔，並寫入 `videos` 資料表。

---

## 4. 歌唱歷史紀錄 (Singing Records) API

### A. 新增單筆歌唱紀錄
* **Method & URL**：`POST /api/v1/records`
* **請求 Payload (JSON)**：
```json
{
  "video_id": "dQw4w9WgXcQ",
  "song_id": 1,
  "timestamp_seconds": 360,
  "note": "清唱版",
  "singer_ids": [1]
}
```

### B. 智慧時間軸文字解析與批次新增
* **Method & URL**：`POST /admin/records/timeline_parse`
* **請求 Payload (Form / JSON)**：
```json
{
  "video_id": "dQw4w9WgXcQ",
  "timeline_text": "03:40 晴天\n1:20:15 錦鯉抄\n02:00:00 告白氣球",
  "default_vtuber_id": 1
}
```
* **說明**：後端會自動以正規表達式解析時間戳記，比對歌曲庫（若不存在則自動新增歌曲），並批次建立 `singing_records`。

---

## 5. 系統自檢與健康診斷 API (Diagnostics & Health Checks)

* `GET /admin/diagnostics`：全方位系統健康評分儀表板，展示四大維度異常診斷報告。
* `POST /admin/diagnostics/auto_link_duplicates`：一鍵合併所有同名重複歌曲，並自動轉移演唱紀錄與點歌關係。
* `POST /admin/diagnostics/auto_link_duplicate_artists`：一鍵合併所有同名重複歌手，並自動更新歌曲外鍵。
* `POST /admin/diagnostics/auto_fix_untagged_clips`：一鍵為所有無標籤切片執行 AI 關鍵字智慧自動補標籤。
* `POST /admin/diagnostics/auto_clean_duplicate_records`：一鍵清理同一秒數重複登錄的演唱紀錄。
* `GET /api/v1/diagnostics/duplicate-artists`：診斷並列出資料庫中文字相似或重複的歌手。
* `POST /api/v1/diagnostics/merge-artists`：一鍵合併指定 ID 的重複歌手，並自動更新受影響歌曲的歌手外鍵。

---

## 6. Clips (切片精華管理與批次操作)

### A. 批次刪除切片
* **Method & URL**：`POST /admin/clips/bulk_delete`
* **請求 Payload (JSON)**：
```json
{
  "ids": [1, 2, 3]
}
```
* **回傳範例 (200 OK)**：
```json
{
  "success": true,
  "count": 3
}
```

### B. 批次修改切片屬性
* **Method & URL**：`POST /admin/clips/bulk_edit`
* **說明**：支援批次修改作者（`set_author`）、批次修改/追加/移除標籤（`set_tags`）、批次關聯主播（`set_vtubers`）與批次關聯歌曲（`set_song`）。
* **請求 Payload 範例 (設定標籤)**：
```json
{
  "ids": [1, 2, 3],
  "action_type": "set_tags",
  "tags": "歌唱,連動",
  "tag_mode": "append"
}
```
* **回傳範例 (200 OK)**：
```json
{
  "success": true,
  "count": 3
}
```
