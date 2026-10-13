from lib.pixelove_ole.geometry import (Gradient, SurfaceStyle, additive_blending, bar, extrude_polygon, glow_segment,
                                       logo_length, logo_point, voxel_block)
from lib.pixelove_ole.glyphs import bold_caption_glyphs, text_rows
from lib.pixelove_ole.part import LogoPart


class Caption(LogoPart):
    """'GAMINGOWA IMPREZA!' banner: dark panel in a neon frame with raised
    voxel text, one object."""

    def __init__(self, x=None, y=None, z=0.3, words=("GAMINGOWA", "IMPREZA!"), depth=0.2):
        center_x, center_y = logo_point(515, 707)
        super().__init__("caption", center_x if x is None else x, center_y if y is None else y, z)
        self.words = words
        self.width = logo_length(620)
        self.height = logo_length(92)
        self.depth = depth
        self.text_height = logo_length(42)
        self.text_depth = 0.08
        self.letter_spacing = 2
        self.panel_style = SurfaceStyle(Gradient((0.0, (0.2, 0.08, 0.42)), (1.0, (0.05, 0.03, 0.18))),
                                        side_near=(0.15, 0.05, 0.3), side_far=(0.05, 0.02, 0.12))
        self.frame_top = (1.0, 0.35, 0.7)
        self.frame_bottom = (0.95, 0.2, 0.85)
        self.frame_sides = (0.75, 0.3, 1.0)
        self.word_styles = (
            SurfaceStyle(Gradient((0.0, (0.6, 1.0, 0.95)), (1.0, (0.2, 0.75, 1.0))),
                         side_near=(0.1, 0.35, 0.6), side_far=(0.03, 0.1, 0.25)),
            SurfaceStyle(Gradient((0.0, (1.0, 0.6, 0.85)), (1.0, (1.0, 0.2, 0.5))),
                         side_near=(0.55, 0.08, 0.3), side_far=(0.2, 0.02, 0.12)),
        )

    def frame_segments(self):
        left, right = -self.width / 2, self.width / 2
        top, bottom = self.height / 2, -self.height / 2
        return (((left, top), (right, top), self.frame_top),
                ((right, top), (right, bottom), self.frame_sides),
                ((right, bottom), (left, bottom), self.frame_bottom),
                ((left, bottom), (left, top), self.frame_sides))

    def build(self):
        half_width, half_height = self.width / 2, self.height / 2
        extrude_polygon(((-half_width, -half_height), (half_width, -half_height),
                         (half_width, half_height), (-half_width, half_height)), self.depth, self.panel_style)

        front = self.depth / 2
        for start, end, color in self.frame_segments():
            bar(start, end, 0.06, self.depth + 0.08, color)

        bold_glyphs = bold_caption_glyphs()
        word_bitmaps = [text_rows(word, bold_glyphs, spacing=self.letter_spacing) for word in self.words]
        cell_height = self.text_height / len(word_bitmaps[0])
        cell_width = cell_height * 0.68
        space = 3 * cell_width
        widths = [len(rows[0]) * cell_width for rows in word_bitmaps]
        cursor = -(sum(widths) + space * (len(widths) - 1)) / 2
        for rows, width, style in zip(word_bitmaps, widths, self.word_styles):
            voxel_block(rows, cell_width, cell_height, self.text_depth, style,
                        offset=(cursor + width / 2, 0.0, front + self.text_depth / 2))
            cursor += width + space

        with additive_blending():
            for start, end, color in self.frame_segments():
                glow_segment(start, end, front + 0.045, 0.35, color, alpha=0.45)
