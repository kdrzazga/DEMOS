from lib.pixelove_ole.geometry import Gradient, SurfaceStyle, logo_point, voxel_block
from lib.pixelove_ole.glyphs import BLOCK_GLYPHS
from lib.pixelove_ole.part import LogoPart


def top_row_style():
    """PIXELOVE: cyan -> white -> hot pink face, deep blue extrusion."""
    face = Gradient((0.0, (0.45, 1.0, 0.95)),
                    (0.4, (0.95, 0.92, 1.0)),
                    (0.6, (1.0, 0.55, 0.78)),
                    (1.0, (1.0, 0.18, 0.55)))
    return SurfaceStyle(face, side_near=(0.22, 0.25, 0.85), side_far=(0.08, 0.04, 0.3),
                        edge=(1.0, 1.0, 1.0), edge_width=1.5)


def bottom_row_style():
    """OLE (and the extra V): yellow -> orange face, magenta/red extrusion."""
    face = Gradient((0.0, (1.0, 0.97, 0.45)),
                    (0.45, (1.0, 0.82, 0.12)),
                    (0.55, (1.0, 0.68, 0.08)),
                    (1.0, (1.0, 0.45, 0.05)))
    return SurfaceStyle(face, side_near=(0.95, 0.15, 0.5), side_far=(0.35, 0.02, 0.25),
                        edge=(1.0, 1.0, 0.85), edge_width=1.5)


class BlockLetter(LogoPart):
    """A single extruded voxel letter, pivoting around its own centre."""

    def __init__(self, character, x, y, z, cell_width, cell_height, depth, style, name=None):
        super().__init__(name or character, x, y, z)
        self.character = character
        self.cell_width = cell_width
        self.cell_height = cell_height
        self.depth = depth
        self.style = style

    @property
    def width(self):
        return max(len(line) for line in BLOCK_GLYPHS[self.character]) * self.cell_width

    def build(self):
        voxel_block(BLOCK_GLYPHS[self.character], self.cell_width, self.cell_height, self.depth, self.style)


class LetterRow:
    """Lays characters out left-to-right, centred on (center_x, center_y)."""

    def __init__(self, text, center_x, center_y, z, cell_width, cell_height, depth, gap, style, name_prefix):
        self.text = text
        self.center_x = center_x
        self.center_y = center_y
        self.z = z
        self.cell_width = cell_width
        self.cell_height = cell_height
        self.depth = depth
        self.gap = gap
        self.style = style
        self.name_prefix = name_prefix

    def make_letter(self, character, x, index):
        return BlockLetter(character, x, self.center_y, self.z, self.cell_width, self.cell_height,
                           self.depth, self.style, name=f"{self.name_prefix}{index}_{character}")

    def build_letters(self):
        widths = [max(len(line) for line in BLOCK_GLYPHS[character]) * self.cell_width for character in self.text]
        total_width = sum(widths) + self.gap * (len(widths) - 1)
        cursor = self.center_x - total_width / 2
        letters = []
        for index, (character, width) in enumerate(zip(self.text, widths)):
            letters.append(self.make_letter(character, cursor + width / 2, index))
            cursor += width + self.gap
        return letters

    def slot_after_last(self, character):
        """Where `character` would sit if appended to the row."""
        letters = self.build_letters()
        last = letters[-1]
        width = max(len(line) for line in BLOCK_GLYPHS[character]) * self.cell_width
        return last.x + last.width / 2 + self.gap + width / 2


def top_row():
    center_x, center_y = logo_point(512, 368)
    return LetterRow("PIXELOVE", center_x, center_y, z=0.0, cell_width=0.15, cell_height=0.215,
                     depth=0.4, gap=0.1, style=top_row_style(), name_prefix="top_")


def bottom_row():
    center_x, center_y = logo_point(507, 550)
    return LetterRow("OLE", center_x, center_y, z=0.15, cell_width=0.245, cell_height=0.245,
                     depth=0.5, gap=0.18, style=bottom_row_style(), name_prefix="bottom_")


def bottom_row_v(row):
    """Extra V in the OLE style (not in the original artwork); WordMorph
    places it when the lower row spells LOVE."""
    letter = row.make_letter("V", row.slot_after_last("V"), len(row.text))
    letter.name = "bottom_extra_V"
    return letter
