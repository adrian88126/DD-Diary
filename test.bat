@echo off
chcp 65001 >nul
title DDDiary - 全系統功能自動化測試套件

set "PY_BIN=python"
if exist ".venv\Scripts\python.exe" (
    set "PY_BIN=.venv\Scripts\python.exe"
)

"%PY_BIN%" run_tests.py
echo.
pause
