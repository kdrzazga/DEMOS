import math

from demos.pixeloveole3.facade_parts import (ArcadeWall, ArchedWindow, Cornice, DentilCourse, RectWindow,
                                             Rustication, WindowStyle)
from demos.pixeloveole3.flag import Flag
from demos.pixeloveole3.roofs import HipRoof


class LibraryPalette:
    def __init__(self):
        self.wall = (0.90, 0.52, 0.34)
        self.side_wall = (0.92, 0.60, 0.48)
        self.cream = (0.91, 0.86, 0.77)
        self.cream_light = (0.95, 0.92, 0.85)
        self.stone = (0.76, 0.72, 0.62)
        self.joint = (0.52, 0.49, 0.43)
        self.plinth = (0.62, 0.60, 0.56)
        self.hood = (0.40, 0.42, 0.45)
        self.frame = (0.96, 0.95, 0.92)
        self.glass = (0.16, 0.20, 0.25)
        self.dentil_shadow = (0.30, 0.28, 0.26)
        self.portico = (0.93, 0.81, 0.73)
        self.portico_shadow = (0.78, 0.66, 0.60)
        self.door = (0.22, 0.18, 0.16)
        self.roof = (0.88, 0.47, 0.33)
        self.ridge = (0.70, 0.33, 0.24)
        self.chimney = (0.66, 0.30, 0.22)
        self.chimney_cap = (0.45, 0.40, 0.38)
        self.eave = (0.30, 0.27, 0.25)
        self.pipe = (0.32, 0.33, 0.35)
        self.step = (0.70, 0.69, 0.66)
        self.caption_ink = (140, 46, 34)


class FloorLevels:
    def __init__(self):
        self.plinth = 0.8
        self.ground_window = 1.3
        self.ground_window_height = 3.3
        self.belt_bottom = 5.2
        self.belt_top = 6.0
        self.first_window = 6.4
        self.first_window_height = 2.4
        self.sill_belt_bottom = 9.6
        self.sill_belt_top = 9.85
        self.second_window = 9.95
        self.second_window_height = 2.3
        self.lower_dentils = 12.75
        self.attic_bottom = 13.0
        self.attic_window = 13.45
        self.attic_window_height = 0.75
        self.upper_dentils = 14.55
        self.cornice = 14.8
        self.eave = 15.8


class ClassicalFacade:
    def __init__(self, palette, levels, length, wall_color, bays=(), pilasters=(), arched_ground=True,
                 door_bays=()):
        self.palette = palette
        self.levels = levels
        self.length = length
        self.wall_color = wall_color
        self.bays = bays
        self.pilasters = pilasters
        self.arched_ground = arched_ground
        self.door_bays = door_bays
        style = WindowStyle(palette.frame, palette.glass, palette.frame, palette.cream, palette.hood, palette.cream)
        self.ground_window = ArchedWindow(style, 1.6, levels.ground_window_height)
        self.first_window = RectWindow(style, 1.4, levels.first_window_height, hood=True)
        self.balcony_door = RectWindow(style, 1.4, levels.first_window + levels.first_window_height - levels.belt_top,
                                       transoms=(0.75, 0.5, 0.25), hood=True)
        self.second_window = RectWindow(style, 1.4, levels.second_window_height)
        self.attic_window = RectWindow(style, 1.1, levels.attic_window_height, transoms=())
        self.rustication = Rustication(palette.stone, palette.joint)
        self.dentils = DentilCourse(palette.frame, palette.dentil_shadow)
        self.cornice = Cornice(((0.25, 0.12, palette.cream), (0.3, 0.3, palette.stone), (0.45, 0.6, palette.cream)),
                               palette.hood)

    def draw(self, shapes):
        palette = self.palette
        levels = self.levels
        length = self.length
        shapes.box(0.0, 0.0, 0.0, length, levels.cornice, 0.01, self.wall_color)
        shapes.box(0.0, 0.0, 0.0, length, levels.plinth, 0.14, palette.plinth)
        shapes.box(0.0, levels.belt_bottom, 0.0, length, levels.belt_top, 0.06, palette.cream)
        shapes.box(0.0, levels.belt_top - 0.14, 0.0, length, levels.belt_top, 0.14, palette.cream_light)
        shapes.box(0.0, levels.sill_belt_bottom, 0.0, length, levels.sill_belt_top, 0.12, palette.cream)
        shapes.box(0.0, levels.attic_bottom, 0.0, length, levels.cornice, 0.05, palette.cream)
        self.dentils.draw(shapes, 0.0, length, levels.lower_dentils)
        self.dentils.draw(shapes, 0.0, length, levels.upper_dentils)
        for center in self.bays:
            self._draw_bay(shapes, center)
        for left, right in self.pilasters:
            self.rustication.draw(shapes, left, right, levels.plinth, levels.attic_bottom)
            shapes.box(left, levels.attic_bottom, 0.0, right, levels.cornice, 0.12, palette.stone)
        self.cornice.draw(shapes, 0.0, length, levels.cornice)

    def _draw_bay(self, shapes, center):
        levels = self.levels
        if self.arched_ground:
            self.ground_window.draw(shapes, center, levels.ground_window)
        shapes.box(center - 0.85, levels.belt_bottom + 0.12, 0.0, center + 0.85, levels.belt_top - 0.24, 0.1,
                   self.palette.cream_light)
        if center in self.door_bays:
            self.balcony_door.draw(shapes, center, levels.belt_top)
        else:
            self.first_window.draw(shapes, center, levels.first_window)
        self.second_window.draw(shapes, center, levels.second_window)
        self.attic_window.draw(shapes, center, levels.attic_window)


