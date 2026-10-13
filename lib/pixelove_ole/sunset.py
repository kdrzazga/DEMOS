import math

from OpenGL.GL import *

from lib.pixelove_ole.geometry import (Gradient, SurfaceStyle, additive_blending, extrude_polygon, glow_disc,
                                       logo_length, logo_point)
from lib.pixelove_ole.part import LogoPart


class Sunset(LogoPart):
    """Retro striped sun: the disc above the horizon cut into horizontal slabs
    whose gaps widen towards the bottom, all sharing one yellow->red gradient."""

    def __init__(self, x=None, y=None, z=-2.0, radius=None, depth=0.18, horizon=None, gaps=None):
        center_x, center_y = logo_point(512, 300)
        super().__init__("sunset", center_x if x is None else x, center_y if y is None else y, z)
        self.radius = radius or logo_length(172)
        self.depth = depth
        # Local y of the lowest visible slab (the skyline covers the rest).
        self.horizon = logo_length(15) if horizon is None else horizon
        # (gap centre, gap height) in local units, top to bottom.
        self.gaps = gaps or tuple((logo_length(300 - pixel_y), logo_length(thickness))
                                  for pixel_y, thickness in ((180, 3), (196, 4), (212, 5),
                                                             (228, 6), (244, 7), (260, 8), (276, 9)))
        self.style = SurfaceStyle(Gradient((0.0, (1.0, 0.92, 0.25)),
                                           (0.45, (1.0, 0.6, 0.12)),
                                           (1.0, (0.95, 0.18, 0.35))),
                                  side_near=(0.9, 0.3, 0.15), side_far=(0.45, 0.05, 0.1))
        self.halo_color = (1.0, 0.45, 0.2)

    def slab_bounds(self):
        bounds = []
        upper = self.radius
        for gap_center, gap_height in self.gaps:
            lower = gap_center + gap_height / 2
            if lower < upper:
                bounds.append((upper, max(lower, self.horizon)))
            upper = gap_center - gap_height / 2
            if upper <= self.horizon:
                return bounds
        bounds.append((upper, self.horizon))
        return bounds

    def slab_outline(self, upper, lower, steps=10):
        """Convex region of the disc between two horizontal lines."""
        right_side, left_side = [], []
        for index in range(steps + 1):
            y = lower + (upper - lower) * index / steps
            half_width = math.sqrt(max(self.radius ** 2 - y ** 2, 0.0))
            right_side.append((half_width, y))
            left_side.append((-half_width, y))
        return right_side + list(reversed(left_side))

    def build(self):
        span = (self.radius, self.horizon)
        for upper, lower in self.slab_bounds():
            extrude_polygon(self.slab_outline(upper, lower), self.depth, self.style, gradient_span=span)
        with additive_blending():
            glow_disc(0.0, self.radius * 0.35, -self.depth, self.radius * 1.7, self.halo_color, alpha=0.35)
