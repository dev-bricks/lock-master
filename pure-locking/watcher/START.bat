@echo off
chcp 65001 >nul
title lock-master Watcher

set "DIR=%~dp0"
set PYTHONIOENCODING=utf-8

echo ========================================
echo   lock-master Watcher
echo ========================================
echo.

:: Daemon (Scanner) im Hintergrund starten oder laufenden Daemon wiederverwenden
echo [1/2] Starte/prüfe Watcher-Daemon ...
start "" /B python "%DIR%lock_watcher.py" --update-cache

:: Kurz warten, damit die DB/Heartbeat initialisiert ist
:: ping works even when stdin is redirected by a scheduler, CI job or pipe.
ping -n 3 127.0.0.1 >nul

:: Web-Server nicht doppelt starten
powershell -NoProfile -ExecutionPolicy Bypass -Command "try { Invoke-RestMethod -Uri 'http://127.0.0.1:8095/api/stats' -TimeoutSec 1 | Out-Null; exit 0 } catch { exit 1 }" >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    echo [2/2] Web-Server läuft bereits auf http://127.0.0.1:8095
    echo Öffne GUI im Browser ...
    start "" "http://127.0.0.1:8095"
    echo.
    echo Daemon läuft session-übergreifend weiter; kein zweiter Web-Server gestartet.
    echo ========================================
    goto :EOF
)

:: Web-Server starten (bleibt im Vordergrund)
echo [2/2] Starte Web-Server auf http://127.0.0.1:8095 ...
echo.
echo Druecke Strg+C zum Beenden des Web-Servers. Der Daemon läuft weiter.
echo ========================================

:: GUI im Browser öffnen, sobald der Server hochgefahren ist (asynchron, mit kurzer Verzögerung)
start "" /B powershell -NoProfile -Command "Start-Sleep -Seconds 3; Start-Process 'http://127.0.0.1:8095'"
python "%DIR%web_server.py" --port 8095