class SegmentalPediment:
    def __init__(self, palette, width, rise, roof_texture, roof_depth=7.5, segments=24):
        self.palette = palette
        self.width = width
        self.rise = rise
        self.roof_texture = roof_texture
        self.roof_depth = roof_depth
        self.radius = (width * width / 4.0 + rise * rise) / (2.0 * rise)
        self.center_y = rise - self.radius
        sweep = math.asin(width / 2.0 / self.radius)
        self.angles = [-sweep + 2.0 * sweep * index / segments for index in range(segments + 1)]

    def _point(self, angle, radius, depth):
        return self.width / 2.0 + radius * math.sin(angle), self.center_y + radius * math.cos(angle), depth

    def _radial(self, angle, sign=1.0):
        return sign * math.sin(angle), sign * math.cos(angle), 0.0

    def draw(self, shapes):
        tympanum = [self._point(angle, self.radius, 0.0) for angle in self.angles]
        shapes.fan((self.width / 2.0, 0.0, 0.0), tympanum, (0.0, 0.0, 1.0), self.palette.cream)
        self._draw_moulding(shapes)
        self._draw_oculus(shapes)
        self._draw_roof(shapes)

    def _draw_moulding(self, shapes):
        inner = self.radius - 0.3
        outer = self.radius + 0.1
        stone = self.palette.stone
        shapes.strip([(self._point(angle, inner, 0.45), self._point(angle, outer, 0.45)) for angle in self.angles],
                     [(0.0, 0.0, 1.0)] * len(self.angles), stone)
        shapes.strip([(self._point(angle, outer, 0.45), self._point(angle, outer, -0.5)) for angle in self.angles],
                     [self._radial(angle) for angle in self.angles], stone)
        shapes.strip([(self._point(angle, inner, 0.45), self._point(angle, inner, 0.0)) for angle in self.angles],
                     [self._radial(angle, -1.0) for angle in self.angles], self.palette.hood)

    def _draw_oculus(self, shapes):
        center_x = self.width / 2.0
        center_y = self.rise * 0.42
        for radius, depth, color in ((0.62, 0.04, self.palette.stone), (0.44, 0.08, self.palette.glass)):
            rim = [(center_x + radius * math.cos(2.0 * math.pi * index / 20),
                    center_y + radius * math.sin(2.0 * math.pi * index / 20), depth) for index in range(21)]
            shapes.fan((center_x, center_y, depth), rim, (0.0, 0.0, 1.0), color)
        shapes.box(center_x - 0.04, center_y - 0.44, 0.0, center_x + 0.04, center_y + 0.44, 0.11, self.palette.frame)
        shapes.box(center_x - 0.44, center_y - 0.04, 0.0, center_x + 0.44, center_y + 0.04, 0.11, self.palette.frame)

    def _draw_roof(self, shapes):
        radius = self.radius + 0.12
        front = 0.55
        back = -self.roof_depth
        step = radius * (self.angles[1] - self.angles[0])
        pairs = [(self._point(angle, radius, front), self._point(angle, radius, back)) for angle in self.angles]
        uvs = [((index * step / 0.5, 0.0), (index * step / 0.5, (front - back) / 0.42))
               for index in range(len(self.angles))]
        with shapes.textured(self.roof_texture):
            shapes.strip(pairs, [self._radial(angle) for angle in self.angles], self.palette.roof, uvs)


