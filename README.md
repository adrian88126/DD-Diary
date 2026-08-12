# 🎵 DDDiary — VTuber 歌唱資料庫與時間軸彙整系統

[![AI Co-Developed](https://img.shields.io/badge/AI-Co--Developed-blueviolet?style=for-the-badge&logo=google-gemini)](https://github.com)
[![GitHub Pages](https://img.shields.io/badge/GitHub_Pages-Active-success?style=for-the-badge&logo=github)](https://pages.github.com)
[![Framework](https://img.shields.io/badge/Framework-Flask_3.x-blue?style=for-the-badge&logo=flask)](https://flask.palletsprojects.com/)

**DDDiary** 是一個專為 VTuber 設計的歌唱資料庫與歌單時間軸彙整系統。支援本地端進行資料庫管理、自動同步 YouTube、智慧解析時間軸，並可一鍵編譯打包為 100% 靜態、支援中英雙語切換、支援 Light/Dark 主題的靜態網頁，免費託管於 GitHub Pages 進行離線或線上分享。

---

## ✨ 核心亮點與功能

1. **高質感玻璃大廳 (Lobby)**
   * **簡約現代設計**：首頁採用高質感的 Glassmorphism（玻璃摩登風）卡片網格，捨棄雜亂的代表色與大頭貼，統一使用優雅的紫色霓虹光芒。
   * **全站數據快照**：頂部即時顯示收錄歌曲數、歌唱紀錄數、關聯影片數。
   * **光暗主題切換**：完美支援深色（Dark）與淺色（Light）模式，並帶有滑順的過渡動畫。
   * **側邊欄週表牆**：點擊可展開全主播週表行程，點選週表圖片可開啟大圖輪播燈箱。

2. **個人歌唱專頁與公開分享**
   * **四分流分頁系統**：將「拿手歌單」、「歌回紀錄」、「其他影片（直播/雜談）」、「歌回時間軸（帶秒數跳轉）」與「MV 影片」分類呈現。
   * **快捷篩選器**：在「其他影片」中，內建「全部」、「雜談/單人」、「連動/合作」以及「短影音」一鍵快速過濾。
   * **平滑視覺細節**：過長的個人簡介採用 `linear-gradient` 底端淡出遮罩，避免文字被直接截斷的突兀感。

3. **智慧歌單時間軸彙整與後台**
   * **時間軸分割工具**：貼上 YouTube 留言區的原始文字（如 `1:20:10 歌名`），智慧型批次解析並建立演唱紀錄。
   * **靜態登入安全攔截**：點擊「登入」在 Flask 環境下進入後台，在 GitHub Pages 靜態版下則會跳出 Toast 警告，避免 404 報錯。

4. **一鍵靜態雙語打包**
   * 本地進行資料同步與新增後，一鍵執行編譯腳本，即可輸出支援 **中文/英文雙語切換** 且相容 `file:///` 離線雙擊開啟的靜態網站。

---

## 🛠️ 技術棧

* **後端**：Python 3.10+ / Flask 3.x / SQLAlchemy 2.x / Flask-Babel (多國語系) / SQLite
* **前端**：Vanilla HTML5 / Vanilla CSS (Theme Variables) / Vanilla JavaScript (傳統腳本加載，100% 避免 `type="module"` 的本地 CORS 封鎖)
* **打包**：Jinja2 Static Generator

---

## 🚀 本地開發與後台管理

### 1. 安裝環境與套件
```bash
pip install -r requirements.txt
```

### 2. 啟動 Flask 伺服器 (本地管理與登錄)
```bash
python run.py
```
訪問 **`http://127.0.0.1:5000/`**。
* 點擊右上角「登入」（預設密碼為 `admin123`），進入後台進行主播管理、歌曲資料登錄、YouTube 影片同步與時間軸解析。

### 3. 一鍵編譯為靜態網頁
當您在本地後台更新了資料庫內容後，執行打包指令：
```bash
python build_static.py
```
這會自動清空並將最新的 SQLite 資料渲染成靜態 HTML，中英文版檔案會完全輸出在 **`docs/`** 目錄下。

---

## 🌐 部署至 GitHub Pages

1. 將本專案推送（Push）至您的 GitHub 儲存庫。
2. 前往 GitHub 儲存庫的 **Settings** ➡️ **Pages**。
3. 在 **Build and deployment** 下將 Source 設定為 `Deploy from a branch`。
4. **Branch** 選擇 `main` (或您的主分支)，資料夾指定為 `/docs`，點擊 **Save**。
5. 稍等一分鐘，即可在線上造訪您的 VTuber 歌唱存檔網站！

---

## 📚 專案開發手冊與系統架構

有關資料庫 Schema 設計、Flask Blueprint 路由、前端 JS 職責以及靜態編譯原理，請參閱：
👉 [**PROJECT_MANUAL.md (專案開發與架構手冊)**](PROJECT_MANUAL.md)

---

## 📄 開源授權與使用聲明

本專案採用 **MIT 授權條款 (MIT License)** 開源。
歡迎自由 Clone、Fork 或拷貝修改本專案，應用於您喜愛的主播（VTuber）個人歌唱存檔與時間軸彙整展示！

*AI Co-Developed with Google Gemini AI (Antigravity)*
