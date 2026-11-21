@echo off
chcp 65001 >nul
cd /d "%~dp0"
if not exist ".venv-motion\Scripts\python.exe" (
  echo .venv-motion 환경이 없습니다. docs\MOTION_PIPELINE_KO.md 설치 안내를 확인하세요.
  pause
  exit /b 1
)
".venv-motion\Scripts\python.exe" -B -X utf8 scripts\motion_pipeline.py review
if errorlevel 1 pause
