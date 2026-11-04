@echo off
chcp 65001 >nul
title DDDiary - 自動抓取最新 YouTube 影片 (預設排除星璃)

echo ============================================================
echo   DDDiary 主播 YouTube 最新影片同步工具 (sync.bat)
echo ============================================================
echo.

set "PY_BIN=python"
if exist ".venv\Scripts\python.exe" (
    set "PY_BIN=.venv\Scripts\python.exe"
    echo [*] 偵測到專案虛擬環境 (.venv)
) else (
    echo [i] 使用系統環境 Python
)

echo.
echo [*] 正在抓取各活躍主播最新 5 部 YouTube 影片 (預設自動排除：星璃)...
echo ------------------------------------------------------------
"%PY_BIN%" sync_cli.py --limit 5
echo.
echo ============================================================
echo   同步作業完成！可雙擊 start.bat 開啟後台填寫歌回時間軸。
echo ============================================================
echo.
pause
