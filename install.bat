@echo off
REM Copies the built app into your account and adds a Start Menu entry.
REM No admin rights needed. Uninstall with uninstall.bat.
setlocal
cd /d "%~dp0"

if not exist "dist\Murmur\Murmur.exe" (
  echo Nothing built yet. Run build.bat first.
  pause & exit /b 1
)

REM A running copy locks its own files. Refuse rather than half install.
tasklist /fi "imagename eq Murmur.exe" 2>nul | find /i "Murmur.exe" >nul
if not errorlevel 1 (
  echo Murmur is still running.
  taskkill /im Murmur.exe /f >nul 2>&1
  timeout /t 2 /nobreak >nul
  tasklist /fi "imagename eq Murmur.exe" 2>nul | find /i "Murmur.exe" >nul
  if not errorlevel 1 (
    echo.
    echo COULD NOT STOP IT. Nothing has been changed.
    echo Close any Murmur error dialog, quit it from the tray, or end
    echo "Murmur.exe" in Task Manager. Then run install.bat again.
    pause & exit /b 1
  )
)

set "TARGET=%LOCALAPPDATA%\Programs\Murmur"
echo Installing to %TARGET%

if exist "%TARGET%" (
  rmdir /s /q "%TARGET%"
  if exist "%TARGET%" (
    echo.
    echo COULD NOT CLEAR THE OLD COPY - a file is locked.
    echo Nothing was installed. Close Murmur and try again.
    pause & exit /b 1
  )
)

xcopy /e /i /q /y "dist\Murmur" "%TARGET%" >nul
if errorlevel 1 goto :failed
if not exist "%TARGET%\Murmur.exe" goto :failed

set "SM=%APPDATA%\Microsoft\Windows\Start Menu\Programs"
powershell -NoProfile -Command ^
  "$s=(New-Object -ComObject WScript.Shell).CreateShortcut('%SM%\Murmur.lnk');" ^
  "$s.TargetPath='%TARGET%\Murmur.exe';" ^
  "$s.WorkingDirectory='%TARGET%';" ^
  "$s.IconLocation='%TARGET%\_internal\assets\murmur.ico';" ^
  "$s.Description='Murmur - Speak. It types.';$s.Save()"

echo.
echo Installed. Search the Start Menu for "Murmur".
echo Turn on "Start Murmur when Windows starts" in Settings (Ctrl+comma).
pause & exit /b 0

:failed
echo.
echo INSTALL FAILED - the files could not be copied.
echo Nothing usable is in %TARGET%. Close Murmur and run install.bat again.
pause & exit /b 1
