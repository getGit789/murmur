@echo off
REM Builds dist\Murmur\Murmur.exe
cd /d "%~dp0"
call .venv\Scripts\activate.bat
pip install -q pyinstaller
rmdir /s /q build 2>nul
rmdir /s /q dist 2>nul
pyinstaller --noconfirm --clean murmur.spec
echo.
if exist "dist\Murmur\Murmur.exe" (
  echo Built: %~dp0dist\Murmur\Murmur.exe
  echo Next:  run install.bat to put it in your Start Menu.
) else (
  echo BUILD FAILED. Read the messages above.
)
pause