class Portico:
    def __init__(self, palette, left, right, back, front, height, caption_texture):
        self.palette = palette
        self.left = left
        self.right = right
        self.back = back
        self.front = front
        self.height = height
        self.caption_texture = caption_texture
        self.arcade = ArcadeWall(palette.portico, palette.portico_shadow, palette.cream)
        width = right - left
        depth = front - back
        self.front_openings = ((width * 0.28, 1.3, 3.2), (width * 0.72, 1.3, 3.2))
        self.left_openings = ((1.8, 0.8, 3.4),)
        self.right_openings = ((depth - 1.8, 0.8, 3.4),)
        balcony = height + 1.0
        self.flags = (Flag((left - 0.15, balcony, front + 0.3), (-0.6, 0.75, 0.35), phase=0.0),
                      Flag((right + 0.15, balcony, front + 0.3), (0.6, 0.75, 0.35), phase=1.7))

    def draw(self, shapes):
        palette = self.palette
        left, right, back, front, height = self.left, self.right, self.back, self.front, self.height
        shapes.box(left, 0.0, back, right, 0.6, front, palette.step)
        shapes.box(left - 0.6, 0.0, front, right + 0.6, 0.45, front + 0.7, palette.step)
        shapes.box(left - 1.2, 0.0, front + 0.7, right + 1.2, 0.3, front + 1.4, palette.step)
        self._draw_doors(shapes)
        with shapes.frame(left, 0.0, front, 0.0):
            self.arcade.draw(shapes, right - left, height, self.front_openings)
        with shapes.frame(left, 0.0, back, -90.0):
            self.arcade.draw(shapes, front - back, height, self.left_openings)
        with shapes.frame(right, 0.0, front, 90.0):
            self.arcade.draw(shapes, front - back, height, self.right_openings)
        shapes.box(left - 0.04, height - 0.75, front - 0.6, right + 0.04, height - 0.6, front + 0.06, palette.cream)
        shapes.box(left - 0.2, height, back, right + 0.2, height + 0.3, front + 0.25, palette.cream)
        self._draw_parapet(shapes)
        for flag in self.flags:
            flag.draw_pole(shapes)

    def _draw_doors(self, shapes):
        palette = self.palette
        for center, half, _ in self.front_openings:
            door_left = self.left + center - half * 0.7
            door_right = self.left + center + half * 0.7
            shapes.box(door_left - 0.15, 0.6, self.back, door_right + 0.15, 3.65, self.back + 0.06, palette.cream)
            shapes.box(door_left, 0.6, self.back, door_right, 3.5, self.back + 0.1, palette.door)
            middle = (door_left + door_right) / 2.0
            shapes.box(middle - 0.03, 0.6, self.back, middle + 0.03, 3.5, self.back + 0.13, palette.portico_shadow)

    def _draw_parapet(self, shapes):
        palette = self.palette
        left, right, back, front = self.left, self.right, self.back, self.front
        floor = self.height + 0.3
        top = self.height + 1.35
        shapes.box(left - 0.2, floor, front - 0.05, right + 0.2, top, front + 0.25, palette.cream)
        shapes.box(left - 0.2, floor, back, left + 0.1, top, front + 0.25, palette.cream)
        shapes.box(right - 0.1, floor, back, right + 0.2, top, front + 0.25, palette.cream)
        shapes.box(left - 0.3, top, front - 0.1, right + 0.3, top + 0.1, front + 0.35, palette.stone)
        shapes.box(left - 0.3, top, back, left + 0.2, top + 0.1, front + 0.35, palette.stone)
        shapes.box(right - 0.2, top, back, right + 0.3, top + 0.1, front + 0.35, palette.stone)
        caption = ((left + 0.45, floor + 0.12, front + 0.26), (right - 0.45, floor + 0.12, front + 0.26),
                   (right - 0.45, top - 0.1, front + 0.26), (left + 0.45, top - 0.1, front + 0.26))
        with shapes.textured(self.caption_texture):
            shapes.polygon(caption, (1.0, 1.0, 1.0), (0.0, 0.0, 1.0), ((0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)))


