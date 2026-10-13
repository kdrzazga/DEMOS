"""Immediate-mode GL builders shared by every Pixelove Ole logo part.

All builders emit unlit, vertex-coloured geometry: a neon logo reads better
with hand-picked face/side shades than with fixed-function lighting. They are
meant to be called while a display list is being compiled (see LogoPart).
"""
import math
from contextlib import contextmanager

from OpenGL.GL import *

LOGO_IMAGE_SIZE = 1024
LOGO_PIXELS_PER_UNIT = 100.0


def logo_point(pixel_x, pixel_y):
    """Map a pixel of res/LOGO.png (1024x1024, y down) to world units
    (origin at the image centre, y up)."""
    half = LOGO_IMAGE_SIZE / 2
    return (pixel_x - half) / LOGO_PIXELS_PER_UNIT, (half - pixel_y) / LOGO_PIXELS_PER_UNIT


def logo_length(pixels):
    return pixels / LOGO_PIXELS_PER_UNIT


def shade(color, factor):
    return tuple(min(1.0, max(0.0, channel * factor)) for channel in color[:3])


def mix(first, second, amount):
    return tuple(a + (b - a) * amount for a, b in zip(first, second))


class Gradient:
    """Colour ramp over t in [0, 1]; t=0 is the top of a shape, t=1 the bottom."""

    def __init__(self, *stops):
        self.stops = tuple(sorted(stops))

    def at(self, t):
        t = min(1.0, max(0.0, t))
        previous_t, previous_color = self.stops[0]
        if t <= previous_t:
            return previous_color
        for stop_t, stop_color in self.stops[1:]:
            if t <= stop_t:
                span = (stop_t - previous_t) or 1.0
                return mix(previous_color, stop_color, (t - previous_t) / span)
            previous_t, previous_color = stop_t, stop_color
        return previous_color


def solid(color):
    return Gradient((0.0, color))


class SurfaceStyle:
    """Colours of an extruded shape: gradient front face, sides fading from
    side_near (front edge) to side_far (back edge), flat back, optional rim."""

    def __init__(self, face, side_near, side_far=None, back=None, edge=None, edge_width=2.0):
        self.face = face
        self.side_near = side_near
        self.side_far = side_far or shade(side_near, 0.45)
        self.back = back or self.side_far
        self.edge = edge
        self.edge_width = edge_width


# --------------------------------------------------------------------------
# 2D outlines
# --------------------------------------------------------------------------

def circle_points(center_x, center_y, radius, segments=32):
    return ellipse_points(center_x, center_y, radius, radius, 0.0, segments)


def ellipse_points(center_x, center_y, radius_x, radius_y, rotation_degrees=0.0, segments=32):
    rotation = math.radians(rotation_degrees)
    cos_r, sin_r = math.cos(rotation), math.sin(rotation)
    points = []
    for index in range(segments):
        angle = 2.0 * math.pi * index / segments
        local_x, local_y = radius_x * math.cos(angle), radius_y * math.sin(angle)
        points.append((center_x + local_x * cos_r - local_y * sin_r,
                       center_y + local_x * sin_r + local_y * cos_r))
    return points


def rounded_rect_points(center_x, center_y, width, height, radius, corner_segments=6):
    radius = min(radius, width / 2, height / 2)
    inner_x, inner_y = width / 2 - radius, height / 2 - radius
    corners = ((inner_x, inner_y, 0.0), (-inner_x, inner_y, 90.0),
               (-inner_x, -inner_y, 180.0), (inner_x, -inner_y, 270.0))
    points = []
    for corner_x, corner_y, start_degrees in corners:
        for step in range(corner_segments + 1):
            angle = math.radians(start_degrees + 90.0 * step / corner_segments)
            points.append((center_x + corner_x + radius * math.cos(angle),
                           center_y + corner_y + radius * math.sin(angle)))
    return points


def rotate_points(points, degrees, pivot=(0.0, 0.0)):
    angle = math.radians(degrees)
    cos_a, sin_a = math.cos(angle), math.sin(angle)
    pivot_x, pivot_y = pivot
    return [(pivot_x + (x - pivot_x) * cos_a - (y - pivot_y) * sin_a,
             pivot_y + (x - pivot_x) * sin_a + (y - pivot_y) * cos_a) for x, y in points]


def grow_points(points, margin):
    """Push a convex outline outwards from its centroid by `margin` units."""
    centroid_x = sum(x for x, _ in points) / len(points)
    centroid_y = sum(y for _, y in points) / len(points)
    grown = []
    for x, y in points:
        dx, dy = x - centroid_x, y - centroid_y
        length = math.hypot(dx, dy) or 1.0
        grown.append((x + dx / length * margin, y + dy / length * margin))
    return grown


