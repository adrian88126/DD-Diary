# VTSong Database — 專案開發與架構手冊 (PROJECT_MANUAL.md)

> **文件版本：** v2.6 | 建立時間：2026-08-12  
> **專案位置：** `VTSong_Database`（專案根目錄）  
> **部署目標：** GitHub Pages（靜態雙語託管）+ 本地 Flask 伺服器（動態資料管理與 YouTube 同步）

---

## 1. 專案開發導覽

為了方便開發與維護，本手冊已將核心章節進行拆分與職責分工。請根據您的開發需求參閱以下分流手冊：

* 📂 [**DATABASE.md (資料庫設計手冊)**](DATABASE.md)：包含資料庫 Schema 欄位、主外鍵關聯以及資料初始化機制。
* 📂 [**API_SPEC.md (後端 API 規格書)**](API_SPEC.md)：後端 REST API 接口定義、JSON 傳輸 Payload 格式以及後台 AJAX 操作。
* 📂 [**BUILD_PROCESS.md (靜態編譯與打包原理)**](BUILD_PROCESS.md)：說明靜態預渲染（Jinja2）、多國語系生成、CORS 去模組化離線相容以及 `lobby_url` 動態路由。

---

## 2. 目錄結構與模組職責說明

```
VTSong_Database/
│
├── run.py                     # Flask 應用程式進入點 (監聽 5000 端口)
├── build_static.py            # 靜態網站中英雙語打包腳本
├── init_db.py                 # 資料庫初始化與 Schema 建立腳本
├── requirements.txt           # Python 依賴包
├── vtuber_songs.db            # 主資料庫（SQLite）
│
├── app/
│   ├── __init__.py            # Flask 應用工廠與 extensions 初始化
│   ├── config.py              # 設定管理 (環境變數、資料庫連結)
│   ├── extensions.py          # SQLAlchemy、LoginManager、Babel 實體定義
│   ├── i18n.py                # Babel 多國語系語系選擇邏輯
│   ├── locales/               # 語系翻譯對照字典 JSON (zh.json, en.json)
│   │
│   ├── models/                # SQLAlchemy 資料表模型
│   │   ├── vtuber.py          # VTuber 主播
│   │   ├── song.py            # 歌曲
│   │   ├── artist.py          # 歌手
│   │   ├── video.py           # 影片/直播
│   │   ├── record.py          # 演唱歷史紀錄
│   │   ├── activity.py        # 里程碑/大事記
│   │   └── association.py     # 多對多關係表 (song_artists, record_singers)
│   │
│   ├── services/              # 主要業務邏輯
│   │   ├── vtuber_service.py  # 主播資料增刪與社群連結轉檔同步
│   │   └── youtube_service.py # YouTube API 影片獲取與同步
│   │
│   ├── blueprints/            # Flask 路由藍圖
│   │   ├── main/routes.py     # 首頁大廳路由
│   │   ├── share/routes.py    # 主播專頁路由
│   │   ├── auth/routes.py     # 後台登入與登出
│   │   ├── admin/routes.py    # 後台管理面板路由
│   │   └── api/               # REST API 各類別 CRUD 路由
│   │
│   ├── static/                # 前端靜態資源
│   │   ├── css/
│   │   │   ├── base.css       # 全站基礎樣式與光暗主題色
│   │   │   └── share.css      # 主播分享頁排版樣式 (修正時間軸靠右)
│   │   └── js/
│   │       ├── ui.js          # 共用 UI 函式（Toast、光暗切換、漢堡選單控制，全域掛載）
│   │       └── share.js       # 個人頁面互動（燈箱、日曆、快捷過濾、播放，全域掛載）
│   │
│   └── templates/             # Jinja2 模板
│       ├── base.html          # 通用導覽列、多國語系下拉式選單與 Toast 容器
│       ├── main/
│       │   └── lobby.html     # 大廳頁面 (繼承 base.html，帶有數據快照與週表牆)
│       ├── share/
│       │   └── profile.html   # 主播公開專頁 (多分頁切換、帶時間軸播放)
│       ├── auth/
│       │   └── login.html     # 後台登入表單
│       └── admin/
│           └── dashboard.html # 後台管理主介面
```

---

## 3. 前端 JS 核心元件職責

為了確保本地直接雙擊 HTML 檔案瀏覽（`file:///` 協定）時不被瀏覽器的 CORS 政策封鎖，專案採用**去模組化**的傳統腳本載入，函式均掛載於 `window` 物件下：

### A. `app/static/js/ui.js` (全域 UI 與互動)
* **Toast 提示**：`window.showToast(message, type = 'success')`，在畫面右下角呈現淡入淡出通知。
* **時間轉換**：`window.formatSeconds(seconds)`，將秒數轉換為 `HH:MM:SS` 格式。
* **主題切換**：自動載入 `localStorage` 的 `theme` 設定。當 `#theme-toggle` 按鈕被點選時，在 `html` 上切換 `data-theme="light"` 屬性並寫入快取，觸發 smooth 過渡背景切換。
* **手機版選單**：偵測並綁定 `.hamburger` 按鈕，點選時切換 `.nav-links` 的 `active` 狀態，控制抽屜開關。

### B. `app/static/js/share.js` (個人頁面核心行為)
* **影音同步播放**：調用 YouTube IFrame API 播放器，監聽特定歌曲的時間戳記，提供點擊後即時跳轉到指定秒數的播放功能。
* **大事記時間軸**：加載並渲染該主播的大事記與里程碑。
* **多功能週表燈箱**：控制 `#image-lightbox-modal`，支援點擊週表圖片放大、滾輪縮放、以及按鍵盤左右鍵切換多張圖片的輪播模式。
* **影片分類過濾器**：在「其他影片」Tab 實作 `window.filterOtherVideos(filterType, btn)`。支援點選「全部」、「雜談/單人」、「連動/合作」以及「短影音」進行前端實時過濾，並與頂端搜尋列的 `searchQuery` 保持完美聯動。

---

## 4. 本地開發與後台運作指引

1. **資料庫初始化**：首次執行前，請先執行 `python init_db.py` 建立 SQLite 資料庫。
2. **啟動 Flask 服務**：執行 `python run.py`。
3. **進入後台管理**：在瀏覽器中開啟 `http://127.0.0.1:5000/`，點選右上角 **Login** 登入（預設帳號密碼為 `admin` / `admin123`），即可進入後台管理面版：
   * 點選 **VTubers** 可新增主播資料並填寫其頻道 ID，可一鍵點選「同步影片」爬取 YouTube 最新存檔。
   * 點選 **演唱紀錄** 可使用「智慧時間軸分割工具」貼上留言區文字（如 `03:40 歌曲名稱`），一鍵解析並寫入資料庫。
4. **一鍵靜態打包**：資料庫有更新後，在本機終端機中執行 `python build_static.py`。生成出的雙語靜態網頁成品將會儲存於專案根目錄的 `docs/` 下，直接推送至 GitHub 即可利用 GitHub Pages 進行公開託管。
