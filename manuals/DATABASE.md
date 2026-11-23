# 🗄️ DDDiary — 資料庫設計手冊 (DATABASE.md)

本文件詳細說明 **DDDiary** 系統所使用的 SQLite 資料庫結構、核心資料表欄位、多對多關聯（Association Tables）以及資料庫初始化與遷移機制。

---

## 1. 資料庫概述
* **資料庫類型**：SQLite 3
* **預設主檔案**：`vtuber_songs.db`（位於專案根目錄下）
* **ORM 框架**：SQLAlchemy 2.x (使用 Declarative Base 語法)

---

## 2. 核心資料表 (Core Tables)

### A. `vtubers` (主播資料表)
儲存 VTuber 的基本資料、社群連結、代表色及週表圖片。

| 欄位名 | 類型 | 說明 | 備註 |
|--------|------|------|------|
| `id` | INTEGER | 主鍵 (Primary Key)，自動遞增 | |
| `name_main` | VARCHAR | 主名稱 (通常為最常用名稱，如 滔滔饕餮) | 不可為空 |
| `name_romaji` | VARCHAR | 羅馬拼音名稱 (用於靜態網址路徑，如 `taotaotaotie_ch`) | |
| `name_ja` | VARCHAR | 日文名稱 | 可為空 |
| `name_zh` | VARCHAR | 中文譯名 | 可為空 |
| `avatar_url` | VARCHAR | 頭像圖片網址 (Lobby 及週表側邊欄小圖頭像) | 可為空 |
| `theme_color` | VARCHAR | 個人代表色 (十六進位制 HEX 值，如 `#00e676`) | 預設 `#a78bfa` |
| `banner_url` | VARCHAR | 個人背景橫幅圖片網址 | 可為空 |
| `description` | TEXT | 個人介紹 / 簡介 | 可為空 |
| `schedule_image_url` | VARCHAR | 本週行程週表圖片網址 | 可為空 |
| `social_links` | TEXT | JSON 陣列格式儲存的社群連結 | 舊版相容欄位，內部轉檔後同步至 `vtuber_links` |

---

### B. `songs` (收錄歌曲表)
儲存被演唱歌曲的資料，支援多語言標題與原唱者關聯。

| 欄位名 | 類型 | 說明 | 備註 |
|--------|------|------|------|
| `id` | INTEGER | 主鍵 (Primary Key)，自動遞增 | |
| `title_main` | VARCHAR | 歌曲主要標題 (如 錦鯉抄) | 不可為空 |
| `title_ja` | VARCHAR | 歌曲日文標題 | 可為空 |
| `title_zh` | VARCHAR | 歌曲中文標題 | 可為空 |
| `song_type` | VARCHAR | 歌曲類型 (通常為 `original` 原創 或 `cover` 翻唱) | 預設 `cover` |

---

### C. `artists` (歌手/原唱表)
儲存歌曲的原唱歌手資訊。

| 欄位名 | 類型 | 說明 | 備註 |
|--------|------|------|------|
| `id` | INTEGER | 主鍵 (Primary Key)，自動遞增 | |
| `name_main` | VARCHAR | 歌手主要名稱 | 不可為空 |
| `name_en` | VARCHAR | 歌手英文名稱 | 可為空 |
| `name_ja` | VARCHAR | 歌手日文名稱 | 可為空 |
| `name_zh` | VARCHAR | 歌手中文名稱 | 可為空 |
| `name_romaji` | VARCHAR | 歌手羅馬拼音名稱 | 可為空 |
| `wikidata_id` | VARCHAR | Wikidata 實體編號（如 `Q238819`） | 可為空 |

---

### D. `videos` (影片與直播存檔表)
記錄 VTuber 的 YouTube 影片或直播存檔，用以關聯歌唱時間軸。

