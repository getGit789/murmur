@echo off
cd /d "%~dp0"
set PYTHONPATH=%~dp0src
if not exist ".venv" (
  echo First run: building the virtual env. This takes a few minutes.
  python -m venv .venv
  call .venv\Scripts\activate.bat
  python -m pip install --upgrade pip
  pip install -r requirements.txt
) else (
  call .venv\Scripts\activate.bat
)
python -m murmur
pause
