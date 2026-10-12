from lib.pixelove_ole.geometry import (Gradient, SurfaceStyle, additive_blending, bar, extrude_polygon, glow_disc,
                                       glow_segment, logo_length, logo_point, solid, voxel_block)
from lib.pixelove_ole.glyphs import PIXEL_PLUS, PIXEL_SQUARE
from lib.pixelove_ole.part import LogoPart

ORANGE = (1.0, 0.5, 0.15)
RED = (1.0, 0.25, 0.3)
PINK = (1.0, 0.45, 0.8)
MAGENTA = (0.9, 0.25, 1.0)
PURPLE = (0.6, 0.3, 0.95)
BLUE = (0.35, 0.6, 1.0)
CYAN = (0.35, 0.95, 1.0)
GREEN = (0.4, 1.0, 0.5)
YELLOW = (1.0, 0.9, 0.3)


class Details(LogoPart):
    """Everything else: the double neon triangle, the box framing PIXELOVE,
    the rainbow comet, the twinkle star, pixel 'clouds' around the skyline and
    the confetti of floating pixel squares and plus signs.

    Built in absolute logo coordinates, so the part sits at the origin."""

    def __init__(self, x=0.0, y=0.0, z=0.0):
        super().__init__("details", x, y, z)
        self.triangle_z = -2.6
        self.frame_z = -0.5
        # (pixel_x, pixel_y, z, kind, colour, pixel cell size)
        self.sparkles = (
            (252, 148, -1.2, "plus", ORANGE, 6), (155, 208, -1.0, "square", ORANGE, 12),
            (200, 172, -1.3, "plus", BLUE, 5), (350, 135, -1.4, "square", ORANGE, 11),
            (385, 115, -1.5, "square", PINK, 7), (622, 100, -1.5, "square", PINK, 6),
            (680, 138, -1.2, "square", ORANGE, 14), (792, 148, -1.1, "square", BLUE, 6),
            (120, 305, -0.8, "square", BLUE, 8), (68, 350, -0.6, "square", PURPLE, 10),
            (88, 382, -0.4, "plus", RED, 8), (85, 456, -0.3, "plus", BLUE, 6),
            (105, 495, 0.2, "square", MAGENTA, 10), (212, 450, 0.3, "plus", RED, 5),
            (60, 548, -0.5, "square", PINK, 7), (938, 385, -0.4, "plus", GREEN, 8),
            (958, 315, -0.9, "square", PURPLE, 8), (942, 456, 0.0, "square", MAGENTA, 11),
            (928, 500, 0.2, "plus", PINK, 6), (905, 540, 0.4, "plus", RED, 7),
            (962, 600, 0.2, "square", BLUE, 6), (865, 652, 0.5, "plus", ORANGE, 7),
            (910, 680, 0.3, "square", BLUE, 7), (182, 692, 0.6, "square", PINK, 10),
            (545, 463, 0.0, "square", MAGENTA, 7), (547, 507, 0.1, "square", PINK, 8),
            (790, 612, 0.5, "square", MAGENTA, 6), (380, 815, 0.8, "square", YELLOW, 8),
            (398, 823, 0.9, "plus", PINK, 5), (660, 796, 0.8, "plus", RED, 7),
            (628, 832, 0.9, "plus", RED, 6), (702, 788, 0.7, "square", PINK, 6),
            (250, 790, 0.5, "square", PURPLE, 6), (840, 760, 0.6, "square", MAGENTA, 6),
            (465, 95, -1.6, "square", BLUE, 5), (905, 215, -1.0, "square", PINK, 6),
        )
        # Purple/pink pixel staircases around the skyline: (pixel_x, pixel_y, z, rows, colour, cell size)
        self.pixel_clouds = (
            (183, 247, -1.5, ("..##", ".###", "####", "#..."), PURPLE, 9),
            (312, 255, -1.5, ("##..", "####", ".###"), PURPLE, 9),
            (720, 248, -1.5, ("...##", "..###", "#####", "##..."), PURPLE, 9),
            (788, 212, -1.3, (".##.", "####", "##.#"), PINK, 10),
            (852, 203, -1.3, ("###", "###", ".##"), PINK, 11),
        )

    def neon_polyline(self, points, z, width, color, closed=True, glow_width=0.4):
        segments = list(zip(points, points[1:] + (points[:1] if closed else [])))
        for start, end in segments:
            bar(start, end, width, width, color, z)
        return [(start, end, z, glow_width, color) for start, end in segments]

    def triangle(self, inset):
        top_left, top_right, bottom = logo_point(48, 265), logo_point(978, 265), logo_point(512, 890)
        center_x = (top_left[0] + top_right[0] + bottom[0]) / 3
        center_y = (top_left[1] + top_right[1] + bottom[1]) / 3
        return [(x + (center_x - x) * inset, y + (center_y - y) * inset) for x, y in (top_left, top_right, bottom)]

    def pixelove_frame(self):
        return [logo_point(130, 445), logo_point(130, 290), logo_point(898, 290), logo_point(898, 445)]

    def comet(self):
        """Rainbow streak: one tapering band per colour, head at the upper right."""
        tail, head = logo_point(222, 252), logo_point(356, 176)
        colors = (YELLOW, ORANGE, RED, MAGENTA, BLUE)
        band = logo_length(7)
        for index, color in enumerate(colors):
            offset = (index - (len(colors) - 1) / 2) * band
            band_tail = (tail[0] + offset * 0.4, tail[1] + offset * 1.6)
            band_head_a = (head[0], head[1] + offset * 0.5)
            band_head_b = (head[0], head[1] + offset * 0.5 - band * 0.5)
            extrude_polygon((band_tail, band_head_b, band_head_a), 0.05, SurfaceStyle(solid(color), color), z=-1.0)
        return head

    def twinkle(self, center, size, z, color):
        center_x, center_y = center
        thin = size * 0.12
        style = SurfaceStyle(Gradient((0.0, (1.0, 1.0, 1.0)), (1.0, color)), color)
        extrude_polygon(((center_x, center_y + size), (center_x - thin, center_y), (center_x, center_y - size),
                         (center_x + thin, center_y)), 0.04, style, z)
        extrude_polygon(((center_x - size, center_y), (center_x, center_y - thin), (center_x + size, center_y),
                         (center_x, center_y + thin)), 0.04, style, z)

    def build(self):
        glows = []
        glows += self.neon_polyline(self.triangle(0.0), self.triangle_z, 0.05, (1.0, 0.3, 0.75), glow_width=0.5)
        glows += self.neon_polyline(self.triangle(0.045), self.triangle_z + 0.05, 0.035, (0.4, 0.85, 1.0))
        glows += self.neon_polyline(self.pixelove_frame(), self.frame_z, 0.05, (1.0, 0.3, 0.7), closed=False)

        comet_head = self.comet()
        star = logo_point(722, 175)
        self.twinkle(star, logo_length(42), -1.2, YELLOW)

        for pixel_x, pixel_y, z, rows, color, cell_pixels in self.pixel_clouds:
            cell = logo_length(cell_pixels)
            style = SurfaceStyle(Gradient((0.0, color), (1.0, tuple(c * 0.7 for c in color))), tuple(c * 0.5 for c in color))
            x, y = logo_point(pixel_x, pixel_y)
            voxel_block(rows, cell, cell, cell, style, offset=(x, y, z))

        for pixel_x, pixel_y, z, kind, color, cell_pixels in self.sparkles:
            cell = logo_length(cell_pixels) / (3 if kind == "plus" else 1)
            rows = PIXEL_PLUS if kind == "plus" else PIXEL_SQUARE
            style = SurfaceStyle(Gradient((0.0, (1.0, 1.0, 1.0)), (0.4, color), (1.0, color)), tuple(c * 0.6 for c in color))
            x, y = logo_point(pixel_x, pixel_y)
            voxel_block(rows, cell, cell, cell, style, offset=(x, y, z))

        with additive_blending():
            for start, end, z, width, color in glows:
                glow_segment(start, end, z, width, color, alpha=0.5)
            glow_disc(*star, -1.25, logo_length(70), YELLOW, alpha=0.5)
            glow_disc(*comet_head, -1.05, logo_length(45), (1.0, 0.6, 0.9), alpha=0.35)
            for pixel_x, pixel_y, z, _, color, cell_pixels in self.sparkles:
                glow_disc(*logo_point(pixel_x, pixel_y), z - 0.02, logo_length(cell_pixels * 2.2), color, alpha=0.3,
                          segments=16)
