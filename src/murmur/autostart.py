"""Start with Windows.

We drop a shortcut in the Startup folder. No registry edits, and you can
delete the shortcut by hand if you ever want to.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from . import APP_NAME

SHORTCUT_NAME = f"{APP_NAME}.lnk"


def startup_dir() -> Path:
    appdata = os.environ.get("APPDATA") or str(Path.home())
    return Path(appdata) / "Microsoft/Windows/Start Menu/Programs/Startup"


def shortcut_path() -> Path:
    return startup_dir() / SHORTCUT_NAME


def target() -> tuple[str, str, str]:
    """Returns (program to run, arguments, folder to start in).

    The startup copy runs with --hidden: tray only, no window. The hotkey
    still works. Opening it from the Start Menu shows the window.
    """
    exe = Path(sys.executable)
    if getattr(sys, "frozen", False):
        # Built app: the exe is the whole thing.
        return str(exe), "--hidden", str(exe.parent)
    # Running from source: use pythonw so no black console window appears.
    windowless = exe.with_name("pythonw.exe")
    runner = windowless if windowless.exists() else exe
    package_root = Path(__file__).resolve().parents[1]
    return str(runner), "-m murmur --hidden", str(package_root)


def is_enabled() -> bool:
    return shortcut_path().exists()


def enable() -> None:
    program, arguments, workdir = target()
    link = shortcut_path()
    link.parent.mkdir(parents=True, exist_ok=True)
    icon = Path(__file__).resolve().parents[2] / "assets" / "murmur.ico"

    script = f"""
$s = (New-Object -ComObject WScript.Shell).CreateShortcut('{link}')
$s.TargetPath = '{program}'
$s.Arguments = '{arguments}'
$s.WorkingDirectory = '{workdir}'
$s.Description = '{APP_NAME} - push to talk dictation'
"""
    if icon.exists():
        script += f"$s.IconLocation = '{icon}'\n"
    script += "$s.Save()\n"

    subprocess.run(
        ["powershell", "-NoProfile", "-NonInteractive", "-Command", script],
        check=True,
        capture_output=True,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )


def disable() -> None:
    shortcut_path().unlink(missing_ok=True)


def toggle() -> bool:
    """Flip it. Returns True if it is now on."""
    if is_enabled():
        disable()
        return False
    enable()
    return True