| 欄位名 | 類型 | 說明 | 備註 |
|--------|------|------|------|
| `video_id` | VARCHAR | 主鍵 (Primary Key)，YouTube 11 碼 ID | 不可為空 |
| `vtuber_id` | INTEGER | 關聯的主播 ID | 外鍵，指向 `vtubers.id` |
| `title` | VARCHAR | 影片標題 | 不可為空 |
| `published_at` | DATETIME | 影片發佈 / 直播上線時間 | 不可為空 |
| `video_type` | VARCHAR | 影片類型 (`stream_singing` 歌枠, `stream_other` 直播雜談, `cover_mv` 翻唱MV, `original_mv` 原創MV, `short` 短片) | 預設 `stream_singing` |
| `thumbnail_url` | VARCHAR | 影片縮圖網址 | 可為空 |

---

### E. `singing_records` (歌唱歷史紀錄表)
記錄某一次歌唱發生的具體影片與時間軸起點（秒數），這是系統最核心的聯結點。

| 欄位名 | 類型 | 說明 | 備註 |
|--------|------|------|------|
| `id` | INTEGER | 主鍵 (Primary Key)，自動遞增 | |
| `video_id` | VARCHAR | 關聯影片的 YouTube ID | 外鍵，指向 `videos.video_id` |
| `song_id` | INTEGER | 關聯歌曲 ID | 外鍵，指向 `songs.id` |
| `timestamp_seconds` | INTEGER | 演唱起點在影片中的秒數時間 (例如 3624 代表 01:00:24) | 不可為空 |
| `note` | VARCHAR | 演唱備註 (例如：與某主播合唱、清唱版等) | 可為空 |

---

### F. `activities` (成就與大事記表)
儲存主播的大事記、週年慶、新衣裝發佈等里程碑時間軸資訊。

| 欄位名 | 類型 | 說明 | 備註 |
|--------|------|------|------|
| `id` | INTEGER | 主鍵 (Primary Key)，自動遞增 | |
| `vtuber_id` | INTEGER | 關聯的主播 ID | 外鍵，指向 `vtubers.id` |
| `title` | VARCHAR | 事件標題 (如：出道一週年紀念) | 不可為空 |
| `event_date` | DATETIME | 事件發生日期 | 不可為空 |
| `activity_type` | VARCHAR | 事件類型 (`milestone`, `announcement`, `other`) | 預設 `milestone` |
| `link_url` | VARCHAR | 相關證實或紀念影片連結 | 可為空 |

---

### G. `clip_authors` (剪輯創作者表)
儲存 YouTube 烤肉曼 / 剪輯師的頻道與個人資訊。

| 欄位名 | 類型 | 說明 | 備註 |
|--------|------|------|------|
| `id` | INTEGER | 主鍵 (Primary Key)，自動遞增 | |
| `name` | VARCHAR | 剪輯師名稱 | 唯一索引，不可為空 |
| `youtube_channel_id` | VARCHAR | YouTube 頻道 ID (如 `UC...`) | 可為空 |
| `channel_url` | VARCHAR | 剪輯師頻道網址 | 可為空 |
| `created_at` | DATETIME | 建立時間戳記 | 預設當前時間 |

---

### H. `clips` (精選切片表)
記錄精選的短片、烤肉與歌唱精華切片。

| 欄位名 | 類型 | 說明 | 備註 |
|--------|------|------|------|
| `id` | INTEGER | 主鍵 (Primary Key)，自動遞增 | |
| `video_id` | VARCHAR | YouTube 影片 ID (11 碼) | 唯一索引，不可為空 |
| `title` | VARCHAR | 切片影片標題 | 不可為空 |
| `tags` | TEXT | 逗號分隔的標籤 (如 歌唱,連動,雜談) | 可為空 |
| `published_at` | DATE | 影片發布日期 | 可為空 |
| `author_id` | INTEGER | 關聯的剪輯師 ID | 外鍵，指向 `clip_authors.id` |
| `song_id` | INTEGER | 關聯的歌曲 ID | 外鍵，指向 `songs.id` |
| `created_at` | DATETIME | 建立時間戳記 | 預設當前時間 |
| `thumbnail_url` | PROPERTY | 動態產生的封面縮圖網址 | 由 `video_id` 即時計算，無需額外儲存 |

