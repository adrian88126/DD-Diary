@echo off
chcp 65001 >nul
title DDDiary - 自動化測試、打包與上傳至 GitHub

echo ============================================================
echo   DDDiary 全系統自檢、靜態網頁打包與 GitHub 一鍵發布工具
echo ============================================================
echo.

:: 1. 偵測 Python 執行檔 (優先使用專案虛擬環境)
set "PY_BIN=python"
if exist ".venv\Scripts\python.exe" (
    set "PY_BIN=.venv\Scripts\python.exe"
    echo [*] 偵測到專案虛擬環境 (.venv)
) else (
    echo [i] 使用系統環境 Python
)

echo.
echo [1/5] 正在將本機 SQLite 資料庫匯出為純文字版控快照 (database_dump.sql)...
echo ------------------------------------------------------------
"%PY_BIN%" db_sync.py dump
if %ERRORLEVEL% neq 0 (
    echo.
    echo [!] 警告：匯出 database_dump.sql 失敗！已中止後續發布流程。
    echo.
    pause
    exit /b 1
)

echo.
echo [2/5] 正在執行全系統功能自動化測試與雙語靜態網頁打包 (docs/)...
echo ------------------------------------------------------------
"%PY_BIN%" run_tests.py
if %ERRORLEVEL% neq 0 (
    echo.
    echo [!] 警告：全系統功能測試或靜態打包發現錯誤！已自動攔截中止上傳。
    echo 請根據上方測試報告修正問題後再重新執行。
    echo.
    pause
    exit /b 1
)

echo.
echo [3/5] 準備 Git 提交訊息...
echo ------------------------------------------------------------
set "DEFAULT_MSG=update: refresh data and rebuild static pages"
set "USER_MSG="
set /p "USER_MSG=請輸入本次更新說明 (直接按 Enter 將使用預設說明): "

if "%USER_MSG%"=="" (
    set "COMMIT_MSG=%DEFAULT_MSG%"
) else (
    set "COMMIT_MSG=%USER_MSG%"
)

echo.
echo 使用的 Commit 訊息: "%COMMIT_MSG%"
echo.

echo [4/5] 正在依白名單加入程式碼、靜態網頁與純文字 SQL 快照並提交...
echo ------------------------------------------------------------
git add -A -- app/ docs/ manuals/ tests/ database_dump.sql build_static.py db_sync.py init_db.py run.py run_tests.py sync_cli.py requirements.txt .gitignore .env.example README.md deploy.bat start.bat sync.bat test.bat
if %ERRORLEVEL% neq 0 (
    echo.
    echo [!] 警告：Git 暫存檔案失敗！已中止提交。
    echo.
    pause
    exit /b 1
)
git commit -m "%COMMIT_MSG%"
if %ERRORLEVEL% neq 0 (
    echo [i] 沒有偵測到新的變更需要提交，準備檢查是否有未推送的 Commit...
)

echo.
echo [5/5] 正在推送至 GitHub 遠端儲存庫 (git push)...
echo ------------------------------------------------------------
set "RETRY_COUNT=0"
:PUSH_RETRY
set /a RETRY_COUNT+=1
git push
if %ERRORLEVEL% neq 0 (
    if %RETRY_COUNT% lss 3 (
        echo.
        echo [!] 遭遇 GitHub 伺服器瞬斷 (第 %RETRY_COUNT%/3 次)，等待 5 秒後自動重試...
        timeout /t 5 /nobreak >nul
        goto PUSH_RETRY
    )
    echo.
    echo [!] 推送失敗！若上方顯示 remote: Internal Server Error，代表 GitHub 官方伺服器目前異常中，請隔幾分鐘後再執行。
    echo.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo   全部完成！全系統測試通過，純文字快照與靜態頁面已發布至 GitHub！
echo   GitHub Pages 預計於 1 至 2 分鐘內完成線上更新。
echo ============================================================
echo.
pause
