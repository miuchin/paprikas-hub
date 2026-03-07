@echo off
setlocal ENABLEDELAYEDEXPANSION

set PORT=%1
if "%PORT%"=="" set PORT=8015

set PYTHON=python

if not exist ".venv" (
  echo [Paprikas Hub] Kreiram virtualenv (.venv)...
  %PYTHON% -m venv .venv
  if errorlevel 1 goto :err
)

call .venv\Scripts\activate.bat

echo [Paprikas Hub] Instaliram dependencies...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
if errorlevel 1 goto :err

echo [Paprikas Hub] Startujem server na http://127.0.0.1:%PORT%/
python server\paprikas_server.py --host 0.0.0.0 --port %PORT%
goto :eof

:err
echo.
echo [Paprikas Hub] GRESKA. Proveri da li je instaliran Python 3.13+ i da li je u PATH.
pause
exit /b 1
