import math
from OpenGL.GL import *
from OpenGL.GLU import *


class House:
    def __init__(self, x, y, z, floor_count, windows_per_floor=3, color=(0.6, 0.6, 0.6), facing=0.0):
        self.x = x
        self.y = y
        self.z = z
        self.floor_count = max(1, floor_count)
        self.windows_per_floor = max(1, windows_per_floor)
        self.color = color
        self.facing = facing

        self.bay_width = 1.45
        self.depth_ratio = 0.78
        self.floor_height = 2.4
        self.roof_height = 1.8
        self.roof_overhang = 0.26
        self.roof_color = (0.38, 0.17, 0.15)
        self.window_color = (0.95, 0.72, 0.28)
        self.frame_color = (0.30, 0.26, 0.24)
        self.door_color = (0.32, 0.20, 0.13)
        self.window_size = (0.62, 0.88)
        self.door_size = (0.92, 1.55)
        self.chimney_color = (0.57, 0.14, 0.11)
        self.chimney_cap_color = (0.34, 0.10, 0.08)
        self.chimney_ratio = 0.14
        self.chimney_span = (0.35, 0.70)
        self.chimney_rise = 1.15
        self.chimney_cap_height = 0.12
        self.chimney_cap_overhang = 0.07
        self.frame_margin = 0.12
        self.sill_fraction = 0.55
        self.surface_lift = 0.02

        self.width = self.windows_per_floor * self.bay_width
        self.depth = self.width * self.depth_ratio
        self.body_height = self.floor_count * self.floor_height
        self.roof_peak = self.body_height + self.roof_height
        self.chimney_width = min(max(self.width * self.chimney_ratio, self.chimney_span[0]),
                                 self.chimney_span[1])
        self.total_height = self.roof_peak + self.chimney_rise + self.chimney_cap_height
        self.display_list = self._compile()

    def _bay_offsets(self):
        span = self.width / self.windows_per_floor
        return tuple(-self.width / 2.0 + span * (index + 0.5) for index in range(self.windows_per_floor))

    def _entrance_bay(self):
        return self.windows_per_floor // 2

    def _draw_box(self, bottom, height, size_x, size_z, capped):
        half_x = size_x / 2.0
        half_z = size_z / 2.0
        top = bottom + height
        faces = (((0.0, 0.0, 1.0), ((-half_x, bottom, half_z), (half_x, bottom, half_z),
                                    (half_x, top, half_z), (-half_x, top, half_z))),
                 ((0.0, 0.0, -1.0), ((half_x, bottom, -half_z), (-half_x, bottom, -half_z),
                                     (-half_x, top, -half_z), (half_x, top, -half_z))),
                 ((1.0, 0.0, 0.0), ((half_x, bottom, half_z), (half_x, bottom, -half_z),
                                    (half_x, top, -half_z), (half_x, top, half_z))),
                 ((-1.0, 0.0, 0.0), ((-half_x, bottom, -half_z), (-half_x, bottom, half_z),
                                     (-half_x, top, half_z), (-half_x, top, -half_z))))
        if capped:
            faces = faces + (((0.0, 1.0, 0.0), ((-half_x, top, half_z), (half_x, top, half_z),
                                                (half_x, top, -half_z), (-half_x, top, -half_z))),)
        glBegin(GL_QUADS)
        for normal, corners in faces:
            glNormal3f(*normal)
            for corner in corners:
                glVertex3f(*corner)
        glEnd()

    def _draw_walls(self):
        glColor3f(*self.color)
        self._draw_box(0.0, self.body_height, self.width, self.depth, False)

    def _draw_chimney(self):
        shaft_top = self.roof_peak + self.chimney_rise
        cap_width = self.chimney_width + self.chimney_cap_overhang * 2.0
        glColor3f(*self.chimney_color)
        self._draw_box(self.body_height, shaft_top - self.body_height,
                       self.chimney_width, self.chimney_width, False)
        glColor3f(*self.chimney_cap_color)
        self._draw_box(shaft_top, self.chimney_cap_height, cap_width, cap_width, True)

    def _draw_gables(self):
        half_width = self.width / 2.0
        half_depth = self.depth / 2.0
        ridge = self.roof_peak
        glColor3f(*self.color)
        glBegin(GL_TRIANGLES)
        for side in (1.0, -1.0):
            glNormal3f(0.0, 0.0, side)
            corners = ((-half_width * side, self.body_height, half_depth * side),
                       (half_width * side, self.body_height, half_depth * side),
                       (0.0, ridge, half_depth * side))
            for corner in corners:
                glVertex3f(*corner)
        glEnd()

    def _draw_roof(self):
        half_width = self.width / 2.0
        eaves_width = half_width + self.roof_overhang
        eaves_depth = self.depth / 2.0 + self.roof_overhang
        ridge = self.roof_peak
        eaves = self.body_height - self.roof_height * self.roof_overhang / half_width
        slope = math.hypot(self.roof_height, half_width)
        glColor3f(*self.roof_color)
        glBegin(GL_QUADS)
        for side in (1.0, -1.0):
            glNormal3f(side * self.roof_height / slope, half_width / slope, 0.0)
            glVertex3f(side * eaves_width, eaves, side * eaves_depth)
            glVertex3f(0.0, ridge, side * eaves_depth)
            glVertex3f(0.0, ridge, -side * eaves_depth)
            glVertex3f(side * eaves_width, eaves, -side * eaves_depth)
        glEnd()

    def _draw_front_panel(self, center_x, bottom, panel_width, panel_height, color, lift):
        front = self.depth / 2.0 + lift
        half = panel_width / 2.0
        glColor3f(*color)
        glNormal3f(0.0, 0.0, 1.0)
        glBegin(GL_QUADS)
        glVertex3f(center_x - half, bottom, front)
        glVertex3f(center_x + half, bottom, front)
        glVertex3f(center_x + half, bottom + panel_height, front)
        glVertex3f(center_x - half, bottom + panel_height, front)
        glEnd()

    def _draw_openings(self):
        window_width, window_height = self.window_size
        door_width, door_height = self.door_size
        margin = self.frame_margin
        entrance = self._entrance_bay()
        near = self.surface_lift * 0.5
        for floor in range(self.floor_count):
            sill = floor * self.floor_height + (self.floor_height - window_height) * self.sill_fraction
            for bay, offset in enumerate(self._bay_offsets()):
                if floor == 0 and bay == entrance:
                    self._draw_front_panel(offset, 0.0, door_width + margin, door_height + margin * 0.5,
                                           self.frame_color, near)
                    self._draw_front_panel(offset, 0.0, door_width, door_height, self.door_color,
                                           self.surface_lift)
                else:
                    self._draw_front_panel(offset, sill - margin * 0.5, window_width + margin,
                                           window_height + margin, self.frame_color, near)
                    self._draw_front_panel(offset, sill, window_width, window_height, self.window_color,
                                           self.surface_lift)

    def _compile(self):
        display_list = glGenLists(1)
        glNewList(display_list, GL_COMPILE)
        self._draw_walls()
        self._draw_gables()
        self._draw_roof()
        self._draw_chimney()
        self._draw_openings()
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
