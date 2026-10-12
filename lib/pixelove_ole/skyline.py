import random

from lib.pixelove_ole.geometry import additive_blending, bar, box, glow_segment, logo_length, logo_point
from lib.pixelove_ole.part import LogoPart


class Skyline(LogoPart):
    """Dark city silhouette standing in front of the sun's lower half,
    each roofline traced with a thin neon line."""

    def __init__(self, x=None, y=None, z=-1.7, width=None, min_height=None, max_height=None,
                 depth=0.25, seed=1985):
        base_x, base_y = logo_point(517, 285)
        super().__init__("skyline", base_x if x is None else x, base_y if y is None else y, z)
        self.width = width or logo_length(450)
        self.min_height = min_height or logo_length(14)
        self.max_height = max_height or logo_length(52)
        self.depth = depth
        self.seed = seed
        self.wall_color = (0.2, 0.04, 0.32)
        self.side_color = (0.1, 0.02, 0.2)
        self.roof_color = (1.0, 0.25, 0.75)
        self.window_color = (1.0, 0.8, 0.35)

    def buildings(self):
        """(left, right, height) tuples covering the whole width; taller towards the middle."""
        generator = random.Random(self.seed)
        result = []
        cursor = -self.width / 2
        while cursor < self.width / 2:
            building_width = generator.uniform(0.12, 0.38)
            right = min(cursor + building_width, self.width / 2)
            centre_weight = 1.0 - abs((cursor + right) / self.width)
            height = self.min_height + (self.max_height - self.min_height) * generator.random() * (0.4 + 0.6 * centre_weight)
            result.append((cursor, right, height))
            cursor = right
        return result

    def build(self):
        generator = random.Random(self.seed + 1)
        buildings = self.buildings()
        front = self.depth / 2
        for left, right, height in buildings:
            box(left, 0.0, -self.depth / 2, right, height, front, self.wall_color, self.side_color)
            for _ in range(int((right - left) * height * 60)):
                window_x = generator.uniform(left + 0.03, right - 0.05)
                window_y = generator.uniform(0.03, height - 0.06)
                box(window_x, window_y, front, window_x + 0.022, window_y + 0.03, front + 0.01,
                    self.window_color, self.window_color)
        roof_line = []
        for left, right, height in buildings:
            roof_line += [(left, height), (right, height)]
        for start, end in zip(roof_line, roof_line[1:]):
            bar(start, end, 0.018, 0.04, self.roof_color, z=front)
        with additive_blending():
            for start, end in zip(roof_line, roof_line[1:]):
                glow_segment(start, end, front, 0.14, self.roof_color, alpha=0.4)
