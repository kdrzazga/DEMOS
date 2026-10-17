"""The drawn parts of the stronghold and how each one is lifted into 3D.

Coordinates are pixels of the scanned drawing (y grows downwards). Depths are
pixels too, positive towards the viewer. Every vertex keeps the image position
it had in the flat drawing and only gains depth, so the drawing itself is the
texture (a projective mapping) and the flat and 3D shapes line up exactly.
"""
import math

import numpy as np


def lerp(start, end, fraction):
    return start + (end - start) * fraction


class DrawnEdge:
    """A straight side outline the artist drew, given by its top and bottom points."""

    def __init__(self, top, bottom):
        self.top_x, self.top_y = top
        self.bottom_x, self.bottom_y = bottom

    def x_at(self, y):
        return lerp(self.top_x, self.bottom_x, (y - self.top_y) / (self.bottom_y - self.top_y))


class DrawnLine:
    """A polyline the artist drew left to right, as y along x."""

    def __init__(self, points):
        self.x, self.y = (np.array(values, np.float64) for values in zip(*points))

    def y_at(self, x):
        return np.interp(x, self.x, self.y)

    def covers(self, x):
        return (x >= self.x[0]) & (x <= self.x[-1])


class DrawnPiece:
    """A region of the drawing between two side edges, a bottom line and a
    crown (the top silhouette) that is found by probing pixel columns.

    ``crown_cap`` is a line the crown may not rise above - where a neighbour
    owns the drawing above it."""

    def __init__(self, name, left_edge, right_edge, crown_band, bottom_left_y, bottom_right_y, rows, highlight,
                 depth_fix, crown_cap):
        self.name = name
        self.depth_fix = depth_fix  # extra depth the 'small fix' stage moves the piece by
        self.left_edge = left_edge
        self.right_edge = right_edge
        self.crown_band = crown_band
        self.bottom_left_y = bottom_left_y
        self.bottom_right_y = bottom_right_y
        self.rows = rows
        self.highlight = highlight
        self.crown_cap = crown_cap
        self.probe_x = self.probe_top = self.crown_y = None
        self.pixel_x = self.pixel_y = self.left_x = self.right_x = None

    def column_fractions(self):
        raise NotImplementedError

    def detect(self, drawing):
        fractions = self.column_fractions()
        band_top, band_bottom = self.crown_band
        band_middle = (band_top + band_bottom) / 2
        self.probe_x = lerp(self.left_edge.x_at(band_middle), self.right_edge.x_at(band_middle), fractions)
        self.probe_top = np.full(len(fractions), float(band_top))
        self.crown_y = np.array([drawing.top_of_ink(x, band_top, band_bottom) for x in self.probe_x], np.float64)
        if self.crown_cap is not None:  # below the cap the neighbour's drawing ends: the crown is the cap
            capped = self.crown_cap.covers(self.probe_x)
            cap_y = self.crown_cap.y_at(self.probe_x[capped])
            self.crown_y[capped] = np.maximum(self.crown_y[capped], cap_y)
            self.probe_top[capped] = cap_y
        bottom_y = lerp(self.bottom_left_y, self.bottom_right_y, fractions)
        downwards = np.linspace(0.0, 1.0, self.rows + 1)[:, None]
        self.pixel_y = lerp(self.crown_y[None, :], bottom_y[None, :], downwards)
        self.left_x = self.left_edge.x_at(self.pixel_y)
        self.right_x = self.right_edge.x_at(self.pixel_y)
        self.pixel_x = lerp(self.left_x, self.right_x, fractions[None, :])

    def probes(self):
        """(x, start y, hit y) of every column probed for the crown."""
        return list(zip(self.probe_x, self.probe_top, self.crown_y))

    def footprint(self):
        crown = np.column_stack((self.pixel_x[0], self.pixel_y[0]))
        bottom = np.column_stack((self.pixel_x[-1], self.pixel_y[-1]))[::-1]
        return np.vstack((crown, bottom))

    def axis_line(self):
        return None

    def build(self, builder, paper_pixel):
        raise NotImplementedError