---

## 3. 多對多關係聯結表 (Association Tables)

為滿足靈活的關聯查詢，系統設計了多對多的聯結表：

### A. `song_artists` (歌曲 ↔ 原唱歌手)
一首歌可以有多位原唱歌手，一個歌手也可以唱過多首不同的歌。
* `song_id` (INTEGER, 外鍵指向 `songs.id`)
* `artist_id` (INTEGER, 外鍵指向 `artists.id`)
* **主鍵**：(`song_id`, `artist_id`) 聯合主鍵。

### B. `record_vtubers` (歌唱紀錄 ↔ 聯手合唱主播)
一次歌唱紀錄可以有多位主播共同合唱。
* `record_id` (INTEGER, 外鍵指向 `singing_records.id`)
* `vtuber_id` (INTEGER, 外鍵指向 `vtubers.id`)
* **主鍵**：(`record_id`, `vtuber_id`) 聯合主鍵。

### C. `clip_vtubers` (精選切片 ↔ 出場主播)
一部切片可標記多位出場的主播。
* `clip_id` (INTEGER, 外鍵指向 `clips.id`)
* `vtuber_id` (INTEGER, 外鍵指向 `vtubers.id`)
* **主鍵**：(`clip_id`, `vtuber_id`) 聯合主鍵。

---

## 4. 索引與效能最佳化
除了主鍵、外鍵與唯一約束自動建立的索引外，[`../init_db.py`](../init_db.py) 與正式環境資料庫額外維護以下查詢索引：
* `idx_artists_name_en` (`artists.name_en`)：加速英文原唱歌手名稱查詢與 `/artists` 歌單排序。
* `idx_artists_wikidata_id` (`artists.wikidata_id`)：加速 Wikidata QID 跨語系同義歌手偵測與合併掃描。

---

## 5. 資料庫初始化、資料遷移與純文字 Git 版控
* **初始化腳本**：[`../init_db.py`](../init_db.py)。
  * **功能**：檢測 `vtuber_songs.db` 是否存在，若不存在則依據 ORM 定義自動建立所有資料表、聯合主鍵、外鍵約束與索引。
  * **內建種子資料**：預置了範例主播的基礎資料與大事記，方便開發環境快速呈現。
* **資料庫升級**：專案目前主要透過 SQLite 升級腳本與 [`../init_db.py`](../init_db.py) 同步演進 Schema（亦可搭配 Flask-Migrate 擴充）。
* **純文字 Git 同步機制（`db_sync.py` ↔ `database_dump.sql`）**：
  * 為避免二進位 `vtuber_songs.db` 造成 `.git` 歷史線性膨脹與無法 diff，`vtuber_songs.db`、`*.db` 與 `reports/` 已列入 `.gitignore`，改由 [`../db_sync.py`](../db_sync.py) 維護純文字 UTF-8 SQL 快照 [`../database_dump.sql`](../database_dump.sql)。
  * `python db_sync.py dump`：以唯讀模式連線 `vtuber_songs.db` 驗證 `PRAGMA integrity_check`，並原子性寫出完整 Schema、索引與資料至 `database_dump.sql`（`deploy.bat` 每次發布自動執行）。
  * `python db_sync.py restore --if-missing`：僅在本地尚無 `vtuber_songs.db` 時從 `database_dump.sql` 還原並驗證外鍵約束（`start.bat`、`sync.bat` 啟動時自動觸發）。
  * `python db_sync.py restore --force`：強制由 `database_dump.sql` 重建覆寫本地 `vtuber_songs.db`（覆寫前會自動備份現有檔案至 `backups/pre_sql_restore_<timestamp>.db`）。
