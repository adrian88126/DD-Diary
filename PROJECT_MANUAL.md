# VTSong Database — 專案功能與架構手冊

> **文件版本：** v1.0 | 建立時間：2026-07-20  
> **專案位置：** `VTSong_Database`（專案根目錄）  
> **部署目標：** GitHub Pages / Vercel / Cloudflare Pages（靜態） + 本地 FastAPI 伺服器（動態）

---

## 目錄

1. [專案簡介與整體架構](#1-專案簡介與整體架構)
2. [技術棧](#2-技術棧)
3. [目錄結構說明](#3-目錄結構說明)
4. [資料庫 Schema](#4-資料庫-schema)
5. [所有頁面與路由清單](#5-所有頁面與路由清單)
6. [後端 API 接口清單](#6-後端-api-接口清單)
7. [核心元件與工具函式](#7-核心元件與工具函式)
8. [靜態網站打包流程](#8-靜態網站打包流程)
9. [自動化測試與健康診斷套件](#9-自動化測試與健康診斷套件)
10. [待整理與疑慮區域（清理與修補紀錄）](#10-待整理與疑慮區域清理與修補紀錄)

---

## 1. 專案簡介與整體架構

**VTSong Database** 是一個 VTuber（虛擬主播）歌唱資料庫與管理系統，主要功能分兩大面向：

| 面向 | 說明 |
|------|------|
| **後台管理（Admin）** | 建立/編輯主播資料、歌曲、歌手、演唱紀錄、里程碑、影片，並可一鍵同步 YouTube 頻道影片 |
| **公開分享（Share）** | 每位主播擁有獨立的靜態公開頁面，展示歌單、歌回時間軸、歌回月曆、週表圖片、大事記 |

### 整體架構圖

```
使用者瀏覽器
    │
    ├── 本地 FastAPI 後端（http://127.0.0.1:8000）
    │       ├── GET /                      → SPA 後台管理介面 (index.html)
    │       ├── GET /share/{identifier}    → Jinja2 SSR 主播公開頁
    │       ├── GET /static/...            → 靜態資源
    │       └── /api/v1/...               → REST API
    │
    └── 靜態部署（GitHub Pages / Vercel）
            ├── docs/index.html            → 大廳入口 (lobby.html 預渲染)
            ├── docs/catalog.html          → SPA 後台管理介面
            ├── docs/share/{id}/           → 每位主播靜態預渲染頁
            └── docs/data/*.json           → 全資料庫快照 JSON
```

**雙模式判斷機制：** 前端 `config.js` 中的 `IS_STATIC` 旗標，判斷目前是本地開發（讀 API）還是靜態部署（讀 JSON）。

---

## 2. 技術棧

### 後端

| 技術 | 版本 | 用途 |
|------|------|------|
| **Python** | 3.10+ | 主要語言 |
| **FastAPI** | ≥ 0.110.0 | REST API 框架 + Jinja2 SSR |
| **SQLAlchemy** | ≥ 2.0.28 | ORM，使用 Declarative Base 2.0 語法 |
| **Pydantic** | ≥ 2.6.4 | 資料驗證 Schema |
| **pydantic-settings** | ≥ 2.2.1 | 設定管理 |
| **Uvicorn** | ≥ 0.28.0 | ASGI 伺服器 |
| **SQLite** | 內建 | 資料庫（`vtuber_songs.db`） |
| **Jinja2** | 傳遞依賴 | 伺服器端 HTML 渲染（分享頁、靜態打包） |

### 前端

| 技術 | 版本 | 用途 |
|------|------|------|
| **HTML5** | — | SPA 結構（`index.html`，1385 行） |
| **Vanilla CSS** | — | 所有樣式（`index.css`，38KB） |
| **Vanilla JavaScript (ES Modules)** | — | 全部前端邏輯（無框架） |
| **Google Fonts** | Outfit + Noto Sans TC | 字型 |
| **FontAwesome** | 6.4.0 CDN | 圖示庫 |
| **YouTube IFrame API** | — | 歌回播放 Modal |

---

## 3. 目錄結構說明

```
VTSong_Database/
│
├── main.py                    # FastAPI 應用程式進入點
├── build_static.py            # 靜態網站打包腳本（已含 .bak 排除邏輯）
├── init_db.py                 # 資料庫初始化腳本（已補齊完整 Schema 定義）
├── PROJECT_MANUAL.md          # 本專案功能與架構手冊
├── requirements.txt           # Python 套件依賴
├── vtuber_songs.db            # 主資料庫（SQLite）
├── vtsong.db                  # ⚠️ 遺留舊資料庫（待使用者確認保留或刪除）
│
├── app/
│   ├── config.py              # Pydantic Settings 設定（API prefix、DB URL）
│   ├── database.py            # SQLAlchemy 引擎、Session、Base、get_db()
│   │
│   ├── models/                # SQLAlchemy ORM 資料表模型
│   │   ├── vtuber.py          # VTuber 主播
│   │   ├── song.py            # 歌曲
│   │   ├── artist.py          # 歌手
│   │   ├── video.py           # 影片/直播
│   │   ├── record.py          # 演唱歷史紀錄
│   │   ├── activity.py        # 里程碑/大事記
│   │   ├── link.py            # 主播社群連結
│   │   └── association.py     # 多對多聯結表（song_artists, vtuber_songs, record_vtubers）
│   │
│   ├── schemas/               # Pydantic 驗證 Schema（API 輸入/輸出格式）
│   │   ├── vtuber.py
│   │   ├── song.py
│   │   ├── artist.py
│   │   ├── video.py
│   │   ├── record.py
│   │   ├── activity.py
│   │   └── link.py
│   │
│   ├── crud/                  # 資料庫操作函式（ORM 查詢邏輯）
│   │   ├── vtuber.py
│   │   ├── song.py
│   │   ├── artist.py
│   │   ├── video.py
│   │   ├── record.py
│   │   └── activity.py
│   │
│   ├── api/
│   │   ├── router.py          # 頂層 API Router（掛載 /api/v1 前綴）
│   │   └── v1/
│   │       ├── __init__.py    # 整合所有子 Router
│   │       ├── vtubers.py     # VTuber CRUD + YouTube 同步（最複雜，~622 行）
│   │       ├── songs.py       # 歌曲 CRUD
│   │       ├── artists.py     # 歌手 CRUD
│   │       ├── videos.py      # 影片 CRUD + YouTube oEmbed
│   │       ├── records.py     # 演唱紀錄 CRUD + 批次匯入
│   │       ├── activities.py  # 里程碑 CRUD
│   │       └── diagnostics.py # 重複資料診斷與自動合併
│   │
│   ├── static/                # 前端靜態資源（同步至 docs/）
│   │   ├── index.html         # SPA 後台管理介面（主頁面，107KB）
│   │   ├── index.css          # 全域樣式表（38KB）
│   │   ├── share.css          # 主播分享頁專用獨立樣式（從 share_profile.html 抽離）
│   │   ├── template.csv       # CSV 批次匯入範本（可下載）
│   │   ├── template.json      # JSON 批次匯入範本（可下載）
│   │   └── js/
│   │       ├── main.js        # 模組進入點（bootstrap，初始化序列）
│   │       ├── config.js      # 設定（API_BASE、IS_STATIC）
│   │       ├── state.js       # 全域狀態（cache、admin mode）
│   │       ├── api.js         # 資料載入 + DELETE 抽象
│   │       ├── portal.js      # 所有 visitor 端視圖渲染
│   │       ├── admin.js       # 後台管理 CRUD 表單（最大，129KB）
│   │       ├── ui.js          # 共用 UI 工具（Toast、Player Modal）
│   │       └── share.js       # 主播分享頁 ES Module 邏輯（含月曆/燈箱/搜尋/播放）
│   │
│   └── templates/             # Jinja2 HTML 模板（SSR + 靜態打包）
│       ├── share_profile.html # 主播公開分享頁（精簡化模板，渲染 OG 社群卡片標籤）
│       └── lobby.html         # 大廳入口頁（靜態部署首頁）
│
├── docs/                      # 靜態網站輸出目錄（GitHub Pages 部署根）
│   ├── index.html             # lobby.html 預渲染結果
│   ├── catalog.html           # index.html 複製（SPA 後台）
│   ├── index.css              # 樣式複製
│   ├── data/                  # 全資料庫 JSON 快照
│   │   ├── songs.json
│   │   ├── artists.json
│   │   ├── vtubers.json
│   │   ├── videos.json
│   │   ├── records.json
│   │   └── activities.json
│   ├── js/                    # JS 複製
│   └── share/                 # 主播靜態頁（每位主播 3 個路徑別名）
│       ├── 1/index.html       # 滔滔饕餮（by ID）
│       ├── 7/index.html       # 星璃 Seri（by ID）
│       ├── taotaotaotie_ch/   # （by name_romaji 底線版）
│       ├── taotaotaotie-ch/   # （by name_romaji 短橫線版）
│       └── seri/              # （by name_romaji）
│
└── scratch/                   # ⚠️ 雜項臨時腳本目錄（見第 9 節）
```

---

## 4. 資料庫 Schema

資料庫：`vtuber_songs.db`（SQLite）

### 核心資料表

| 資料表 | 說明 |
|--------|------|
| `vtubers` | 主播資料（名稱、頻道ID、頭像、主題色、週表圖片...） |
| `songs` | 歌曲資料（多語言標題、類型） |
| `artists` | 歌手資料（多語言名稱） |
| `videos` | 影片/直播資料（YouTube ID、標題、類型、日期） |
| `singing_records` | 演唱歷史紀錄（歌曲 ↔ 影片 ↔ 時間軸秒數） |
| `activities` | 里程碑/大事記（標題、類型、日期、連結） |
| `vtuber_links` | 主播社群平台連結（平台名、URL） |

### 聯結表

| 聯結表 | 用途 |
|--------|------|
| `song_artists` | 歌曲 ↔ 歌手（多對多） |
| `vtuber_songs` | 主播 ↔ 歌曲（多對多，含 `association_type`：`signature` 常駐 / `requestable` 點歌） |
| `record_vtubers` | 演唱紀錄 ↔ 主播（多對多，支援合唱 feat. 功能） |

### VTuber 模型欄位一覽

| 欄位 | 類型 | 說明 |
|------|------|------|
| `id` | int PK | 自動遞增 |
| `name_main` | str | 主要顯示名稱（必填） |
| `name_ja` | str? | 日文名 |
| `name_zh` | str? | 中文名 |
| `name_romaji` | str? | 羅馬拼音（用於 URL slug） |
| `description` | str? | 個人簡介 |
| `youtube_channel_id` | str? | YouTube 頻道 ID（unique） |
| `avatar_url` | str? | 頭像圖片 URL |
| `theme_color` | str? | 主題色（hex） |
| `banner_url` | str? | 橫幅圖片 URL |
| `social_links` | str? | 社群連結（舊版，已被 `vtuber_links` 取代） |
| `schedule_image_url` | str? | 本週行程週表圖片 URL |
| `created_at` | datetime | 建立時間 |

---

## 5. 所有頁面與路由清單

### 5.1 後端動態路由（FastAPI）

| URL | 類型 | 對應檔案 | 主要功能 |
|-----|------|----------|----------|
| `GET /` | SSR → FileResponse | `app/static/index.html` | 後台管理 SPA 入口 |
| `GET /share/{identifier}` | Jinja2 SSR | `app/templates/share_profile.html` | 主播公開個人頁（支援 ID、name_romaji、模糊比對） |
| `GET /favicon.ico` | FileResponse | `app/static/favicon.ico` | Favicon（不存在則回 204） |
| `GET /static/...` | StaticFiles | `app/static/` | 靜態資源（CSS、JS、template 檔） |

**識別碼解析優先順序（`/share/{identifier}`）：**
1. 純數字 → 比對 `vtubers.id`
2. 非數字 → 比對 `vtubers.name_romaji`（含底線/短橫線統一化）
3. 如仍無結果 → `LIKE` 模糊比對
4. 仍無 → HTTP 404

### 5.2 靜態部署路由（GitHub Pages / docs/）

| URL 路徑 | 對應檔案 | 主要功能 |
|----------|----------|----------|
| `/`（根目錄） | `docs/index.html` | 大廳入口（Lobby，列出所有主播） |
| `/catalog.html` | `docs/catalog.html` | SPA 後台管理介面（靜態版） |
| `/share/1/` | `docs/share/1/index.html` | 滔滔饕餮公開頁（by ID） |
| `/share/7/` | `docs/share/7/index.html` | 星璃 Seri 公開頁（by ID） |
| `/share/taotaotaotie_ch/` | `docs/share/taotaotaotie_ch/index.html` | 滔滔饕餮（底線 slug） |
| `/share/taotaotaotie-ch/` | `docs/share/taotaotaotie-ch/index.html` | 滔滔饕餮（短橫線 slug） |
| `/share/seri/` | `docs/share/seri/index.html` | 星璃 Seri（slug） |
| `/data/*.json` | `docs/data/` | 資料庫 JSON 快照（供靜態前端讀取） |

### 5.3 SPA 內部視圖（`index.html` / `catalog.html`）

前端 SPA 使用 `switchView()` 切換以下視圖（無真實 URL 路由）：

| 視圖 ID | 功能說明 |
|---------|----------|
| `#view-dashboard` | 儀表板：統計數字、最新 Live 紀錄、大事記時間軸 |
| `#view-vtuber-profile` | 主播個人檔案（動態渲染，含 6 分頁 Tab） |
| `#view-catalog` | 資料目錄（5 Tab：歌曲/歌手/影片/紀錄/大事記） |
| `#view-admin` | 後台管理（8 子面板，含 VTuber、影片、歌曲、紀錄、大事記管理） |

---

## 6. 後端 API 接口清單

所有 API 前綴：`/api/v1`  
互動文件：`http://127.0.0.1:8000/api/v1/openapi.json`

### 6.1 VTuber 主播 `/api/v1/vtubers`

| 方法 | 路徑 | 說明 |
|------|------|------|
| `GET` | `/` | 取得所有主播清單（`skip` / `limit` 分頁） |
| `GET` | `/fetch_youtube_info` | 抓取 YouTube 頻道資訊（頭像、橫幅、描述）Query: `channel_url` |
| `GET` | `/{vtuber_id}` | 取得單一主播資料 |
| `POST` | `/` | 建立新主播 |
| `PUT` | `/{vtuber_id}` | 更新主播資料（含 `schedule_image_url`） |
| `DELETE` | `/{vtuber_id}` | 刪除主播 |
| `POST` | `/{vtuber_id}/links` | 新增社群連結 |
| `POST` | `/{vtuber_id}/signatures/{song_id}` | 設定常駐拿手歌曲 |
| `POST` | `/{vtuber_id}/songs/{song_id}` | 關聯歌曲（`signature` 或 `requestable`） |
| `POST` | `/{vtuber_id}/songs/batch` | 批次新增歌曲（自動建立歌曲/歌手） |
| `POST` | `/{vtuber_id}/sync_youtube` | 同步 YouTube 頻道影片到資料庫 |

### 6.2 歌曲 `/api/v1/songs`

| 方法 | 路徑 | 說明 |
|------|------|------|
| `GET` | `/` | 取得歌曲清單（支援 `q` 模糊搜尋、`song_type`、`vtuber_id`、`is_signature`） |
| `GET` | `/{song_id}` | 取得單一歌曲 |
| `POST` | `/` | 建立歌曲 |
| `PUT` | `/{song_id}` | 更新歌曲 |
| `DELETE` | `/{song_id}` | 刪除歌曲 |

### 6.3 歌手 `/api/v1/artists`

| 方法 | 路徑 | 說明 |
|------|------|------|
| `GET` | `/` | 取得歌手清單（`skip` / `limit`） |
| `POST` | `/` | 建立歌手 |
| `PUT` | `/{artist_id}` | 更新歌手 |
| `DELETE` | `/{artist_id}` | 刪除歌手 |

### 6.4 影片/直播 `/api/v1/videos`

| 方法 | 路徑 | 說明 |
|------|------|------|
| `GET` | `/` | 取得影片清單（支援 `video_type`、`vtuber_id` 過濾） |
| `GET` | `/fetch_youtube_info` | 抓取 YouTube 影片 oEmbed 資訊（標題、縮圖、日期）Query: `video_id` |
| `GET` | `/{video_id}` | 取得單一影片 |
| `POST` | `/` | 建立影片 |
| `PATCH` | `/{video_id}/type` | 僅更新影片類型 |
| `PUT` | `/{video_id}` | 完整更新影片 |
| `DELETE` | `/{video_id}` | 刪除影片 |

### 6.5 演唱紀錄 `/api/v1/records`

| 方法 | 路徑 | 說明 |
|------|------|------|
| `GET` | `/` | 取得紀錄清單（支援 `vtuber_id`、`video_id`、`song_id` 過濾） |
| `POST` | `/` | 建立單筆紀錄 |
| `POST` | `/batch` | 批次匯入紀錄（自動建立 Song / Video / VTuber） |
| `PUT` | `/{record_id}` | 更新紀錄（含 `singer_ids`） |
| `DELETE` | `/{record_id}` | 刪除紀錄 |

### 6.6 里程碑/大事記 `/api/v1/activities`

| 方法 | 路徑 | 說明 |
|------|------|------|
| `GET` | `/` | 取得大事記清單（支援 `vtuber_id`、`start_date`、`end_date`、`activity_type` 過濾） |
| `POST` | `/` | 建立大事記 |
| `PUT` | `/{activity_id}` | 更新大事記 |
| `DELETE` | `/{activity_id}` | 刪除大事記 |

### 6.7 診斷工具 `/api/v1/diagnostics`

| 方法 | 路徑 | 說明 |
|------|------|------|
| `GET` | `/unknown_songs` | 取得沒有任何關聯歌手的歌曲（孤兒歌曲） |
| `GET` | `/duplicate_songs` | 取得名稱重複的歌曲清單 |
| `POST` | `/auto_link_duplicates` | 自動合併重複歌曲（將紀錄移至 canonical，刪除重複） |
| `GET` | `/duplicate_artists` | 取得名稱重複的歌手清單 |
| `POST` | `/auto_link_duplicate_artists` | 自動合併重複歌手 |

---

## 7. 核心元件與工具函式

### 7.1 後端核心

#### `app/database.py` — 資料庫連線

```
SessionLocal = sessionmaker(...)     # Session 工廠
Base = DeclarativeBase               # 所有 ORM Model 基礎類別
get_db()                             # FastAPI Dependency Injection 用 Session 產生器
```

- SQLite 連線啟用 `PRAGMA foreign_keys=ON`（外鍵約束）
- `check_same_thread=False`（允許多執行緒存取）

#### `app/config.py` — 設定

```
settings.PROJECT_NAME = "VTuber Song Database"
settings.API_V1_STR   = "/api/v1"
settings.DATABASE_URL  = "sqlite:///./vtuber_songs.db"
```

#### `app/crud/` — 資料庫操作

| 模組 | 主要函式 |
|------|----------|
| `vtuber.py` | `get_vtuber`, `get_vtubers`, `create_vtuber`, `create_vtuber_link`, `add_signature_song`, `get_vtuber_by_name` |
| `song.py` | `get_song`, `get_songs`, `create_song` |
| `artist.py` | `get_artist`, `get_artists`, `create_artist` |
| `video.py` | `get_video`, `get_videos`, `create_video` |
| `record.py` | `get_record`, `get_records`, `create_record` |
| `activity.py` | `get_activities`, `create_activity` |

### 7.2 前端 JS 模組

#### 模組依賴圖

```
index.html
  └── main.js (type="module")
        ├── imports: state.js
        ├── imports: api.js
        │     └── imports: config.js, state.js
        ├── imports: portal.js
        │     └── imports: config.js, state.js, ui.js
        ├── imports: admin.js
        │     └── imports: config.js, state.js, ui.js, api.js, portal.js
        └── imports: ui.js
```

#### `config.js` — 前端設定

| 匯出 | 說明 |
|------|------|
| `API_BASE` | `'/api/v1'` |
| `IS_STATIC` | `true` 時讀 JSON，`false` 時打 API（依 hostname/port 判斷） |

#### `state.js` — 全域狀態

| 匯出 | 說明 |
|------|------|
| `state` | 全域快取物件（`cacheSongs`, `cacheArtists`, `cacheVtubers`, `cacheVideos`, `cacheRecords`, `cacheActivities`） + Admin mode 狀態 |
| `setIsAdminMode(val)` | 設定 Admin 模式並存入 localStorage |
| `initAdminModeFromStorage()` | 從 localStorage 讀取 Admin 模式狀態 |

#### `api.js` — 資料層抽象

| 匯出 | 說明 |
|------|------|
| `fetchAllData()` | 並發載入全部 6 個資料集（靜態 JSON / 動態 API），存入 `state.cache*` |
| `deleteRecordOnServer(endpoint, id)` | DELETE `${API_BASE}/${endpoint}/${id}` |

#### `ui.js` — UI 工具函式

| 匯出 | 說明 |
|------|------|
| `showToast(message, type)` | 右下角 Toast 通知（success / error / warning，3 秒自動消失） |
| `formatSeconds(seconds)` | 秒數 → `MM:SS` / `HH:MM:SS` |
| `scrollToElementInsideContent(id)` | 平滑捲動至 `.scroll-content` 內的元素 |
| `formatApiError(err, fallback)` | FastAPI / Pydantic 錯誤格式化為可讀字串 |
| `playRecord(videoId, startSeconds, ...)` | 開啟 YouTube Iframe Player Modal（帶時間點） |
| `closePlayerOverlay()` | 關閉 Player Modal |

#### `portal.js` — 訪客端視圖渲染（1103 行）

| 匯出 | 說明 |
|------|------|
| `switchView(viewName, title?)` | 切換 SPA 視圖 |
| `loadSidebarVtubers()` | 渲染側邊欄主播清單 |
| `loadDashboardData()` | 渲染儀表板統計與最新 Live |
| `loadActivitiesTimeline(typeFilter?)` | 渲染垂直大事記時間軸 |
| `loadVtuberProfile(vtuberId)` | 渲染主播完整個人頁（6 Tab 佈局） |
| `searchSongHistory(songId, songTitle)` | 搜尋特定歌曲的演唱紀錄 |
| `renderCatalog()` | 渲染資料目錄（5 Tab） |
| `renderVtuberCatalog()` | 渲染主播資料表 |
| `populateCatalogDropdowns()` | 填充目錄過濾下拉選單 |

#### `admin.js` — 後台管理（129KB，最大模組）

主要功能包含：
- VTuber CRUD 表單（含 YouTube 頻道同步、週表圖片、`formatScheduleImageUrl`）
- 影片 / 直播 CRUD 表單
- 歌曲 / 歌手 CRUD 表單
- 演唱紀錄 CRUD（含 Setlist 時間軸編輯）
- 批次匯入（CSV / JSON / 純文字 Tab 分隔格式）
- 資料庫診斷（孤兒歌曲、重複歌曲 / 歌手自動合併）

#### `main.js` — 初始化進入點（273 行）

**初始化序列（DOMContentLoaded）：**
1. `initAdminModeFromStorage()` — 讀取登入狀態
2. `fetchAllData()` — 並發載入全部資料
3. `populateAdminDropdowns()` / `populateCatalogDropdowns()` — 填充下拉選單
4. `setupTheme()` — 深/淺色主題切換（localStorage 持久化）
5. `setupNavigation()` — 側邊欄 nav 連結
6. `setupCatalogTabs()` — 目錄 5 Tab + 即時搜尋（200ms debounce）
7. `setupAdminToggle()` — Admin 登入（密碼：`admin123`，本地保護）
8. `setupAutocompleteSelects()` / `setupAdminFormListeners()` / `setupCurateModalListeners()`
9. `loadSidebarVtubers()` / `loadDashboardData()` / `renderCatalog()` / `renderVtuberCatalog()`

### 7.3 Jinja2 模板

#### `share_profile.html`（86KB）

主播公開個人頁，包含：
- 主播基本資料（頭像、橫幅、主題色）
- 📅 本週行程週表（`schedule_image_url` + Lightbox 燈箱 Modal）
- 6 分頁 Tab：
  - **主播與活動**：Top5 歌曲、Top5 歌手、成就時間軸、歌回月曆
  - **總歌單**（requestable songs）
  - **歌回直播**（stream_singing）
  - **其他直播**（stream_other）
  - **歷史歌回單曲**（346+ 筆，含日期過濾）
  - **MV 影片清單**
- 歌回月曆（年/月下拉選擇，點日期過濾歌曲）
- YouTube IFrame API 播放器

#### `lobby.html`（靜態部署首頁）

大廳入口頁，使用 Jinja2 `{% for vt in vtubers %}` 渲染主播卡片格線，每張卡片連結至 `/share/{name_romaji}/`。

---

## 8. 靜態網站打包流程

執行 `python build_static.py` 後依序：

1. **清空 `docs/`** 目錄（保留 locked 項目）
2. **複製 `app/static/`** 至 `docs/`（`index.html` → 重命名為 `catalog.html`）
3. **建立 `docs/data/` 和 `docs/share/`** 目錄
4. **匯出 6 張全庫資料表** 為 JSON（`songs`, `artists`, `vtubers`, `videos`, `records`, `activities`）並**匯出每位主播專屬歌唱紀錄 JSON** (`records_vtuber_{id}.json` 供按需/非同步載入)。
5. **預渲染每位主播** 的 `share_profile.html`：
   - **主要路徑 (Primary Slug)**：寫入完整預渲染 HTML 頁面（例如 `docs/share/taotaotaotie_ch/index.html`）。
   - **別名路徑 (Alias Paths)**：寫入 390 位元組的輕量級 HTML Redirect 檔（例如 `docs/share/1/index.html` 轉址至 Primary Slug），減少 95% 以上重複檔案體積。
6. **渲染 Lobby** 首頁至 `docs/index.html`

## 9. 自動化測試與健康診斷套件

為了解決程式碼修改後容易造成後台網頁、API 或資料庫關聯損壞的問題，專案新增了完整的測試系統（位於 `tests/` 目錄，可由根目錄的 `run_tests.py` 一鍵呼叫）。

### 測試維度

1. **資料庫與數據關聯檢測 (`tests/test_database.py`)**：
   - 檢查 `vtuber_songs.db` 的連線與基本資料表。
   - 檢測孤兒演唱紀錄（`SingingRecord` 是否指向不存在的歌曲/影片）。
   - 校驗 YouTube `video_id` 格式是否為 11 字元，以及頭像、週表 URL 是否合法。
2. **後端 API 整合測試 (`tests/test_api.py`)**：
   - 在 `8005` 埠口（不干擾運行中的 8000 埠口）拉起臨時 FastAPI 伺服器進行測試。
   - 檢驗所有主要查詢路由（`GET /vtubers`, `GET /songs`, `GET /videos`, `GET /records`）的響應。
   - 測試完整的 `POST`（新增測試主播）➔ `GET`（驗證寫入）➔ `DELETE`（復原環境並刪除）生命週期。
3. **後台網頁 DOM 與 JS 選取器完整性檢測 (`tests/test_frontend_integrity.py`)**：
   - 解析後台 `index.html` 以及 JS 內動態渲染模板中的 ID 定義。
   - 抓取 `admin.js`, `portal.js`, `main.js` 內所有 `getElementById('ID')` 與 `querySelector('#ID')` 所使用的 ID。
   - 自動進行交叉比對，若 JS 引用了任何不存在於 HTML 中的 ID，會立即精確報錯，防止前端因抓不到元素而崩潰。
4. **靜態打包產物與快取驗證 (`tests/test_static.py`)**：
   - 測試執行 `build_static.py` 編譯流程是否出錯。
   - 檢驗 `docs/index.html` 存在與快取 JSON（`docs/data/*.json`）格式及完整性。

### 一鍵測試指令
在專案根目錄下直接執行：
```powershell
python run_tests.py
```
若全部測試通過，會以綠色字體印出測試成功報告；若有任何失敗項目，將會列出詳細錯誤清單與所在程式碼。

---

## 10. 待整理與疑慮區域（清理與修補紀錄）

### 🟢 已完成清理的孤兒檔案與補丁 (Cleaned Files & Patches)

| 檔案/項目 | 原大小 | 處理動作與說明 |
|-----------|--------|----------------|
| `app/static/app.js.bak` | 167KB | **已刪除**。重構前的舊單體 JS 備份，現行系統已重構為 ES 模組架構。 |
| `docs/app.js.bak` | 167KB | **已刪除**。原由 `build_static.py` 無差別複製，現已清理。 |
| `scratch_continuation.json` | 40KB | **已刪除**。AI 輔助開發過程之中繼暫存資料。 |
| `scratch/` 腳本目錄 | — | **已刪除**。包含修補日曆等一次性除錯與修補腳本。 |
| `project_architecture.md` | 10KB | **已刪除**。舊版架構說明文件，已由本文件 `PROJECT_MANUAL.md` 完全取代。 |
| `build_static.py` 腳本 | — | **已補丁修復**。新增 `.bak` 副檔名過濾機制，避免靜態打包時將備份檔複製進 `docs/`。 |
| `init_db.py` 腳本 | — | **已補丁修復**。`CREATE TABLE vtubers` 補齊 `avatar_url`、`theme_color`、`banner_url`、`social_links` 與 `schedule_image_url` 等完整欄位定義。 |

### 🟡 待確認與保留功能

| 檔案/欄位 | 狀態說明 |
|-----------|----------|
| [`vtsong.db`](vtsong.db) | **遺留舊資料庫**。系統現使用 `vtuber_songs.db`。請使用者確認裡面是否包含需備份的舊資料後再手動刪除。 |
| [`app/models/vtuber.py` — `social_links` 欄位](app/models/vtuber.py#L22) | **保留雙軌相容**。`social_links` 為早期單欄位存儲，在 `crud/vtuber.py` 與 `admin.js` 中有自動轉檔同步邏輯，維持舊相容性。 |
| [`docs/share/1/` 與 `docs/share/7/`](docs/share/1/) | **數字 ID 別名**。`build_static.py` 預先渲染的別名目錄，可直接透過 `/share/1/` 存取。 |

---

*本文件由 Antigravity AI 自動掃描分析與修補後更新，末次更新：2026-07-20*