class Tower(DrawnPiece):
    """Becomes a cylinder: a column at fraction s across the drawn tower sits at
    angle asin(2s - 1), so seen from the front the texture is undistorted.

    A tower whose crown runs on over a neighbour drawn in front of it gets an
    ``annex``: the strip from its right edge to ``annex_right_x``, between the
    probed crown and ``annex_bottom`` (the neighbour's top line). The annex is
    flat, standing in the plane of the tower's axis, so it meets the cylinder's
    edge and moves with the tower; the tower's drawn outline becomes an L."""

    def __init__(self, name, left_edge, right_edge, crown_band, bottom_left_y, bottom_right_y, axis_depth,
                 highlight, depth_fix=0.0, annex_right_x=None, annex_bottom=None, segments=96, rows=32,
                 roof_segments=64, annex_columns=32, annex_rows=8, annex_lift=3.0):
        super().__init__(name, left_edge, right_edge, crown_band, bottom_left_y, bottom_right_y, rows, highlight,
                         depth_fix, None)
        self.axis_depth = axis_depth
        self.angles = np.linspace(-math.pi / 2, math.pi / 2, segments + 1)
        self.roof_segments = roof_segments
        self.annex_right_x = annex_right_x
        self.annex_bottom = annex_bottom
        self.annex_columns = annex_columns
        self.annex_rows = annex_rows
        self.annex_lift = annex_lift
        self.annex_x = self.annex_y = self.annex_probe_x = self.annex_crown_y = None

    def column_fractions(self):
        return (np.sin(self.angles) + 1.0) / 2.0

    def detect(self, drawing):
        super().detect(drawing)
        if self.annex_bottom is None:
            return
        band_top, band_bottom = self.crown_band
        band_middle = (band_top + band_bottom) / 2
        across = np.linspace(0.0, 1.0, self.annex_columns + 1)
        self.annex_probe_x = lerp(self.right_edge.x_at(band_middle), self.annex_right_x, across)
        self.annex_crown_y = np.array([drawing.top_of_ink(x, band_top, band_bottom) for x in self.annex_probe_x])
        downwards = np.linspace(0.0, 1.0, self.annex_rows + 1)[:, None]
        bottom_y = self.annex_bottom.y_at(self.annex_probe_x)
        self.annex_y = lerp(self.annex_crown_y[None, :], bottom_y[None, :], downwards)
        self.annex_x = lerp(self.right_edge.x_at(self.annex_y), self.annex_right_x, across[None, :])

    def probes(self):
        body = super().probes()
        if self.annex_bottom is None:
            return body
        band_top = float(self.crown_band[0])
        return body + [(x, band_top, y) for x, y in zip(self.annex_probe_x, self.annex_crown_y)]

    def footprint(self):
        if self.annex_bottom is None:
            return super().footprint()
        body_crown = np.column_stack((self.pixel_x[0], self.pixel_y[0]))
        annex_crown = np.column_stack((self.annex_x[0], self.annex_y[0]))
        annex_bottom = np.column_stack((self.annex_x[-1], self.annex_y[-1]))[::-1]
        body_bottom = np.column_stack((self.pixel_x[-1], self.pixel_y[-1]))[::-1]
        return np.vstack((body_crown, annex_crown, annex_bottom, body_bottom))

    def axis_line(self):
        top_y = float(self.crown_y.min())
        bottom_y = float(self.pixel_y[-1].mean())
        center_top = (self.left_edge.x_at(top_y) + self.right_edge.x_at(top_y)) / 2
        center_bottom = (self.left_edge.x_at(bottom_y) + self.right_edge.x_at(bottom_y)) / 2
        return (center_top, top_y), (center_bottom, bottom_y)

    def build(self, builder, paper_pixel):
        sine = np.sin(self.angles)[None, :]
        cosine = np.cos(self.angles)[None, :]
        radius = (self.right_x - self.left_x) / 2
        for side in (1.0, -1.0):  # front half, then back half (same texture, mirrored crown)
            depth = self.axis_depth + side * radius * cosine
            normal = np.stack(np.broadcast_arrays(sine, 0.0 * sine, side * cosine), axis=-1)
            builder.add_grid(self.pixel_x, self.pixel_y, depth, normal, self.pixel_x, self.pixel_y, self.highlight)
        self._build_roof(builder, paper_pixel)
        if self.annex_bottom is not None:
            self._build_annex(builder)

    def _build_annex(self, builder):
        """Flat in the axis plane at first; the 'small fix' rolls it onto the
        cylinder past the right edge, each column keeping its distance from
        that edge as arc length (slightly proud of the surface, against z-fighting)."""
        left = self.left_edge.x_at(self.annex_y)
        right = self.right_edge.x_at(self.annex_y)
        center = (left + right) / 2
        radius = (right - left) / 2 + self.annex_lift
        angle = math.pi / 2 + (self.annex_x - right) / radius
        wrapped_x = center + radius * np.sin(angle)
        wrapped_depth = radius * np.cos(angle)  # relative to the axis, where the flat annex stands
        wrapped_normal = np.stack((np.sin(angle), np.zeros_like(angle), np.cos(angle)), axis=-1)
        builder.add_grid(self.annex_x, self.annex_y, np.full(self.annex_x.shape, float(self.axis_depth)),
                         (0.0, 0.0, 1.0), self.annex_x, self.annex_y, self.highlight,
                         stretch=wrapped_x - self.annex_x, depth_shift=wrapped_depth, fixed_normal=wrapped_normal)

    def _build_roof(self, builder, paper_pixel):
        roof_y = float(self.crown_y.max())  # level of the lowest crenel notch
        left = self.left_edge.x_at(roof_y)
        right = self.right_edge.x_at(roof_y)
        center, radius = (left + right) / 2, (right - left) / 2
        around = np.linspace(0.0, 2 * math.pi, self.roof_segments + 1)[None, :]
        spoke = np.array([[0.0], [1.0]])
        pixel_x = center + spoke * radius * np.sin(around)
        depth = self.axis_depth + spoke * radius * np.cos(around)
        builder.add_grid(pixel_x, roof_y, depth, (0.0, 1.0, 0.0), *paper_pixel, self.highlight)


