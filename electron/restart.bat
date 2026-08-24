@echo off
rem 一键重启桌宠脚本
taskkill /F /IM electron.exe 2>nul
taskkill /F /IM backend_server.exe 2>nul
timeout /t 1 /nobreak >nul
cd /d E:\code\dsh\desktop-pet\electron
start "" ".\node_modules\electron\dist\electron.exe" .
echo 桌宠已启动
