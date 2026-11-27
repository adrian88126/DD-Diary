# 🏗️ DDDiary — 靜態編譯與打包原理手冊 (BUILD_PROCESS.md)

本文件深入探討 **DDDiary** 系統所使用的靜態網頁打包流程、多國語系編譯原理、如何相容瀏覽器本地端離線直接打開（`file:///` 協定），以及靜態版防錯的安全設計。

---

## 1. 靜態編譯整體流程

靜態網站編譯由指令 `python build_static.py` 觸發。核心執行流程如下：

```
執行 build_static.py
    │
    ├── 1. 清空 Docs 目錄 ─────→ 刪除 docs/ 下的所有舊網頁
    │
    ├── 2. 複製靜態檔案 ─────→ 將 app/static/ 複製至 docs/static/ (排除遺骸檔與後台專用 admin.*)
    │
    ├── 3. 資料庫統計快照 ───→ 從 SQLite 取得全站的 歌曲數/歷史紀錄數/影片數
    │
    ├── 4. 預渲染 [zh] 網頁 ──→ 使用 zh 語系 Request Context 生成中文版大廳與主播專頁
    │
    ├── 5. 預渲染 [en] 網頁 ──→ 使用 en 語系 Request Context 生成英文版大廳與主播專頁
    │
    └── 6. 生成轉址別名 ─────→ 為各個主播的 name_romaji 建立目錄並輸出跳轉 index.html
```

---

## 2. 多國語系與 SEO 預渲染原理 (Multi-language SSR)

Flask 應用在運行時，是透過專案自建的 `app/i18n.py`（讀取 `app/locales/{zh,en}.json` 並依檔案 `mtime` 快取）來實現輕量化中英雙語切換，無需沉重編譯步。
為了在**沒有後端服務**的靜態網頁（GitHub Pages）上也能提供「中文/英文切換」與正確的社群預覽卡片，`build_static.py` 在預渲染時模擬對應語系的 Cookie 上下文：

```python
with app.test_request_context(environ_base={'HTTP_COOKIE': f'lang={lang}'}):
```

### 運作原理：
1. `build_static.py` 分別為 `lang='zh'`（中文）與 `lang='en'`（英文）建立了一個偽造的請求上下文。
2. 上下文的 Cookie 寫入 `lang=zh` 或 `lang=en`，觸發 `i18n.py` 載入對應字典（`zh.json` 與 `en.json` 保持 100% 鍵值對齊）；模板同步動態切換 `<html lang="zh-Hant">` / `<html lang="en">`、SVG inline favicon 與雙語 Open Graph / Twitter 預覽標記，並於根目錄產生 `docs/robots.txt`。
3. 隨後呼叫 `render_template` 進行預渲染：
   * **中文版**：輸出大廳至 `docs/index.html`、原唱歌手歌單至 `docs/artists/index.html`，主播專頁輸出至 `docs/share/{id}/index.html`。
   * **英文版**：輸出大廳至 `docs/en/index.html`、原唱歌手歌單至 `docs/en/artists/index.html`，主播專頁輸出至 `docs/en/share/{id}/index.html`。
   * **共用歌手資料檔**：輸出至 `docs/static/data/artist_catalog.js`（掛載 `window.ARTIST_CATALOG_DATA` 供雙語 `/artists` 專頁在 `file:///` 離線模式下共用讀取，避免重複內嵌龐大 JSON）。
   * **主播個人頁資料抽離檔**：透過共用的 `share_service.get_vtuber_profile_payload()` 序列化資料，輸出至 `docs/static/data/vtuber_{id}.js`（掛載 `window.VTUBER_PROFILE_DATA`），供中英文雙語 `share/{id}/index.html` 共用載入，大幅縮減單頁 HTML 體積並減少快取冗餘。
   * **靜態資源精簡複製**：複製 `app/static/` 至 `docs/static/` 時透過 `_ignore_static` 自動排除 `*.bak`、根目錄舊檔（`share.css`、`template.csv`、`template.json`）、純後台資源（`css/admin.css`、`js/admin.js`）與舊版腳本（`js/portal.js`、`js/config.js`、`js/state.js`）。