class Block(DrawnPiece):
    """Becomes a box: the drawn face stays the front, a back face, two sides
    and a walkway on top are extruded behind it."""

    def __init__(self, name, left_edge, right_edge, crown_band, bottom_left_y, bottom_right_y,
                 front_depth_left, front_depth_right, thickness, highlight, depth_fix=0.0, reach_fix=(0.0, 0.0),
                 crown_cap=None, columns=64, rows=24, side_strip=40):
        super().__init__(name, left_edge, right_edge, crown_band, bottom_left_y, bottom_right_y, rows, highlight,
                         depth_fix, crown_cap)
        self.reach_fix = reach_fix  # pixels the (left, right) ends reach further out in the 'small fix'
        self.front_depth_left = front_depth_left
        self.front_depth_right = front_depth_right
        self.thickness = thickness
        self.columns = columns
        self.side_strip = side_strip

    def column_fractions(self):
        return np.linspace(0.0, 1.0, self.columns + 1)

    def build(self, builder, paper_pixel):
        across_face = self.column_fractions()[None, :]
        front = np.broadcast_to(lerp(self.front_depth_left, self.front_depth_right, across_face), self.pixel_x.shape)
        back = front - self.thickness
        width = float(np.mean(self.right_x - self.left_x))
        facing = np.array([-(self.front_depth_right - self.front_depth_left) / width, 0.0, 1.0])
        facing /= np.linalg.norm(facing)
        reach_left, reach_right = self.reach_fix
        stretch = lerp(-reach_left, reach_right, across_face)
        builder.add_grid(self.pixel_x, self.pixel_y, front, facing, self.pixel_x, self.pixel_y, self.highlight,
                         stretch)
        builder.add_grid(self.pixel_x, self.pixel_y, back, -facing, self.pixel_x, self.pixel_y, self.highlight,
                         stretch)

        front_to_back = np.array([[0.0, 1.0]])
        for column, outward, strip in ((0, (-1.0, 0.0, 0.0), self.side_strip), (-1, (1.0, 0.0, 0.0), -self.side_strip)):
            edge_x, edge_y = self.pixel_x[:, [column]], self.pixel_y[:, [column]]
            depth = lerp(front[:, [column]], back[:, [column]], front_to_back)
            # sides borrow a strip of the face's own hatching next to the edge
            builder.add_grid(edge_x, edge_y, depth, outward, edge_x + strip * front_to_back, edge_y, self.highlight,
                             stretch[:, [column]])

        top_depth = lerp(front[0:1], back[0:1], front_to_back.T)
        builder.add_grid(self.pixel_x[0:1], self.pixel_y[0:1], top_depth, (0.0, 1.0, 0.0), *paper_pixel,
                         self.highlight, stretch)


