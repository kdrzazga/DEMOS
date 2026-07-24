import os

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))


class Constants:

    WIDTH = 1150
    HEIGHT = 700
    FPS = 25

    COLUMNS = 40
    ROWS = 25
    FONT_BASE = 0xE000

    FONT_PATH = os.path.join(_ROOT, "lib", "resources", "C64_Pro_Mono-STYLE.ttf")

    SPACE = 32

    # corners the reveal grows from, filled in this order
    TOP_LEFT, TOP_RIGHT, BOTTOM_RIGHT, BOTTOM_LEFT = range(4)
    CORNERS = 4

    # characters added per call to render_from_corners
    REVEAL_SPEED = 6

    # $D020 and $D021 as set by the program
    BORDER_COLOR = 0
    BACKGROUND_COLOR = 0

    # standard C64 palette, indexed by colour code
    PALETTE = (
        (0, 0, 0),        # 0  black
        (255, 255, 255),  # 1  white
        (104, 55, 43),    # 2  red
        (112, 164, 178),  # 3  cyan
        (111, 61, 134),   # 4  purple
        (88, 141, 67),    # 5  green
        (53, 40, 121),    # 6  blue
        (184, 199, 111),  # 7  yellow
        (111, 79, 37),    # 8  orange
        (67, 57, 0),      # 9  brown
        (154, 103, 89),   # 10 light red
        (68, 68, 68),     # 11 dark grey
        (108, 108, 108),  # 12 grey
        (154, 210, 132),  # 13 light green
        (108, 94, 181),   # 14 light blue
        (149, 149, 149),  # 15 light grey
    )
