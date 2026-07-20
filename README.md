# 🎵 VTuber Song Database & Timeline Curator (VTuber 歌唱資料庫與時間軸彙整系統)

[![AI Co-Developed](https://img.shields.io/badge/AI-Co--Developed-blueviolet?style=for-the-badge&logo=google-gemini)](https://github.com)
[![GitHub Pages](https://img.shields.io/badge/GitHub_Pages-Active-success?style=for-the-badge&logo=github)](https://pages.github.com)

本專案是一個專為 VTuber 設計的歌唱資料庫與歌單時間軸彙整系統。
本專案是由開發者與 **Google Gemini (Antigravity AI)** 共同協同開發完成。

---

## ✨ 核心功能

1. **個人歌唱專頁與公開分享**
   - 包含常駐拿手歌、點歌歌單、歷史歌單統計。
   - 獨立的「歌回直播」分頁，將歌回影片與日常雜談影片分離展示。
   - 內置 YouTube 播放器與秒數跳轉控制。
2. **快捷篩選總庫目錄**
   - 提供依影片類型、所屬主播、以及有無建立時間軸等多重聯動過濾器。
3. **智慧歌單時間軸彙整**
   - 彈出式視窗 (Modal Overlay) 互動，支持直接貼上 YouTube 說明欄的時間軸格式文字，一鍵自動解析並批量登錄。
4. **一鍵靜態打包**
   - 本地進行後台數據維護與爬蟲同步，一鍵匯出為 100% 靜態網站，免費託管於 GitHub Pages。

---

## 🛠️ 技術棧

- **前端**：Vanilla HTML / CSS (Neon CSS theme) / Javascript (SPA)
- **後端**：FastAPI (Python)
- **資料庫**：SQLite
- **打包工具**：Jinja2 + Python static generator

---

## 🚀 本地開發與後台管理

### 1. 安裝套件
```bash
pip install -r requirements.txt
```

### 2. 啟動伺服器 (本地管理)
```bash
python main.py
```
訪問 `http://127.0.0.1:8000/`，點擊右上方「管理登入」（預設密碼為 `admin123`）即可啟用所有後台登錄功能與爬蟲同步。

### 3. 一鍵打包靜態網頁
當在本地管理並新增了時間軸或主播資料後，執行以下指令：
```bash
python build_static.py
```
打包程式會將 SQLite 資料轉出為 JSON，並自動將分享頁渲染成靜態 HTML 儲存於 `docs/` 目錄。

---

## 🌐 部署至 GitHub Pages

1. 將本專案推送至您的 GitHub 公開儲存庫。
2. 前往儲存庫的 **Settings** ➡️ **Pages**。
3. 在 **Build and deployment** 下的 **Source** 選擇 `Deploy from a branch`。
4. **Branch** 選擇 `main` (或您的主分支)，資料夾選擇 `/docs`，點擊 Save。
5. 稍等一分鐘，您的網站就正式在線了！

---

## 📚 專案開發手冊與系統架構

有關本專案的完整技術架構、資料庫 Schema、所有 API 接口與頁面路由說明，請參閱專案根目錄下的開發手冊：
👉 [**PROJECT_MANUAL.md (專案功能與架構手冊)**](PROJECT_MANUAL.md)

---

## 📄 開源授權與使用聲明 (Open Source & License)

本專案採用 **MIT 授權條款 (MIT License)** 開源。
歡迎並鼓勵任何人自由 Clone、Fork、拷貝或修改本專案，並將其應用於您喜愛的主播（VTuber）個人時間軸存檔與歌唱展示資料庫！

---

## 🤝 聲明與致謝
本專案的全部代碼與架構由 **Google Gemini (Antigravity AI)** 全程協同開發與優化。


