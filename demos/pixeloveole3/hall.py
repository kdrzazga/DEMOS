"""3D model of the library's entrance hall (models/hall.jpg), empty: no
people, furniture, stands, posters or pictures, just the architecture.

Metres, y up. The foyer spans x -4..4 and z +1..-7 with the street entrance
in its front wall (z = +1). Its back wall (z -7..-7.5) has the pillar on the
left and, right of it, the wide opening into the hall proper (x -3.5..4,
z -7.5..-16), which has spotlights washing its back wall.
"""
import math

import pygame
from OpenGL.GL import *


class HallPalette:
    def __init__(self):
        self.wall = (0.92, 0.88, 0.80)
        self.hall_wall = (0.95, 0.90, 0.78)
        self.ceiling = (0.96, 0.95, 0.92)
        self.cornice = (0.97, 0.95, 0.90)
        self.skirting = (0.42, 0.27, 0.15)
        self.door = (0.33, 0.20, 0.12)
        self.door_panel = (0.38, 0.24, 0.15)
        self.casing = (0.95, 0.94, 0.91)
        self.window_frame = (0.96, 0.96, 0.94)
        self.daylight_glass = (0.80, 0.88, 0.94)
        self.dark_glass = (0.22, 0.27, 0.30)
        self.aluminium = (0.72, 0.73, 0.74)
        self.handle = (0.75, 0.70, 0.55)
        self.radiator = (0.94, 0.94, 0.92)
        self.dark_room = (0.12, 0.10, 0.09)
        self.street_daylight = (0.93, 0.95, 0.98)
        self.spotlight = (0.25, 0.25, 0.27)
        self.lamp_glow = (1.0, 0.82, 0.55)
        self.floor_cream = (228, 208, 168)
        self.floor_tan = (196, 148, 88)
        self.floor_dot = (38, 32, 28)
        self.floor_grout = (170, 150, 120)


def floor_tiles_surface(palette, size=128):
    """One repeat of the floor: tan and cream squares laid diagonally, small
    black squares where four tiles meet."""
    surface = pygame.Surface((size, size), pygame.SRCALPHA)
    surface.fill((*palette.floor_cream, 255))
    half = size // 2
    diamond = ((half, 0), (size, half), (half, size), (0, half))
    pygame.draw.polygon(surface, (*palette.floor_tan, 255), diamond)
    pygame.draw.polygon(surface, (*palette.floor_grout, 255), diamond, 2)
    dot = size // 10
    for center_x, center_y in ((half, 0), (size, half), (half, size), (0, half)):
        pygame.draw.polygon(surface, (*palette.floor_dot, 255),
                            ((center_x, center_y - dot), (center_x + dot, center_y),
                             (center_x, center_y + dot), (center_x - dot, center_y)))
    return surface


class Opening:
    """A hole in a wall, in the wall's local coordinates (`start`..`end`
    along it, `bottom`..`top` up). `kind`: 'window', 'door', 'glass_door',
    'passage' (open) or 'dark_doorway' (opening onto an unlit room)."""

    def __init__(self, start, end, bottom, top, kind):
        self.start = start
        self.end = end
        self.bottom = bottom
        self.top = top
        self.kind = kind

    @property
    def reaches_floor(self):
        return self.bottom <= 0.0


