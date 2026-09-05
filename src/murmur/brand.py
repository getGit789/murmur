"""One place for the name, the colours, and the logo.

Change a value here and the tray icon, the pill, and the window icon all
follow. No image files to hunt down - every mark is drawn in code.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

NAME = "Murmur"
VERSION = "1.4.0"
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

# Every size Windows asks for, from the tray at 100% up to the desktop
# at 200%. Each one is drawn fresh, never stretched from another.
ICO_SIZES = [16, 20, 24, 32, 40, 48, 64, 96, 128, 256]


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

    # Small icons need a bigger, bolder mark or the mic turns to fluff
    # in the tray. The shape is zoomed about the centre, and no stroke
    # is allowed thinner than about 1.6 real pixels.
    zoom = 1.0 if size >= 64 else 1.15 if size >= 32 else 1.32
    thinnest = 1.6 * scale

    def at(value: float) -> float:
        """A point on the 64 unit grid, zoomed about the centre."""
        return (32 + (value - 32) * zoom) * unit

    def wide(value: float) -> float:
        """A width on the 64 unit grid, never thinner than `thinnest`."""
        return max(value * zoom * unit, thinnest)

    # A mic capsule sitting in a cradle. Bold and simple, so it still
    # reads at 16 pixels in the taskbar.
    draw.rounded_rectangle(
        (at(27), at(15), at(37), at(35)),
        radius=5 * zoom * unit,
        fill=ink,
    )
    draw.arc(
        (at(21), at(21), at(43), at(43)),
        start=0,
        end=180,
        fill=ink,
        width=int(wide(3.6)),
    )
    stem = wide(3.2) / 2
    draw.rounded_rectangle(
        (at(32) - stem, at(41), at(32) + stem, at(50)),
        radius=stem,
        fill=ink,
    )

    return image.resize((size, size), Image.LANCZOS)


def write_ico(path: Path) -> Path:
    """Save a multi size .ico for the exe, the shortcuts and the installer.

    The biggest frame must be the base image. Pillow throws away every
    requested size larger than the base, so a 16 pixel base would leave
    a file with nothing but a 16 pixel icon in it - and Windows would
    stretch that across the desktop.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    frames = [draw_mark(s, "recording") for s in ICO_SIZES]
    base, rest = frames[-1], frames[:-1]
    base.save(
        path,
        format="ICO",
        sizes=[(s, s) for s in ICO_SIZES],
        append_images=rest,
    )
    return path
