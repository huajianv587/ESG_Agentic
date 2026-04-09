@echo off
setlocal

cd /d "%~dp0"

set "PS_EXE=%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe"
if not exist "%PS_EXE%" set "PS_EXE=powershell"

if not exist ".venv\Scripts\python.exe" (
  echo [start] Missing .venv
  echo [start] Run scripts\bootstrap_local_windows.bat first.
  pause
  exit /b 1
)

if not exist ".env" (
  echo [start] Missing .env
  echo [start] Copy .env.example to .env and fill in at least DEEPSEEK_API_KEY or OPENAI_API_KEY.
  pause
  exit /b 1
)

set APP_MODE=local
set LLM_BACKEND_MODE=cloud
set DEMO_FAST_MODE=1
set PYTHONIOENCODING=utf-8

if not "%~1"=="" (
  set PORT=%~1
) else (
  for /f %%p in ('"%PS_EXE%" -NoProfile -ExecutionPolicy Bypass -Command "$ports=8000,8001,8011,8088; foreach($p in $ports){ if(-not (Get-NetTCPConnection -LocalPort $p -State Listen -ErrorAction SilentlyContinue)){ Write-Output $p; break } }"') do set PORT=%%p
)

if not defined PORT set PORT=8011

echo [start] ESG Agentic RAG Copilot demo mode
echo [start] APP_MODE=%APP_MODE%
echo [start] LLM_BACKEND_MODE=%LLM_BACKEND_MODE%
echo [start] DEMO_FAST_MODE=%DEMO_FAST_MODE%
echo [start] URL: http://127.0.0.1:%PORT%/app
echo [start] Press Ctrl+C in this window to stop the demo server.
start "" "%PS_EXE%" -NoProfile -ExecutionPolicy Bypass -Command "$healthUrl='http://127.0.0.1:%PORT%/health'; $appUrl='http://127.0.0.1:%PORT%/app'; for($i=0; $i -lt 90; $i++){ try { Invoke-WebRequest -UseBasicParsing $healthUrl -TimeoutSec 2 | Out-Null; Start-Process $appUrl; exit 0 } catch { Start-Sleep -Milliseconds 1000 } }; Start-Process $appUrl"

".venv\Scripts\python.exe" -m uvicorn gateway.main:app --host 0.0.0.0 --port %PORT%
