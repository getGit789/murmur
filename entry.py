"""Start point for the built .exe.

PyInstaller runs this as a plain script, so it cannot use the relative
imports that `python -m murmur` relies on. Both routes end up here.
"""

import multiprocessing
import sys

from murmur.ui.qtapp import run

if __name__ == "__main__":
    multiprocessing.freeze_support()  # stops the app opening copies of itself
    sys.exit(run())
