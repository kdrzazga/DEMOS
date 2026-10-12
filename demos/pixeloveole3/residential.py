from demos.pixeloveole3.facade_parts import RectWindow, WindowStyle
from demos.pixeloveole3.roofs import HipRoof


class Footprint:
    def __init__(self, x0, z0, x1, z1):
        self.x0 = x0
        self.z0 = z0
        self.x1 = x1
        self.z1 = z1

    def faces(self):
        width = self.x1 - self.x0
        depth = self.z1 - self.z0
        return (("front", self.x0, self.z1, 0.0, width),
                ("east", self.x1, self.z1, 90.0, depth),
                ("back", self.x1, self.z0, 180.0, width),
                ("west", self.x0, self.z0, -90.0, depth))


class BuildingStyle:
    def __init__(self, wall, roof, ridge, trim, plinth, frame, glass, sill):
        self.wall = wall
        self.roof = roof
        self.ridge = ridge
        self.trim = trim
        self.plinth = plinth
        self.frame = frame
        self.glass = glass
        self.sill = sill


class PlainBuilding:
    def __init__(self, style, footprint, height, roof_rise, window_rows, columns, roof_texture, plinth_height=1.0):
        self.style = style
        self.footprint = footprint
        self.height = height
        self.columns = columns
        self.plinth_height = plinth_height
        self.window_style = WindowStyle(style.frame, style.glass, style.frame, style.sill, style.trim, style.wall,
                                        surround=0.16, depth=0.08)
        self.windows = tuple((bottom, RectWindow(self.window_style, width, window_height, transoms=(0.66,)))
                             for bottom, window_height, width in window_rows)
        self.roof = HipRoof(footprint.x0 - 0.5, footprint.z0 - 0.5, footprint.x1 + 0.5, footprint.z1 + 0.5, height,
                            roof_rise, style.roof, roof_texture, style.ridge)

    def draw(self, shapes):
        footprint = self.footprint
        shapes.box(footprint.x0, 0.0, footprint.z0, footprint.x1, self.height, footprint.z1, self.style.wall)
        for name, x, z, yaw, length in footprint.faces():
            with shapes.frame(x, 0.0, z, yaw):
                self._draw_face(shapes, length, self.columns.get(name, 0))
                self.decorate_face(shapes, name, length)
        shapes.box(footprint.x0 - 0.5, self.height - 0.12, footprint.z0 - 0.5, footprint.x1 + 0.5, self.height,
                   footprint.z1 + 0.5, self.style.trim)
        self.roof.draw(shapes)
        self.decorate_roof(shapes)

    def _draw_face(self, shapes, length, count):
        style = self.style
        shapes.box(0.0, 0.0, 0.0, length, self.plinth_height, 0.1, style.plinth)
        shapes.box(-0.1, self.height - 0.7, 0.0, length + 0.1, self.height - 0.12, 0.22, style.trim)
        top_row = self.windows[-1][0]
        shapes.box(0.0, top_row - 0.42, 0.0, length, top_row - 0.3, 0.07, style.sill)
        for column in range(count):
            center = (column + 0.5) * length / count
            for bottom, window in self.windows:
                window.draw(shapes, center, bottom)

    def column_center(self, name, length, column):
        return (column + 0.5) * length / self.columns[name]

    def decorate_face(self, shapes, name, length):
        pass

    def decorate_roof(self, shapes):
        pass


class Dormer:
    def __init__(self, roof, z, window, wall_color, roof_color, half_width=1.0, lift=0.6):
        self.z = z
        self.window = window
        self.wall_color = wall_color
        self.roof_color = roof_color
        self.half_width = half_width
        self.eave = roof.base
        self.base = roof.base + lift
        self.front_x = roof.x0 + lift / roof.pitch

    def draw(self, shapes):
        front, base, z, half = self.front_x, self.base, self.z, self.half_width
        wall_top = base + 1.7
        ridge = base + 2.4
        shapes.box(front, self.eave, z - half, front + 3.2, wall_top, z + half, self.wall_color)
        shapes.polygon(((front, wall_top, z - half), (front, wall_top, z + half), (front, ridge - 0.05, z)),
                       self.wall_color, (-1.0, 0.0, 0.0))
        with shapes.frame(front, base, z - half, -90.0):
            self.window.draw(shapes, half, 0.35)
        for side in (-1.0, 1.0):
            slope = ((front - 0.3, wall_top - 0.1, z + side * (half + 0.25)),
                     (front + 3.2, wall_top - 0.1, z + side * (half + 0.25)),
                     (front + 3.2, ridge, z), (front - 0.3, ridge, z))
            shapes.polygon(slope, self.roof_color, shapes.upward_normal(slope))


class Tenement(PlainBuilding):
    def __init__(self, style, footprint, height, roof_rise, window_rows, columns, roof_texture, balcony_columns,
                 dormer_positions, railing_color):
        super().__init__(style, footprint, height, roof_rise, window_rows, columns, roof_texture)
        self.balcony_columns = balcony_columns
        self.railing_color = railing_color
        dormer_window = RectWindow(self.window_style, 0.9, 1.1, transoms=(0.6,))
        self.dormers = tuple(Dormer(self.roof, z, dormer_window, style.wall, style.roof) for z in dormer_positions)

    def decorate_face(self, shapes, name, length):
        if name != "west":
            return
        for column in self.balcony_columns:
            center = self.column_center(name, length, column)
            for bottom, _ in self.windows[1:]:
                self._draw_balcony(shapes, center, bottom - 0.1)

    def _draw_balcony(self, shapes, center, floor):
        railing = self.railing_color
        shapes.box(center - 1.3, floor - 0.2, 0.0, center + 1.3, floor, 1.3, self.style.plinth)
        shapes.box(center - 1.3, floor, 1.2, center + 1.3, floor + 1.0, 1.3, railing)
        shapes.box(center - 1.3, floor, 0.0, center - 1.2, floor + 1.0, 1.3, railing)
        shapes.box(center + 1.2, floor, 0.0, center + 1.3, floor + 1.0, 1.3, railing)
        shapes.box(center - 1.35, floor + 1.0, 0.0, center + 1.35, floor + 1.06, 1.35, self.style.trim)

    def decorate_roof(self, shapes):
        for dormer in self.dormers:
            dormer.draw(shapes)