def stronghold_rock_zone():
    """Outline of the rocky hill in the stronghold scan: along the tops of the
    rocks and the bases of the towers, down to the bottom of the page."""
    return np.array([
        (95, 1282), (45, 1185), (78, 1005), (238, 890), (360, 872), (527, 840), (760, 820), (1242, 835),
        (1255, 865), (1432, 695), (1713, 825), (1745, 875), (1755, 930), (1795, 960), (1880, 960),
        (1900, 1045), (1965, 1095), (1965, 1282),
    ], np.float64)


def stronghold_pieces(tower_color=(0.85, 0.18, 0.12), block_color=(0.12, 0.32, 0.85)):
    """Where the towers and walls are in the stronghold scan (2000 x 1282)."""
    # lower edge of the inner wall's top line: the left tower's crown (with the
    # door on top of the wall) runs on above it up to x=684
    inner_wall_top = DrawnLine([(552, 461), (560, 459), (584, 451), (600, 446), (640, 437), (664, 432),
                                (684, 428)])
    return [
        Tower("left tower", DrawnEdge((228, 335), (158, 940)), DrawnEdge((555, 335), (523, 940)),
              crown_band=(290, 420), bottom_left_y=940, bottom_right_y=845, axis_depth=-120, highlight=tower_color,
              depth_fix=100, annex_right_x=684, annex_bottom=inner_wall_top),
        Block("inner wall", DrawnEdge((556, 330), (528, 825)), DrawnEdge((748, 330), (748, 825)),
              crown_band=(290, 470), bottom_left_y=825, bottom_right_y=825,
              front_depth_left=-40, front_depth_right=-40, thickness=200, highlight=block_color,
              depth_fix=120, reach_fix=(50, 110), crown_cap=inner_wall_top),
        Tower("keep", DrawnEdge((754, 160), (758, 845)), DrawnEdge((1220, 200), (1242, 845)),
              crown_band=(100, 235), bottom_left_y=845, bottom_right_y=845, axis_depth=0, highlight=tower_color,
              depth_fix=-100),
        Block("outer wall", DrawnEdge((1232, 330), (1250, 870)), DrawnEdge((1410, 330), (1432, 700)),
              crown_band=(300, 470), bottom_left_y=870, bottom_right_y=700,
              front_depth_left=-60, front_depth_right=-230, thickness=110, highlight=block_color,
              reach_fix=(25, 50)),
        Tower("right tower", DrawnEdge((1420, 335), (1440, 700)), DrawnEdge((1683, 370), (1713, 830)),
              crown_band=(300, 425), bottom_left_y=700, bottom_right_y=830, axis_depth=-250,
              highlight=tower_color),
    ]