class Wall:
    """Straight wall drawn in its own frame: it runs along local +x from
    (x, z) for `length`, its room-side face at local z = 0, its thickness
    behind it (local -z). `yaw` turns it into place (90: runs towards -z
    with the room on +x; -90: towards +z with the room on -x; 180: towards
    -x with the room on -z)."""

    def __init__(self, x, z, yaw, length, height, color, palette, thickness=0.5, openings=(), arched_windows=(),
                 skirting_height=0.15, cornice_height=0.22):
        self.x = x
        self.z = z
        self.yaw = yaw
        self.length = length
        self.height = height
        self.color = color
        self.palette = palette
        self.thickness = thickness
        self.openings = tuple(sorted(openings, key=lambda opening: opening.start))
        self.arched_windows = arched_windows
        self.skirting_height = skirting_height
        self.cornice_height = cornice_height

    def draw(self, shapes):
        with shapes.frame(self.x, 0.0, self.z, self.yaw):
            self._draw_masonry(shapes)
            self._draw_skirting(shapes)
            shapes.box(0.0, self.height - self.cornice_height, 0.0, self.length, self.height, 0.12,
                       self.palette.cornice)
            for opening in self.openings:
                self._draw_opening(shapes, opening)
            for center, width, sill, spring in self.arched_windows:
                self._draw_arched_window(shapes, center, width, sill, spring)

    def _draw_masonry(self, shapes):
        back = -self.thickness
        cursor = 0.0
        for opening in self.openings:
            if opening.start > cursor:
                shapes.box(cursor, 0.0, back, opening.start, self.height, 0.0, self.color)
            shapes.box(opening.start, opening.top, back, opening.end, self.height, 0.0, self.color)
            if not opening.reaches_floor:
                shapes.box(opening.start, 0.0, back, opening.end, opening.bottom, 0.0, self.color)
            cursor = opening.end
        if cursor < self.length:
            shapes.box(cursor, 0.0, back, self.length, self.height, 0.0, self.color)

    def _draw_skirting(self, shapes):
        cursor = 0.0
        for opening in self.openings:
            if opening.reaches_floor:
                if opening.start > cursor:
                    shapes.box(cursor, 0.0, 0.0, opening.start, self.skirting_height, 0.03, self.palette.skirting)
                cursor = opening.end
        if cursor < self.length:
            shapes.box(cursor, 0.0, 0.0, self.length, self.skirting_height, 0.03, self.palette.skirting)

    def _draw_opening(self, shapes, opening):
        if opening.kind == "window":
            self._draw_window(shapes, opening)
        elif opening.kind == "door":
            self._draw_door(shapes, opening)
        elif opening.kind == "open_door":
            self._draw_open_door(shapes, opening)
        elif opening.kind == "glass_door":
            self._draw_glass_door(shapes, opening)
        elif opening.kind == "dark_doorway":
            shapes.box(opening.start, 0.0, -self.thickness - 0.05, opening.end, opening.top, -self.thickness,
                       self.palette.dark_room)
            self._draw_casing(shapes, opening)

    def _draw_window(self, shapes, opening):
        palette = self.palette
        glass_z = -self.thickness + 0.1
        start, end, bottom, top = opening.start, opening.end, opening.bottom, opening.top
        shapes.box(start, bottom, glass_z - 0.02, end, top, glass_z, palette.daylight_glass)
        bar = 0.07
        middle_x, transom_y = (start + end) / 2.0, top - (top - bottom) * 0.28
        for x0, y0, x1, y1 in ((start, bottom, start + bar, top), (end - bar, bottom, end, top),
                               (start, top - bar, end, top), (start, bottom, end, bottom + bar),
                               (middle_x - bar / 2, bottom, middle_x + bar / 2, transom_y),
                               (start, transom_y - bar / 2, end, transom_y + bar / 2)):
            shapes.box(x0, y0, glass_z, x1, y1, glass_z + 0.06, palette.window_frame)
        shapes.box(start - 0.05, bottom - 0.05, -0.02, end + 0.05, bottom, 0.12, palette.window_frame)

    def _draw_casing(self, shapes, opening):
        width = 0.12
        start, end, top = opening.start, opening.end, opening.top
        for x0, y0, x1, y1 in ((start - width, 0.0, start, top + width), (end, 0.0, end + width, top + width),
                               (start - width, top, end + width, top + width)):
            shapes.box(x0, y0, 0.0, x1, y1, 0.03, self.palette.casing)

    def _draw_door(self, shapes, opening):
        palette = self.palette
        start, end, top = opening.start, opening.end, opening.top
        leaf_z = -0.08
        shapes.box(start, 0.0, leaf_z - 0.05, end, top, leaf_z, palette.door)
        leaves = 2 if end - start > 1.4 else 1
        leaf_width = (end - start) / leaves
        for leaf in range(leaves):
            left = start + leaf * leaf_width
            for panel_bottom, panel_top in ((0.25, top * 0.45), (top * 0.5, top - 0.2)):
                shapes.box(left + 0.15, panel_bottom, leaf_z, left + leaf_width - 0.15, panel_top, leaf_z + 0.02,
                           palette.door_panel)
            handle_x = left + (leaf_width - 0.12 if leaf == 0 else 0.12)
            shapes.sphere(handle_x, 1.05, leaf_z + 0.05, 0.035, palette.handle)
        if leaves == 2:
            middle = (start + end) / 2.0
            shapes.box(middle - 0.01, 0.0, leaf_z, middle + 0.01, top, leaf_z + 0.025, palette.skirting)
        self._draw_casing(shapes, opening)

    def _draw_open_door(self, shapes, opening):
        palette = self.palette
        start, end, top = opening.start, opening.end, opening.top
        leaf_width = (end - start) / 2.0
        outside = -self.thickness - 1.0
        shapes.box(start - 0.4, 0.0, outside - 0.2, end + 0.4, top + 0.4, outside, palette.street_daylight)
        for hinge, side in ((start, 1.0), (end, -1.0)):
            inner = hinge + side * 0.05
            shapes.box(min(hinge, inner), 0.0, 0.02, max(hinge, inner), top, leaf_width, palette.door)
            for panel_bottom, panel_top in ((0.25, top * 0.45), (top * 0.5, top - 0.2)):
                face = inner + side * 0.02
                shapes.box(min(inner, face), panel_bottom, 0.17, max(inner, face), panel_top, leaf_width - 0.15,
                           palette.door_panel)
        self._draw_casing(shapes, opening)

    def _draw_glass_door(self, shapes, opening):
        palette = self.palette
        start, end, top = opening.start, opening.end, opening.top
        glass_z = -self.thickness / 2.0
        shapes.box(start, 0.0, glass_z - 0.02, end, top, glass_z, palette.dark_glass)
        bar = 0.08
        middle = (start + end) / 2.0
        for x0, y0, x1, y1 in ((start, 0.0, start + bar, top), (end - bar, 0.0, end, top),
                               (start, top - bar, end, top), (start, 0.0, end, 0.18),
                               (middle - bar / 2, 0.0, middle + bar / 2, top), (start, 1.0, end, 1.0 + bar)):
            shapes.box(x0, y0, glass_z, x1, y1, glass_z + 0.06, palette.aluminium)
        self._draw_casing(shapes, opening)

    def _draw_arched_window(self, shapes, center, width, sill, spring, segments=16):
        """Window set into the wall face: a rectangle up to `spring` with a
        semicircular head."""
        palette = self.palette
        half = width / 2.0
        glass_z, frame_z = 0.01, 0.03
        shapes.polygon(((center - half, sill, glass_z), (center + half, sill, glass_z),
                        (center + half, spring, glass_z), (center - half, spring, glass_z)),
                       palette.daylight_glass, (0.0, 0.0, 1.0))
        arc = [(center + half * math.cos(math.pi * index / segments), spring + half * math.sin(math.pi * index / segments),
                glass_z) for index in range(segments + 1)]
        shapes.fan((center, spring, glass_z), arc, (0.0, 0.0, 1.0), palette.daylight_glass)
        bar = 0.07
        for x0, y0, x1, y1 in ((center - half, sill, center - half + bar, spring),
                               (center + half - bar, sill, center + half, spring),
                               (center - bar / 2, sill, center + bar / 2, spring + half),
                               (center - half, spring - bar / 2, center + half, spring + bar / 2)):
            shapes.box(x0, y0, glass_z, x1, y1, frame_z + 0.03, palette.window_frame)
        for start, end in zip(arc, arc[1:]):
            shapes.beam((start[0], start[1], frame_z), (end[0], end[1], frame_z), bar, palette.window_frame)
        shapes.box(center - half - 0.08, sill - 0.06, 0.0, center + half + 0.08, sill, 0.14, palette.window_frame)


