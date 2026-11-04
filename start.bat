@echo off
chcp 65001 >nul
title DDDiary - 後台管理伺服器 (http://127.0.0.1:5000)

echo ============================================================
echo   DDDiary 本地管理伺服器啟動工具 (start.bat)
echo ============================================================
echo.

set "PY_BIN=python"
if exist ".venv\Scripts\python.exe" (
    set "PY_BIN=.venv\Scripts\python.exe"
    echo [*] 偵測到專案虛擬環境 (.venv)
) else (
    echo [i] 使用系統環境 Python
)

echo [*] 將於 2 秒後自動開啟瀏覽器進入「歌回管理 (最新排序)」...
echo [*] 伺服器運行期間請勿關閉此視窗 (按 Ctrl+C 可停止伺服器)。
echo ------------------------------------------------------------
start "" cmd /c "timeout /t 2 /nobreak >nul && start http://127.0.0.1:5000/admin/singing_streams?sort=newest"
"%PY_BIN%" run.py
pause