def segment_quad(start, end, width):
    """Convex quad of the given width around the segment, ends extended by width/2
    so neighbouring segments of a polyline close their joints."""
    (x0, y0), (x1, y1) = start, end
    length = math.hypot(x1 - x0, y1 - y0) or 1.0
    along_x, along_y = (x1 - x0) / length, (y1 - y0) / length
    across_x, across_y = -along_y * width / 2, along_x * width / 2
    x0, y0 = x0 - along_x * width / 2, y0 - along_y * width / 2
    x1, y1 = x1 + along_x * width / 2, y1 + along_y * width / 2
    return [(x0 - across_x, y0 - across_y), (x1 - across_x, y1 - across_y),
            (x1 + across_x, y1 + across_y), (x0 + across_x, y0 + across_y)]


def _signed_area(points):
    return sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(points, points[1:] + points[:1])) / 2


# --------------------------------------------------------------------------
# Solid geometry
# --------------------------------------------------------------------------

def extrude_polygon(points, depth, style, z=0.0, gradient_span=None):
    """Extrude a convex 2D outline along z. `gradient_span` = (y_top, y_bottom)
    lets several pieces share one face gradient (e.g. the sunset bands)."""
    points = list(points)
    if _signed_area(points) < 0:
        points.reverse()
    front, back = z + depth / 2, z - depth / 2
    y_top, y_bottom = gradient_span or (max(y for _, y in points), min(y for _, y in points))
    span = (y_top - y_bottom) or 1.0

    glBegin(GL_POLYGON)
    for x, y in points:
        glColor3f(*style.face.at((y_top - y) / span))
        glVertex3f(x, y, front)
    glEnd()

    glColor3f(*style.back)
    glBegin(GL_POLYGON)
    for x, y in reversed(points):
        glVertex3f(x, y, back)
    glEnd()

    glBegin(GL_QUADS)
    for (x0, y0), (x1, y1) in zip(points, points[1:] + points[:1]):
        length = math.hypot(x1 - x0, y1 - y0) or 1.0
        upward = -(x1 - x0) / length  # outward normal y component for CCW outlines
        brightness = 0.75 + 0.3 * upward
        near, far = shade(style.side_near, brightness), shade(style.side_far, brightness)
        glColor3f(*near)
        glVertex3f(x0, y0, front)
        glColor3f(*far)
        glVertex3f(x0, y0, back)
        glVertex3f(x1, y1, back)
        glColor3f(*near)
        glVertex3f(x1, y1, front)
    glEnd()

    if style.edge:
        glLineWidth(style.edge_width)
        glColor3f(*style.edge)
        glBegin(GL_LINE_LOOP)
        for x, y in points:
            glVertex3f(x, y, front + 0.002)
        glEnd()


def bar(start, end, width, depth, color, z=0.0):
    """Neon tube core: a thin box between two points of the xy plane."""
    style = SurfaceStyle(solid(color), shade(color, 0.8), shade(color, 0.5))
    extrude_polygon(segment_quad(start, end, width), depth, style, z)


def box(x0, y0, z0, x1, y1, z1, top_color, side_color=None):
    side_color = side_color or shade(top_color, 0.7)
    left, right = min(x0, x1), max(x0, x1)
    bottom, top = min(y0, y1), max(y0, y1)
    back, front = min(z0, z1), max(z0, z1)
    faces = (
        (top_color, ((left, top, front), (right, top, front), (right, top, back), (left, top, back))),
        (shade(side_color, 1.1), ((left, bottom, front), (right, bottom, front), (right, top, front), (left, top, front))),
        (shade(side_color, 0.5), ((right, bottom, back), (left, bottom, back), (left, top, back), (right, top, back))),
        (side_color, ((right, bottom, front), (right, bottom, back), (right, top, back), (right, top, front))),
        (shade(side_color, 0.8), ((left, bottom, back), (left, bottom, front), (left, top, front), (left, top, back))),
        (shade(side_color, 0.4), ((left, bottom, back), (right, bottom, back), (right, bottom, front), (left, bottom, front))),
    )
    glBegin(GL_QUADS)
    for color, corners in faces:
        glColor3f(*color)
        for corner in corners:
            glVertex3f(*corner)
    glEnd()