class Radiator:
    def __init__(self, x, z, yaw, width, palette, height=0.6, lift=0.15, fins=14):
        self.x = x
        self.z = z
        self.yaw = yaw
        self.width = width
        self.palette = palette
        self.height = height
        self.lift = lift
        self.fins = fins

    def draw(self, shapes):
        with shapes.frame(self.x, 0.0, self.z, self.yaw):
            pitch = self.width / self.fins
            for fin in range(self.fins):
                left = -self.width / 2.0 + fin * pitch
                shapes.box(left + 0.01, self.lift, 0.04, left + pitch - 0.01, self.lift + self.height, 0.16,
                           self.palette.radiator)
            shapes.box(-self.width / 2.0, self.lift + 0.05, 0.06, self.width / 2.0, self.lift + self.height - 0.05,
                       0.14, self.palette.radiator)


class Spotlight:
    """Ceiling spot aimed at the wall it hangs in front of; its warm wash is
    drawn separately (additively) by draw_glow."""

    def __init__(self, x, ceiling, z, palette, wall_z, glow_height=1.6, glow_width=1.3):
        self.x = x
        self.ceiling = ceiling
        self.z = z
        self.palette = palette
        self.wall_z = wall_z
        self.glow_height = glow_height
        self.glow_width = glow_width

    def draw(self, shapes):
        shapes.cylinder(self.x, self.ceiling - 0.12, self.z, 0.02, 0.02, 0.12, self.palette.spotlight, 6)
        shapes.cylinder(self.x, self.ceiling - 0.3, self.z, 0.07, 0.06, 0.18, self.palette.spotlight, 10)

    def draw_glow(self):
        top = self.ceiling - 0.25
        z = self.wall_z + 0.02
        glBegin(GL_TRIANGLE_FAN)
        glColor4f(*self.palette.lamp_glow, 0.55)
        glVertex3f(self.x, top, z)
        glColor4f(*self.palette.lamp_glow, 0.0)
        segments = 12
        for index in range(segments + 1):
            angle = math.pi * (1.0 + index / segments)
            glVertex3f(self.x + self.glow_width * 0.5 * math.cos(angle),
                       top + self.glow_height * math.sin(angle), z)
        glEnd()


