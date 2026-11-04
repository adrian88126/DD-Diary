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
echo [1/4] 正在執行全系統功能自動化測試與雙語靜態網頁打包 (docs/)...
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
echo [2/4] 準備 Git 提交訊息...
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

echo [3/4] 正在將變更加入 Git 暫存區並提交...
echo ------------------------------------------------------------
git add .
git commit -m "%COMMIT_MSG%"
if %ERRORLEVEL% neq 0 (
    echo [i] 沒有偵測到新的變更需要提交，準備檢查是否有未推送的 Commit...
)

echo.
echo [4/4] 正在推送至 GitHub 遠端儲存庫 (git push)...
echo ------------------------------------------------------------
git push
if %ERRORLEVEL% neq 0 (
    echo.
    echo [!] 推送失敗！請檢查您的網路連線或 GitHub 存取權限。
    echo.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo   全部完成！全系統測試通過，最新靜態頁面已成功發布至 GitHub！
echo   GitHub Pages 預計於 1 至 2 分鐘內完成線上更新。
echo ============================================================
echo.
pause
