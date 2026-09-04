"""One place for the name, the colours, and the logo.

Change a value here and the tray icon, the pill, and the window icon all
follow. No image files to hunt down - every mark is drawn in code.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

NAME = "Murmur"
VERSION = "1.1.0"
TAGLINE = "Speak. It types."

# Light + teal
BG = "#f4f4f2"          # pill body
BORDER = "#c4c4bd"      # hairline edge
HALO = "#e8e8e3"        # soft outer ring, keeps the shape on white
TEXT = "#1c1c1a"        # main text
MUTED = "#6b6b66"       # quiet text
ACCENT = "#0d9488"      # teal - listening
WORKING = "#b45309"     # amber - thinking
ERROR = "#b91c1c"       # red - something broke
IDLE = "#9a9a94"        # grey - asleep

STATE_COLOUR = {
    "idle": IDLE,
    "recording": ACCENT,
    "working": WORKING,
    "error": ERROR,
}

# Magenta is the "see through this" key colour for the pill window.
CHROMA_KEY = "#ff00fe"


def _hex_to_rgb(value: str) -> tuple[int, int, int]:
    value = value.lstrip("#")
    return tuple(int(value[i : i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]


def draw_mark(size: int, state: str = "idle", solid: bool = True) -> Image.Image:
    """The Murmur mark: a soft square, a mic, and a sound wave under it."""
    scale = 4  # draw big, shrink down - gives smooth edges
    box = size * scale
    image = Image.new("RGBA", (box, box), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    fill = _hex_to_rgb(STATE_COLOUR.get(state, IDLE))
    ink = (255, 255, 255)

    if solid:
        draw.rounded_rectangle(
            (0, 0, box - 1, box - 1), radius=int(box * 0.28), fill=fill
        )
    else:
        ink = fill

    unit = box / 64.0

    # A mic capsule sitting in a cradle. Bold and simple, so it still
    # reads at 16 pixels in the taskbar.
    draw.rounded_rectangle(
        (27 * unit, 15 * unit, 37 * unit, 35 * unit),
        radius=5 * unit,
        fill=ink,
    )
    draw.arc(
        (21 * unit, 21 * unit, 43 * unit, 43 * unit),
        start=0,
        end=180,
        fill=ink,
        width=int(3.6 * unit),
    )
    draw.rounded_rectangle(
        (30.4 * unit, 41 * unit, 33.6 * unit, 50 * unit),
        radius=1.6 * unit,
        fill=ink,
    )

    return image.resize((size, size), Image.LANCZOS)


def write_ico(path: Path) -> Path:
    """Save a multi size .ico for the window and, later, the installer."""
    path.parent.mkdir(parents=True, exist_ok=True)
    sizes = [16, 24, 32, 48, 64, 128, 256]
    frames = [draw_mark(s, "recording") for s in sizes]
    frames[0].save(path, format="ICO", sizes=[(s, s) for s in sizes], append_images=frames[1:])
    return path
