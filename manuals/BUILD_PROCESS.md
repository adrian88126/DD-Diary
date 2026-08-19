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
    ├── 2. 複製靜態檔案 ─────→ 將 app/static/ 複製至 docs/static/ (排除 *.bak 檔案)
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

## 2. 多國語系預渲染原理 (Multi-language SSR)

Flask 應用在運行時，是利用 `Flask-Babel` 來實現多國語系的。
為了在**沒有後端服務**的靜態網頁（GitHub Pages）上也能提供「中文/英文切換」功能，`build_static.py` 在預渲染時使用了一個巧妙的 Request Context 模擬技術：

```python
with app.test_request_context(environ_base={'HTTP_COOKIE': f'lang={lang}'}):
```

### 運作原理：
1. `build_static.py` 分別為 `lang='zh'`（中文）與 `lang='en'`（英文）建立了一個偽造的請求上下文。
2. 上下文的 Cookie 寫入 `lang=zh` 或 `lang=en`，這會直接觸發專案內部的 `i18n.py` 語言檢測攔截器，強制 Flask 載入對應的語系翻譯字典（`zh.json` 或 `en.json`）。
3. 隨後呼叫 `render_template` 進行預渲染：
   * **中文版**：輸出大廳至 `docs/index.html`，主播專頁輸出至 `docs/share/{id}/index.html`。
   * **英文版**：輸出大廳至 `docs/en/index.html`，主播專頁輸出至 `docs/en/share/{id}/index.html`。
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
  * 大廳本身渲染時傳入 `lobby_url="index.html"`。
  * 主播個人專頁渲染時傳入 `lobby_url="../../index.html"`（用以倒回上層的大廳）。
  * 本地運行時，不傳入此變數，自動 Fallback 到 Flask 路由 `url_for('main.lobby')` 指向 `/`。
* **結果**：完美實現了本地開發路由與靜態部署路由的無縫雙軌切換。
