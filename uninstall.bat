@echo off
REM Removes Murmur. Your settings and dictionary are kept.
setlocal
set "TARGET=%LOCALAPPDATA%\Programs\Murmur"
set "SM=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Murmur.lnk"
set "SU=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\Murmur.lnk"

taskkill /im Murmur.exe /f >nul 2>&1
if exist "%SU%" del "%SU%"
if exist "%SM%" del "%SM%"
if exist "%TARGET%" rmdir /s /q "%TARGET%"

echo Murmur removed.
echo Your settings are still at %APPDATA%\Murmur ^(delete by hand if you want^).
pause
