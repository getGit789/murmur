"""Design tokens. The single source of truth for how Murmur looks.

Direction: a 1990s MiniDisc deck. Sony MZ-R series, Technics hi-fi,
Windows 95 at its crispest. Light silver body, honest bevels, one dark
glass display window with bright segments behind it.

Rules for anyone editing a view:
  - Never write a raw colour, size, or radius in a component.
  - Point at a token here instead.
  - If a value you need is missing, add it here first.
"""

from __future__ import annotations

from dataclasses import dataclass


# ---------------------------------------------------------------------------
# COLOUR
# Cool silvers and near-white wells. Teal is the accent (same family as
# the tray icon). Red is reserved for the record lamp. The display glass
# is the one dark thing in the app.
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Colour:
    # -- chassis: the silver body of the machine ----------------------------
    chassis:        str = "#d3d5d1"   # window background
    chassis_raised: str = "#dcded9"   # menu bar, status bar
    panel:          str = "#e3e5e0"   # main working surface
    panel_sunken:   str = "#f4f5f2"   # recessed well: lists, fields

    # -- brushed aluminium: top and bottom of the metal gradient ------------
    alu_light:      str = "#f0f1ee"
    alu:            str = "#d7d9d4"
    alu_dark:       str = "#b7b9b3"
    alu_edge:       str = "#ffffff"   # the bright top lip of a bevel

    # -- moulded plastic: buttons ------------------------------------------
    plastic:        str = "#d0d2cd"   # disabled face
    plastic_light:  str = "#eceee9"   # raised face
    plastic_dark:   str = "#c2c4bf"   # pressed face

    # -- seams and edges ----------------------------------------------------
    seam:           str = "#90938d"   # hairline between panels
    bevel_light:    str = "#ffffff"   # lit top-left edge
    bevel_dark:     str = "#83867f"   # shadowed bottom-right edge

    # -- printed text -------------------------------------------------------
    ink:            str = "#212420"   # main text on the body
    ink_dim:        str = "#50534e"   # secondary label
    ink_faint:      str = "#8b8e88"   # disabled / hint
    ink_on_metal:   str = "#2c2e2b"   # text printed on aluminium

    # -- the record lamp ----------------------------------------------------
    record:         str = "#d13328"
    record_glow:    str = "#ff4f3d"   # the lit state of the same lamp
    record_dead:    str = "#3a4640"   # the unlit lamp, resting on the glass
    lamp_ring:      str = "#0a0d0b"   # thin ring holding the lamp in

    # -- the display glass: the one dark surface ---------------------------
    lcd_bg:         str = "#101815"   # dark green-black glass
    lcd_frame:      str = "#454843"   # frame line around the glass
    lcd_text:       str = "#6bf0cf"   # bright segment teal
    lcd_text_dim:   str = "#3f8f7c"   # quieter segment text
    lcd_unlit:      str = "#22302a"   # a segment that is off

    # -- level segments, lit on the glass -----------------------------------
    level_green:    str = "#3ddc55"
    level_amber:    str = "#ffb62e"
    level_peak:     str = "#ff453a"

    # -- the floating pill --------------------------------------------------
    pill_bar:       str = "#e9f2ee"   # voice bars, soft white on the glass

    # -- accent and states --------------------------------------------------
    accent:         str = "#0d9488"   # teal, same family as the tray icon
    focus:          str = "#0d9488"   # keyboard focus ring
    selection:      str = "#c9e8e2"   # selected row in a list
    warning:        str = "#8f5f00"   # dictionary "this looks risky" notice


COLOUR = Colour()


# ---------------------------------------------------------------------------
# TYPE
# Silkscreen labels: small, uppercase, tightly tracked, neutral grotesque.
# Counters, timings and the display: monospaced, so digits do not jump.
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Type:
    # families, in fallback order
    grotesque: str = '"Inter", "Segoe UI", "Helvetica Neue", Arial, sans-serif'
    mono:      str = '"Cascadia Mono", "Consolas", "DejaVu Sans Mono", monospace'

    # size scale, in points
    size_label:    int = 9    # silkscreen labels under controls
    size_micro:    int = 10   # table meta, timestamps
    size_body:     int = 11   # transcript text, fields
    size_heading:  int = 13   # panel titles
    size_readout:  int = 18   # the transcript counter
    size_counter:  int = 24   # the big display digits

    # weights
    weight_normal: int = 400
    weight_medium: int = 500
    weight_bold:   int = 700

    # letter spacing, in em. Silkscreen printing is tight and wide-tracked.
    track_label:  float = 0.14   # UPPERCASE LABELS
    track_body:   float = 0.0
    track_mono:   float = 0.04

    # line height multipliers
    leading_tight: float = 1.15
    leading_body:  float = 1.45


TYPE = Type()


# ---------------------------------------------------------------------------
# SPACE  -- 4 px base grid
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Space:
    xxs: int = 2
    xs:  int = 4
    sm:  int = 8
    md:  int = 12
    lg:  int = 16
    xl:  int = 24
    xxl: int = 32
    xxxl: int = 48


SPACE = Space()


# ---------------------------------------------------------------------------
# RADIUS
# Equipment has firm edges. A little rounding keeps it friendly.
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Radius:
    none:   int = 0    # panels, seams, wells
    sharp:  int = 4    # buttons, fields
    soft:   int = 6    # the display glass and the outer chassis
    lamp:   int = 999  # round: record light, LEDs


RADIUS = Radius()


# ---------------------------------------------------------------------------
# BORDER
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Border:
    hairline: int = 1   # every seam and edge
    thick:    int = 2   # the display frame
    focus:    int = 1   # focus ring width


BORDER = Border()


# ---------------------------------------------------------------------------
# ELEVATION
# Not drop shadows. Bevels. A lit top edge and a shadowed bottom edge.
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Elevation:
    # (top edge colour, bottom edge colour)
    raised:  tuple[str, str] = (COLOUR.bevel_light, COLOUR.bevel_dark)
    pressed: tuple[str, str] = (COLOUR.bevel_dark, COLOUR.bevel_light)
    sunken:  tuple[str, str] = (COLOUR.bevel_dark, COLOUR.bevel_light)
    flush:   tuple[str, str] = (COLOUR.seam, COLOUR.seam)

    # the only real shadow in the app: under the window chrome
    chrome_shadow: str = "rgba(0, 0, 0, 0.45)"


ELEVATION = Elevation()


# ---------------------------------------------------------------------------
# MOTION
# Mechanical, not bouncy. A key press is instant. A meter has weight.
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Motion:
    press_ms:  int = 70    # button travel
    fade_ms:   int = 140   # panel and pill fades
    lamp_ms:   int = 90    # record light on and off

    # Segment meter ballistics: the bar follows the voice at once,
    # the peak marker hangs back and falls slowly.
    meter_peak_decay: float = 0.96   # per update, ~30 updates a second

    ease_mechanical: str = "cubic-bezier(0.2, 0.0, 0.2, 1.0)"


MOTION = Motion()


# ---------------------------------------------------------------------------
# SIZE  -- fixed control sizes, so panels line up on the grid
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Size:
    button_h:      int = 32
    button_min_w:  int = 84
    transport_h:   int = 46   # the big Record / Stop keys
    field_h:       int = 30
    row_h:         int = 30   # dictionary and history rows
    toolbar_h:     int = 40
    display_h:     int = 104  # the glass display window
    lamp:          int = 10   # record light diameter
    window_min:     tuple[int, int] = (820, 540)
    window_default: tuple[int, int] = (1120, 780)
    settings_size: tuple[int, int] = (540, 460)


SIZE = Size()