4. 網頁右上角的「語系切換」下拉選單，在靜態模式下（`is_static=True`）會直接指向這些靜態預渲染出的語系路徑，達到無後端雙語切換的效果。

---

## 3. 本地離線 CORS 與「去模組化」設計

### CORS 安全性封鎖問題
在早期的設計中，`ui.js` 和 `share.js` 採用了 ES6 模組結構（即使用 `import`、`export` 關鍵字，且在 HTML 中以 `<script type="module">` 載入）。
當使用者在本地端**雙擊直接開啟 `docs/index.html`** 時，使用的是瀏覽器的 `file:///` 本地檔案協定。在這種協定下：
* 瀏覽器的安全政策（CORS Policy）會將 Origin 判定為 `null`。
* 瀏覽器拒絕為 `null` 來源加載任何 `type="module"` 的 JavaScript 檔案，導致 `ui.js` 和 `share.js` 加載失敗，拋出 `ERR_FAILED` 錯誤。
* JS 載入失敗進一步導致：手機版 Hamburger 漢堡按鈕點擊無反應、音樂無法跳轉、大圖燈箱無法打開等。

### 解決方案：傳統腳本去模組化 (Non-Module)
為了解決此核心問題，專案移除了所有的模組化聲明，改為**標準傳統腳本加載**：
1. **移除關鍵字**：在 `ui.js` 和 `share.js` 中移除了所有 `import` 和 `export`。
2. **全域掛載**：改在 `ui.js` 與 `share.js` 的末端，將需要給外部調用的函式與變數手動綁定到全域的 `window` 物件上：
   ```javascript
   window.showToast = showToast;
   window.formatSeconds = formatSeconds;
   window.openDrawer = openDrawer;
   window.closeDrawer = closeDrawer;
   window._ = _;
   ```
3. **消除 script module**：在模板中（`base.html`、`profile.html`），所有的 script 標籤均移除 `type="module"` 屬性。
4. **結果**：在 `file:///` 本地雙擊開啟下，所有 JS 文件都能正常加載運行，本地離線可用性達到 100%。

---

## 4. 靜態路由適應性 (lobby_url)

靜態網站上最容易遇到根目錄路由導向錯誤（例如點擊首頁時導向 `https://username.github.io/`，進而跳出專案目錄發生 404）。
專案使用 `lobby_url` 參數來動態生成相對路徑：
* **大廳模板 (`base.html` Navbar 連結)**：
  ```html
  <a href="{{ lobby_url or url_for('main.lobby') }}">首頁</a>
  ```
* **打包時**：
  * 大廳本身渲染時傳入 `lobby_url="index.html"`、`artists_url="./artists/index.html"`。
  * 原唱歌手歌單專頁（`docs/artists/index.html` 與 `docs/en/artists/index.html`）傳入 `lobby_url="../index.html"`、`artists_url="./index.html"`、`share_base_url="../share/"`，並依層級設定 `static_data_url`（中文版 `../static/data/artist_catalog.js`、英文版 `../../static/data/artist_catalog.js`）。
  * 主播個人專頁渲染時傳入 `lobby_url="../../index.html"`（用以倒回上層的大廳）。
  * 本地運行時，不傳入此變數，自動 Fallback 到 Flask 路由 `url_for('main.lobby')` 與 `url_for('main.artists_catalog')`。
* **結果**：完美實現了本地開發路由與靜態部署路由的無縫雙軌切換。

---

## 5. 雙擊發布流水線 (`deploy.bat`)

1. **`python db_sync.py dump`**：將本機 `vtuber_songs.db` 匯出為純文字 UTF-8 快照 `database_dump.sql`（取代直接提交二進位 `.db`）。
2. **`python run_tests.py`**：依序執行資料庫與 `db_sync` 還原驗證、API/CRUD 沙盒、前端 DOM/批次檔格式檢查，以及 `build_static.py` 靜態雙語打包（`docs/`）；任一環節失敗即中止發布。
3. **白名單 `git add` & `git commit`**：明確只將 `app/`、`docs/`、`manuals/`、`tests/`、`database_dump.sql` 與核心根目錄腳本加入暫存區，避免誤將二進位資料庫或本機 `reports/` 推上 GitHub。
4. **`git push`（含 3 次瞬斷重試）**：完成推送，更新 GitHub Pages 線上網站。
