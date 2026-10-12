from OpenGL.GL import *

from lib.urban.residential import BuildingProportions, BuildingStyle, Footprint, PlainBuilding
from lib.urban.shapes import Shapes


class Chimney:
    def __init__(self, x, z, width, rise, color, cap_color, cap_height=0.12, cap_overhang=0.07):
        self.x = x
        self.z = z
        self.width = width
        self.rise = rise
        self.color = color
        self.cap_color = cap_color
        self.cap_height = cap_height
        self.cap_overhang = cap_overhang

    def draw(self, shapes, roof):
        half = self.width / 2.0
        cap = half + self.cap_overhang
        top = roof.top + self.rise
        shapes.box(self.x - half, roof.base, self.z - half, self.x + half, top, self.z + half, self.color)
        shapes.box(self.x - cap, top, self.z - cap, self.x + cap, top + self.cap_height, self.z + cap, self.cap_color)


class UrbanBuilding(PlainBuilding):
    def __init__(self, style, footprint, height, roof_rise, window_rows, columns, roof_texture, proportions,
                 entrance_column, door_size, door_color, chimney):
        super().__init__(style, footprint, height, roof_rise, window_rows, columns, roof_texture, proportions)
        self.entrance_column = entrance_column
        self.door_size = door_size
        self.door_color = door_color
        self.chimney = chimney

    def has_window(self, name, column, row):
        return not (name == "front" and row == 0 and column == self.entrance_column)

    def decorate_face(self, shapes, name, length):
        if name != "front":
            return
        center = self.column_center(name, length, self.entrance_column)
        door_width, door_height = self.door_size
        half = door_width / 2.0
        rim = self.proportions.window_surround
        depth = self.proportions.window_depth
        shapes.box(center - half - rim, 0.0, 0.0, center + half + rim, door_height + rim, depth, self.style.frame)
        shapes.box(center - half, 0.0, 0.0, center + half, door_height, depth + 0.02, self.door_color)
        shapes.box(center - half - rim - 0.1, door_height + rim, 0.0, center + half + rim + 0.1,
                   door_height + rim + 0.08, 0.35, self.style.trim)

    def decorate_roof(self, shapes):
        self.chimney.draw(shapes, self.roof)


class DetailedHouse:
    def __init__(self, x, y, z, floor_count, windows_per_floor=3, color=(0.6, 0.6, 0.6),
                 facing=0.0, snow_top=0.0, chimney_scale=1.0, chimney_width_scale=1.0, shapes=None,
                 roof_texture=None):
        self.x = x
        self.y = y
        self.z = z
        self.floor_count = max(1, floor_count)
        self.windows_per_floor = max(1, windows_per_floor)
        self.color = color
        self.facing = facing
        self.snow_top = max(0.0, min(1.0, snow_top))
        self.chimney_scale = chimney_scale
        self.chimney_width_scale = chimney_width_scale

        self.bay_width = 1.45
        self.depth_ratio = 0.78
        self.floor_height = 2.4
        self.roof_height = 1.8
        self.roof_overhang = 0.26
        self.roof_color = (0.66, 0.32, 0.24)
        self.ridge_color = (0.48, 0.22, 0.17)
        self.snow_color = (0.90, 0.92, 0.95)
        self.window_color = (0.95, 0.72, 0.28)
        self.frame_color = (0.90, 0.88, 0.84)
        self.door_color = (0.32, 0.20, 0.13)
        self.window_size = (0.62, 0.88)
        self.door_size = (0.92, 1.55)
        self.sill_fraction = 0.55
        self.chimney_color = (0.57, 0.14, 0.11)
        self.chimney_cap_color = (0.34, 0.10, 0.08)
        self.chimney_ratio = 0.14
        self.chimney_span = (0.35, 0.70)
        self.chimney_base_rise = 1.15
        self.chimney_cap_height = 0.12
        self.proportions = BuildingProportions(plinth_height=0.35, cornice_height=0.3, cornice_projection=0.1,
                                               eave_overhang=self.roof_overhang, eave_thickness=0.06,
                                               window_surround=0.07, window_depth=0.05, belt_drop=0.22,
                                               belt_thickness=0.06, transoms=(0.62,))

        self.width = self.windows_per_floor * self.bay_width
        self.depth = self.width * self.depth_ratio
        self.body_height = self.floor_count * self.floor_height
        self.roof_peak = self.body_height + self.roof_height
        self.chimney_rise = self.chimney_base_rise * self.chimney_scale
        self.chimney_width = min(max(self.width * self.chimney_ratio, self.chimney_span[0]),
                                 self.chimney_span[1]) * self.chimney_scale * self.chimney_width_scale
        self.total_height = self.roof_peak + self.chimney_rise + self.chimney_cap_height
        self.shapes = shapes or Shapes()
        self.building = self._create_building(roof_texture)
        self.display_list = self._compile()

    def _blend(self, first, second, amount):
        return tuple(first[index] + (second[index] - first[index]) * amount for index in range(3))

    def _scaled(self, color, factor):
        return tuple(min(1.0, component * factor) for component in color)

    def _create_style(self):
        return BuildingStyle(wall=self.color,
                             roof=self._blend(self.roof_color, self.snow_color, self.snow_top),
                             ridge=self._blend(self.ridge_color, self.snow_color, self.snow_top),
                             trim=self._scaled(self.color, 0.8), plinth=self._scaled(self.color, 0.65),
                             frame=self.frame_color, glass=self.window_color, sill=self._scaled(self.color, 0.75))

    def _window_rows(self):
        window_width, window_height = self.window_size
        return tuple((floor * self.floor_height + (self.floor_height - window_height) * self.sill_fraction,
                      window_height, window_width) for floor in range(self.floor_count))

    def _create_building(self, roof_texture):
        half_width = self.width / 2.0
        half_depth = self.depth / 2.0
        side_columns = max(1, round(self.depth / self.bay_width))
        columns = {"front": self.windows_per_floor, "back": self.windows_per_floor,
                   "east": side_columns, "west": side_columns}
        chimney = Chimney(0.0, -half_depth * 0.15, self.chimney_width, self.chimney_rise, self.chimney_color,
                          self.chimney_cap_color, self.chimney_cap_height)
        return UrbanBuilding(self._create_style(), Footprint(-half_width, -half_depth, half_width, half_depth),
                             self.body_height, self.roof_height, self._window_rows(), columns, roof_texture,
                             self.proportions, self.windows_per_floor // 2, self.door_size, self.door_color, chimney)

    def _compile(self):
        display_list = glGenLists(1)
        glNewList(display_list, GL_COMPILE)
        self.building.draw(self.shapes)
        glEndList()
        return display_list

    def release(self):
        if self.display_list:
            glDeleteLists(self.display_list, 1)
            self.display_list = 0

    def draw(self):
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        glRotatef(self.facing, 0.0, 1.0, 0.0)
        glCallList(self.display_list)
        glPopMatrix()