class Library:
    def __init__(self, roof_texture, texture_factory):
        self.palette = LibraryPalette()
        self.levels = FloorLevels()
        self.width = 31.0
        self.depth = 24.0
        self.risalit_left = 11.4
        self.risalit_right = 19.6
        self.risalit_projection = 0.5
        palette = self.palette
        levels = self.levels
        background = tuple(int(component * 255) for component in palette.cream)
        caption_texture = texture_factory.upload(
            texture_factory.caption("BIBLIOTEKA", palette.caption_ink, background), repeat=False)
        risalit_width = self.risalit_right - self.risalit_left
        self.front_facade = ClassicalFacade(palette, levels, self.width, palette.wall,
                                            bays=(3.4, 6.4, 9.4, 21.6, 24.6, 27.6),
                                            pilasters=((0.0, 1.4), (29.6, 31.0)))
        self.west_facade = ClassicalFacade(palette, levels, self.depth, palette.side_wall,
                                           bays=(2.5, 5.8, 9.1, 12.4, 15.7, 19.0),
                                           pilasters=((0.0, 0.8), (22.6, 24.0)))
        self.back_facade = ClassicalFacade(palette, levels, self.width, palette.wall)
        self.east_facade = ClassicalFacade(palette, levels, self.depth, palette.wall)
        self.risalit_facade = ClassicalFacade(palette, levels, risalit_width, palette.wall, bays=(2.8, 5.4),
                                              pilasters=((0.0, 1.2), (risalit_width - 1.2, risalit_width)),
                                              arched_ground=False, door_bays=(2.8,))
        self.pediment = SegmentalPediment(palette, risalit_width, 2.4, roof_texture)
        self.portico = Portico(palette, self.risalit_left, self.risalit_right, self.risalit_projection, 4.0, 5.4,
                               caption_texture)
        self.roof = HipRoof(-0.7, -self.depth - 0.7, self.width + 0.7, 0.7, levels.eave, 6.0, palette.roof,
                            roof_texture, palette.ridge)
        self.chimneys = ((4.5, -9.0), (7.5, -5.5), (10.5, -7.0), (14.0, -11.5), (17.0, -11.5), (20.5, -7.0),
                         (23.5, -5.0), (26.5, -9.0), (9.0, -17.0), (22.0, -18.0))

    def draw(self, shapes):
        palette = self.palette
        eave = self.levels.eave
        shapes.box(0.0, 0.0, -self.depth, self.width, eave, 0.0, palette.wall)
        with shapes.frame(0.0, 0.0, 0.0):
            self.front_facade.draw(shapes)
        with shapes.frame(0.0, 0.0, -self.depth, -90.0):
            self.west_facade.draw(shapes)
        with shapes.frame(self.width, 0.0, -self.depth, 180.0):
            self.back_facade.draw(shapes)
        with shapes.frame(self.width, 0.0, 0.0, 90.0):
            self.east_facade.draw(shapes)
        shapes.box(self.risalit_left, 0.0, -0.2, self.risalit_right, eave, self.risalit_projection, palette.wall)
        with shapes.frame(self.risalit_left, 0.0, self.risalit_projection):
            self.risalit_facade.draw(shapes)
        with shapes.frame(self.risalit_left, eave, self.risalit_projection):
            self.pediment.draw(shapes)
        self.portico.draw(shapes)
        shapes.box(-0.7, eave - 0.12, -self.depth - 0.7, self.width + 0.7, eave, 0.7, palette.eave)
        self.roof.draw(shapes)
        self._draw_chimneys(shapes)
        shapes.box(self.width - 0.15, 0.0, 0.0, self.width + 0.1, eave, 0.25, palette.pipe)

    def _draw_chimneys(self, shapes):
        palette = self.palette
        for x, z in self.chimneys:
            top = self.roof.height_at(x, z) + 1.6
            shapes.box(x - 0.45, self.levels.eave, z - 0.35, x + 0.45, top, z + 0.35, palette.chimney)
            shapes.box(x - 0.55, top, z - 0.45, x + 0.55, top + 0.18, z + 0.45, palette.chimney_cap)
            shapes.box(x - 0.22, top + 0.18, z - 0.18, x + 0.22, top + 0.45, z + 0.18, palette.chimney)

    def draw_animated(self, elapsed):
        for flag in self.portico.flags:
            flag.draw_cloth(elapsed)