class Hall:
    def __init__(self, floor_texture, palette=None, foyer_height=4.2, hall_height=3.9):
        self.palette = palette or HallPalette()
        self.floor_texture = floor_texture
        self.foyer_height = foyer_height
        self.hall_height = hall_height
        self.tile_repeat = 0.9
        self.foyer = (-4.0, 4.0, -7.0, 1.0)
        self.hall = (-3.5, 4.0, -16.0, -7.5)
        self.walls = self._create_walls()
        self.pillar = (-1.75, -1.05, -6.3)
        self.radiators = (Radiator(-4.0, -1.0, 90.0, 1.2, self.palette), Radiator(-4.0, -4.0, 90.0, 1.2, self.palette))
        self.spotlights = tuple(Spotlight(x, hall_height, -15.3, self.palette, -16.0)
                                for x in (-2.4, -1.0, 0.4, 1.8, 3.2))

    def _create_walls(self):
        palette = self.palette
        foyer_height, hall_height = self.foyer_height, self.hall_height
        return (
            # Foyer: street entrance (front), windows (left), door (right), opening into the hall (back).
            Wall(4.0, 1.0, 180.0, 8.0, foyer_height, palette.wall, palette,
                 openings=(Opening(3.1, 4.9, 0.0, 3.0, "door"),)),
            Wall(-4.0, 1.0, 90.0, 8.0, foyer_height, palette.wall, palette, thickness=0.6,
                 openings=(Opening(1.35, 2.65, 0.9, 3.4, "window"), Opening(4.35, 5.65, 0.9, 3.4, "window"))),
            Wall(4.0, -7.0, -90.0, 8.0, foyer_height, palette.wall, palette,
                 openings=(Opening(3.85, 4.95, 0.0, 2.5, "door"),)),
            Wall(-4.0, -7.0, 0.0, 8.0, foyer_height, palette.wall, palette,
                 openings=(Opening(3.0, 6.8, 0.0, 3.4, "passage"),)),
            # Hall proper: two entrance doors (left), glass door and a dark doorway (back).
            Wall(-3.5, -7.5, 90.0, 8.5, hall_height, palette.hall_wall, palette,
                 openings=(Opening(1.2, 2.8, 0.0, 2.8, "open_door"), Opening(5.0, 6.6, 0.0, 2.8, "door"))),
            Wall(4.0, -16.0, -90.0, 8.5, hall_height, palette.hall_wall, palette),
            Wall(-3.5, -16.0, 0.0, 7.5, hall_height, palette.hall_wall, palette,
                 openings=(Opening(3.1, 4.7, 0.0, 2.6, "glass_door"), Opening(5.9, 6.9, 0.0, 2.4, "dark_doorway"))),
        )

    def _draw_floor(self, shapes, left, right, back, front):
        corners = ((left, 0.0, front), (right, 0.0, front), (right, 0.0, back), (left, 0.0, back))
        uvs = [(x / self.tile_repeat, z / self.tile_repeat) for x, _, z in corners]
        with shapes.textured(self.floor_texture):
            shapes.polygon(corners, (1.0, 1.0, 1.0), (0.0, 1.0, 0.0), uvs)

    def _draw_ceiling(self, shapes, left, right, back, front, height):
        shapes.box(left, height, back, right, height + 0.2, front, self.palette.ceiling)

    def _draw_pillar(self, shapes):
        left, right, front = self.pillar
        back = self.foyer[2]
        palette = self.palette
        shapes.box(left, 0.0, front, right, self.foyer_height, back, palette.wall)
        shapes.box(left - 0.02, 0.0, front - 0.02, right + 0.02, 0.15, back, palette.skirting)
        shapes.box(left - 0.08, self.foyer_height - 0.3, front - 0.08, right + 0.08, self.foyer_height, back,
                   palette.cornice)

    def draw(self, shapes):
        foyer_left, foyer_right, foyer_back, foyer_front = self.foyer
        hall_left, hall_right, hall_back, hall_front = self.hall
        self._draw_floor(shapes, foyer_left, foyer_right, hall_front, foyer_front)
        self._draw_floor(shapes, hall_left, hall_right, hall_back, hall_front)
        self._draw_ceiling(shapes, foyer_left, foyer_right, hall_front, foyer_front, self.foyer_height)
        self._draw_ceiling(shapes, hall_left, hall_right, hall_back, hall_front, self.hall_height)
        for wall in self.walls:
            wall.draw(shapes)
        self._draw_pillar(shapes)
        for radiator in self.radiators:
            radiator.draw(shapes)
        for spotlight in self.spotlights:
            spotlight.draw(shapes)

    def draw_glow(self):
        """Warm light pools of the spotlights; call with lighting off,
        additive blending and depth writes off."""
        for spotlight in self.spotlights:
            spotlight.draw_glow()