def voxel_block(rows, cell_width, cell_height, depth, style, offset=(0.0, 0.0, 0.0)):
    """Extrude a bitmap ('#' = filled) into a block of voxels centred on `offset`.
    Only outer side faces are emitted, so a glyph reads as one solid piece."""
    filled = {(column, row) for row, line in enumerate(rows) for column, mark in enumerate(line) if mark == "#"}
    row_count = len(rows)
    column_count = max(len(line) for line in rows)
    offset_x, offset_y, offset_z = offset
    left = offset_x - column_count * cell_width / 2
    top = offset_y + row_count * cell_height / 2
    front, back = offset_z + depth / 2, offset_z - depth / 2

    def x_at(column):
        return left + column * cell_width

    def y_at(row):
        return top - row * cell_height

    glBegin(GL_QUADS)
    for column, row in filled:
        x0, x1 = x_at(column), x_at(column + 1)
        y_top, y_bottom = y_at(row), y_at(row + 1)
        color_top, color_bottom = style.face.at(row / row_count), style.face.at((row + 1) / row_count)

        glColor3f(*color_bottom)
        glVertex3f(x0, y_bottom, front)
        glVertex3f(x1, y_bottom, front)
        glColor3f(*color_top)
        glVertex3f(x1, y_top, front)
        glVertex3f(x0, y_top, front)

        glColor3f(*style.back)
        glVertex3f(x0, y_top, back)
        glVertex3f(x1, y_top, back)
        glVertex3f(x1, y_bottom, back)
        glVertex3f(x0, y_bottom, back)

        sides = (
            ((column - 1, row), 0.8, ((x0, y_bottom), (x0, y_top))),
            ((column + 1, row), 0.65, ((x1, y_top), (x1, y_bottom))),
            ((column, row - 1), 1.3, ((x0, y_top), (x1, y_top))),
            ((column, row + 1), 0.45, ((x1, y_bottom), (x0, y_bottom))),
        )
        for neighbour, brightness, ((ax, ay), (bx, by)) in sides:
            if neighbour in filled:
                continue
            near, far = shade(style.side_near, brightness), shade(style.side_far, brightness)
            glColor3f(*near)
            glVertex3f(ax, ay, front)
            glVertex3f(bx, by, front)
            glColor3f(*far)
            glVertex3f(bx, by, back)
            glVertex3f(ax, ay, back)
    glEnd()

    if style.edge:
        glLineWidth(style.edge_width)
        glColor3f(*style.edge)
        glBegin(GL_LINES)
        lifted = front + 0.003
        for column, row in filled:
            x0, x1 = x_at(column), x_at(column + 1)
            y_top, y_bottom = y_at(row), y_at(row + 1)
            outline = (
                ((column - 1, row), (x0, y_bottom), (x0, y_top)),
                ((column + 1, row), (x1, y_bottom), (x1, y_top)),
                ((column, row - 1), (x0, y_top), (x1, y_top)),
                ((column, row + 1), (x0, y_bottom), (x1, y_bottom)),
            )
            for neighbour, (ax, ay), (bx, by) in outline:
                if neighbour not in filled:
                    glVertex3f(ax, ay, lifted)
                    glVertex3f(bx, by, lifted)
        glEnd()


# --------------------------------------------------------------------------
# Additive glow
# --------------------------------------------------------------------------

@contextmanager
def additive_blending():
    """Additive glow that still honours the part's fade: colours are
    premultiplied by their alpha and scaled by the GL constant alpha, which
    LogoPart.draw() sets from its opacity. Restores the previous blend state."""
    glPushAttrib(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glEnable(GL_BLEND)
    glBlendFunc(GL_CONSTANT_ALPHA, GL_ONE)
    glDepthMask(GL_FALSE)
    try:
        yield
    finally:
        glPopAttrib()


def glow_segment(start, end, z, width, color, alpha=0.45):
    """Soft halo around a segment; call inside additive_blending()."""
    (x0, y0), (x1, y1) = start, end
    length = math.hypot(x1 - x0, y1 - y0) or 1.0
    across_x, across_y = -(y1 - y0) / length * width / 2, (x1 - x0) / length * width / 2
    glBegin(GL_QUADS)
    for direction in (1.0, -1.0):
        glColor3f(*shade(color, alpha))
        glVertex3f(x0, y0, z)
        glVertex3f(x1, y1, z)
        glColor3f(0.0, 0.0, 0.0)
        glVertex3f(x1 + across_x * direction, y1 + across_y * direction, z)
        glVertex3f(x0 + across_x * direction, y0 + across_y * direction, z)
    glEnd()


def glow_disc(center_x, center_y, z, radius, color, alpha=0.4, segments=40):
    """Radial halo; call inside additive_blending()."""
    glBegin(GL_TRIANGLE_FAN)
    glColor3f(*shade(color, alpha))
    glVertex3f(center_x, center_y, z)
    glColor3f(0.0, 0.0, 0.0)
    for index in range(segments + 1):
        angle = 2.0 * math.pi * index / segments
        glVertex3f(center_x + radius * math.cos(angle), center_y + radius * math.sin(angle), z)
    glEnd()
