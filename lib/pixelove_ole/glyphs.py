"""Bitmaps ('#' = filled) extruded into voxels by geometry.voxel_block."""

# Chunky 6x7 font with two-cell strokes for the big PIXELOVE / OLE letters.
BLOCK_GLYPHS = {
    "P": ("#####.",
          "##..##",
          "##..##",
          "#####.",
          "##....",
          "##....",
          "##...."),
    "I": ("####",
          ".##.",
          ".##.",
          ".##.",
          ".##.",
          ".##.",
          "####"),
    "X": ("##..##",
          "##..##",
          ".####.",
          "..##..",
          ".####.",
          "##..##",
          "##..##"),
    "E": ("######",
          "##....",
          "##....",
          "#####.",
          "##....",
          "##....",
          "######"),
    "L": ("##....",
          "##....",
          "##....",
          "##....",
          "##....",
          "##....",
          "######"),
    "O": (".####.",
          "##..##",
          "##..##",
          "##..##",
          "##..##",
          "##..##",
          ".####."),
    "V": ("##..##",
          "##..##",
          "##..##",
          "##..##",
          ".####.",
          ".####.",
          "..##.."),
}

# Thin 5x7 font for the caption; embolden() thickens it.
CAPTION_GLYPHS = {
    "G": (".###.", "#...#", "#....", "#.###", "#...#", "#...#", ".###."),
    "A": (".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "M": ("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),
    "I": (".###.", "..#..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "N": ("#...#", "##..#", "##..#", "#.#.#", "#..##", "#..##", "#...#"),
    "O": (".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "W": ("#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"),
    "P": ("####.", "#...#", "#...#", "####.", "#....", "#....", "#...."),
    "R": ("####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"),
    "E": ("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    "Z": ("#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"),
    "!": ("#", "#", "#", "#", "#", ".", "#"),
    " ": ("..", "..", "..", "..", "..", "..", ".."),
}

SPACE_INVADER = (
    "..#.....#..",
    "...#...#...",
    "..#######..",
    ".##.###.##.",
    "###########",
    "#.#######.#",
    "#.#.....#.#",
    "...##.##...",
)

PIXEL_PLUS = (".#.", "###", ".#.")
PIXEL_SQUARE = ("#",)


def embolden(rows):
    """Classic pixel-font bold: OR every row with itself shifted one cell right."""
    widened = []
    for line in rows:
        padded = line + "."
        widened.append("".join("#" if padded[i] == "#" or (i > 0 and padded[i - 1] == "#") else "."
                               for i in range(len(padded))))
    return tuple(widened)


# Letters whose middle strokes would merge into a blob under embolden().
CAPTION_BOLD_OVERRIDES = {
    "G": (".####.", "##..##", "##....", "##.###", "##..##", "##..##", ".####."),
    "M": ("##...##", "###.###", "##.#.##", "##.#.##", "##...##", "##...##", "##...##"),
    "W": ("##...##", "##...##", "##...##", "##.#.##", "##.#.##", "###.###", "##...##"),
}


def bold_caption_glyphs():
    """Caption font emboldened glyph by glyph, so letter gaps survive."""
    glyphs = {character: embolden(rows) for character, rows in CAPTION_GLYPHS.items()}
    glyphs.update(CAPTION_BOLD_OVERRIDES)
    return glyphs


def text_rows(text, glyphs, spacing=1):
    """Lay out a string as one bitmap, glyphs separated by `spacing` empty columns."""
    height = len(next(iter(glyphs.values())))
    rows = [""] * height
    for index, character in enumerate(text):
        glyph = glyphs[character]
        for row in range(height):
            rows[row] += glyph[row] + ("." * spacing if index < len(text) - 1 else "")
    return tuple(rows)
