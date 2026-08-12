# 🌐 DDDiary — 後端 API 規格書 (API_SPEC.md)

本文件詳細列出 **DDDiary** 後端所提供的 REST API 接口定義、傳輸資料格式（JSON Schema）、請求參數以及後端與管理介面互動的 AJAX 行為規範。

---

## 1. 基礎設定與 URL 前綴
* **本機訪問地址**：`http://127.0.0.1:5000`
* **API 前綴路徑**：`/api/v1`
* **回應資料格式**：全數使用 `application/json; charset=utf-8`。
* **權限防護**：後台寫入、修改、刪除（`POST`, `PUT`, `DELETE`）API 均由 `Flask-Login` 的 `@login_required` 裝飾器防護。在未登入狀態下，將回傳 `401 Unauthorized` 狀態碼或引導至登入畫面。

---

## 2. VTubers (主播管理)

### A. 獲取所有主播
* **Method & URL**：`GET /api/v1/vtubers`
* **查詢參數**：
  * `skip` (int, 預設 0)：跳過前 N 筆。
  * `limit` (int, 預設 100)：取得前 N 筆。
* **回傳範例 (200 OK)**：
```json
[
  {
    "id": 1,
    "name_main": "滔滔饕餮 TaotaoTaotie Ch.",
    "name_romaji": "taotaotaotie_ch",
    "theme_color": "#00E676",
    "avatar_url": "https://yt3.ggpht.com/...",
    "banner_url": "https://...",
    "schedule_image_url": "https://...",
    "description": "大家好，我是滔滔饕餮..."
  }
]
```

### B. 更新主播資料
* **Method & URL**：`PUT /api/v1/vtubers/<id>`
* **請求 Payload (JSON)**：
```json
{
  "name_main": "滔滔饕餮 TaotaoTaotie Ch.",
  "name_romaji": "taotaotaotie_ch",
  "theme_color": "#00E676",
  "avatar_url": "https://...",
  "banner_url": "https://...",
  "schedule_image_url": "https://...",
  "description": "更新後的介紹..."
}
```
* **回傳範例 (200 OK)**：
```json
{
  "status": "success",
  "message": "VTuber updated successfully"
}
```

### C. 頻道影片自動同步 (YouTube API 同步)
* **Method & URL**：`POST /api/v1/vtubers/<id>/sync-youtube`
* **說明**：向後端請求，自動呼叫 YouTube API 獲取該主播頻道的最新 50 部影片，自動分類為歌枠或一般影片並登入至 `videos` 表。
* **回傳範例 (200 OK)**：
```json
{
  "status": "success",
  "synced_count": 12,
  "message": "Successfully synced 12 new videos from YouTube channel."
}
```

---

## 3. Videos (影片/直播存檔)

### A. 獲取特定主播影片
* **Method & URL**：`GET /api/v1/videos?vtuber_id=<vtuber_id>`
* **回傳範例 (200 OK)**：
```json
[
  {
    "video_id": "xbzjE_249hw",
    "vtuber_id": 1,
    "title": "【歌枠】日常下午清唱時間",
    "published_at": "2026-08-11T16:00:00",
    "video_type": "stream_singing",
    "thumbnail_url": "https://img.youtube.com/vi/xbzjE_249hw/mqdefault.jpg"
  }
]
```

---

## 4. Repertoire & Records (歌單與歌唱紀錄)

### A. 儲存批次解析時間軸結果至資料庫
* **Method & URL**：`POST /admin/videos/<id>/timeline/save`
* **說明**：將管理員在預覽視窗中確認無誤的批量解析與編輯結果（含備註/歌手）正式寫入資料庫。
* **請求 Payload (JSON)**：
```json
{
  "items": [
    { "title": "表裏一体", "timestamp_seconds": 1340, "note": "ゆず" },
    { "title": "猫", "timestamp_seconds": 7346, "note": "DISH//" }
  ],
  "singer_ids": [1]
}
```
* **回傳範例 (200 OK)**：
```json
{
  "success": true,
  "count": 2
}
```

---

## 5. 重複資料健康診斷 (Diagnostics)

為保證資料乾淨性，後端內建自動化診斷介面：

* `GET /api/v1/diagnostics/duplicate-artists`：診斷並列出資料庫中文字相似或重複的歌手。
* `POST /api/v1/diagnostics/merge-artists`：一鍵合併指定 ID 的重複歌手，並自動更新受影響歌曲的歌手外鍵。
