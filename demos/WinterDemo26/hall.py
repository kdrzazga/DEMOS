import math
from OpenGL.GL import *
from OpenGL.GLU import *


class Hall:
    def __init__(self, x, y, z, width=20.0, length=36.0, arch_count=7, facing=0.0, size=1.0):
        self.x = x
        self.y = y
        self.z = z
        self.width = width
        self.length = length
        self.arch_count = max(1, arch_count)
        self.facing = facing
        self.size = size

        self.half_span = width / 2.0
        self.arch_rise = 14.0
        self.arch_band = 0.8
        self.arch_depth = 0.7
        self.arch_steps = 20
        self.wall_top = 10.0
        self.ridge = 15.8
        self.brick_height = 3.2
        self.brick_course = 0.26
        self.brick_length = 0.55
        self.window_bottom = 4.6
        self.window_top = 9.2
        self.window_share = 0.55
        self.window_columns = 3
        self.window_rows = 6
        self.plank_width = 0.6

        self.stage_depth = 1.8
        self.stage_base = 3.3
        self.stage_steps = 5
        self.step_rise = 0.63
        self.landing_half = 2.4
        self.stage_half_width = 6.8
        self.opening_width = 4.8
        self.opening_height = 4.05
        self.door_size = (1.1, 2.0)
        self.side_step_count = 3
        self.side_step_depth = 0.6
        self.side_step_top = 2.2 / 3.0
        self.rail_height = 0.9

        self.wall_white = (0.7, 0.7, 0.7)
        self.lighting_gain = 1.5
        self.outline_color = (0.45, 0.45, 0.46)
        self.outline_width = 2.0
        self.arch_base_shadow = 0.62
        self.arch_base_reach = 3.0
        self.arch_crown_shadow = 0.82
        self.arch_crown_reach = 3.0
        self.eave_shadow = 0.80
        self.ridge_shadow = 0.70
        self.wall_top_shadow = 0.80
        self.brick_color = (0.42, 0.16, 0.11)
        self.mortar_color = (0.46, 0.40, 0.36)
        self.glass_color = (0.55, 0.62, 0.66)
        self.frame_color = (0.62, 0.62, 0.62)
        self.floor_color = (0.40, 0.28, 0.18)
        self.plank_color = (0.24, 0.16, 0.10)
        self.opening_color = (0.05, 0.04, 0.04)
        self.door_color = (0.50, 0.50, 0.48)
        self.rail_color = (0.18, 0.18, 0.20)
        self.roof_color = (0.22, 0.22, 0.23)
        self.roof_thickness = 0.3
        self.chimney_color = (0.57, 0.14, 0.11)
        self.chimney_cap_color = (0.34, 0.10, 0.08)
        self.chimney_width = 0.70 * 3.4 * 1.21
        self.chimney_rise = 1.15 * 3.4
        self.chimney_cap_height = 0.12
        self.chimney_cap_overhang = 0.07
        self.flue_color = (0.03, 0.03, 0.04)
        self.flue_ratio = 0.62
        self.flue_width = self.chimney_width * self.flue_ratio

        self.wall_x = self.half_span + self.arch_band
        self.side_step_run = (self.wall_x - self.stage_half_width) / self.side_step_count
        self.step_run = (self.stage_half_width - self.landing_half) / self.stage_steps
        self.chimney_z = self.length / self.arch_count / 2.0
        self.display_list = self._compile()

    def _winds_with(self, normal, corners):
        first = tuple(corners[1][axis] - corners[0][axis] for axis in range(3))
        second = tuple(corners[2][axis] - corners[0][axis] for axis in range(3))
        facing = (first[1] * second[2] - first[2] * second[1],
                  first[2] * second[0] - first[0] * second[2],
                  first[0] * second[1] - first[1] * second[0])
        return sum(facing[axis] * normal[axis] for axis in range(3)) >= 0.0

    def _quad(self, normal, corners):
        if not self._winds_with(normal, corners):
            corners = tuple(reversed(corners))
        glNormal3f(*normal)
        for corner in corners:
            glVertex3f(*corner)

    def _white(self, shade):
        glColor3f(*(channel / self.lighting_gain * shade for channel in self.wall_white))

    def _shaded_quad(self, normals, corners, shades):
        average = tuple(sum(normal[axis] for normal in normals) for axis in range(3))
        if not self._winds_with(average, corners):
            normals, corners, shades = (tuple(reversed(normals)), tuple(reversed(corners)),
                                        tuple(reversed(shades)))
        for normal, corner, shade in zip(normals, corners, shades):
            self._white(shade)
            glNormal3f(*normal)
            glVertex3f(*corner)

    def _ease(self, value):
        value = max(0.0, min(1.0, value))
        return value * value * (3.0 - 2.0 * value)

    def _arch_shade(self, height):
        base = self.arch_base_shadow + (1.0 - self.arch_base_shadow) * self._ease(height / self.arch_base_reach)
        crown = 1.0 - (1.0 - self.arch_crown_shadow) * self._ease(
            (height - (self.arch_rise - self.arch_crown_reach)) / self.arch_crown_reach)
        return base * crown

    def _bay_length(self):
        return self.length / self.arch_count

    def _arch_positions(self):
        bay = self._bay_length()
        return tuple(-self.length / 2.0 + bay * (index + 0.5) for index in range(self.arch_count))

    def _window_positions(self):
        bay = self._bay_length()
        return tuple(-self.length / 2.0 + bay * index for index in range(1, self.arch_count))

    def _draw_floor(self):
        half_length = self.length / 2.0
        glColor3f(*self.floor_color)
        glBegin(GL_QUADS)
        self._quad((0.0, 1.0, 0.0), ((-self.wall_x, 0.0, half_length), (self.wall_x, 0.0, half_length),
                                     (self.wall_x, 0.0, -half_length), (-self.wall_x, 0.0, -half_length)))
        glEnd()

    def _draw_floor_planks(self):
        half_length = self.length / 2.0
        glColor3f(*self.plank_color)
        glBegin(GL_LINES)
        across = -self.wall_x + self.plank_width
        while across < self.wall_x:
            glVertex3f(across, 0.01, -half_length)
            glVertex3f(across, 0.01, half_length)
            across += self.plank_width
        glEnd()

    def _draw_side_walls(self):
        half_length = self.length / 2.0
        glBegin(GL_QUADS)
        for side in (1.0, -1.0):
            wall = side * self.wall_x
            normal = (-side, 0.0, 0.0)
            glColor3f(*self.brick_color)
            self._quad(normal, ((wall, 0.0, -half_length), (wall, 0.0, half_length),
                                (wall, self.brick_height, half_length), (wall, self.brick_height, -half_length)))
            self._shaded_quad((normal,) * 4,
                              ((wall, self.brick_height, -half_length), (wall, self.brick_height, half_length),
                               (wall, self.wall_top, half_length), (wall, self.wall_top, -half_length)),
                              (1.0, 1.0, self.wall_top_shadow, self.wall_top_shadow))
        glEnd()

    def _draw_brick_lines(self, fixed_axis, fixed_value, span, height_limit, facing_sign, base=0.0):
        glBegin(GL_LINES)
        course = 0
        level = base + self.brick_course
        while level < height_limit:
            start, end = span
            if fixed_axis == "x":
                glVertex3f(fixed_value, level, start)
                glVertex3f(fixed_value, level, end)
            else:
                glVertex3f(start, level, fixed_value)
                glVertex3f(end, level, fixed_value)
            course += 1
            level += self.brick_course
        course = 0
        level = base
        while level < height_limit:
            top = min(height_limit, level + self.brick_course)
            along = span[0] + (self.brick_length / 2.0 if course % 2 else 0.0)
            while along < span[1]:
                if fixed_axis == "x":
                    glVertex3f(fixed_value, level, along)
                    glVertex3f(fixed_value, top, along)
                else:
                    glVertex3f(along, level, fixed_value)
                    glVertex3f(along, top, fixed_value)
                along += self.brick_length
            course += 1
            level += self.brick_course
        glEnd()

    def _draw_windows(self):
        bay = self._bay_length()
        half_window = bay * self.window_share / 2.0
        for side in (1.0, -1.0):
            wall = side * (self.wall_x - 0.03)
            normal = (-side, 0.0, 0.0)
            for center in self._window_positions():
                glColor3f(*self.frame_color)
                glBegin(GL_QUADS)
                self._quad(normal, ((wall, self.window_bottom - 0.2, center - half_window - 0.2),
                                    (wall, self.window_bottom - 0.2, center + half_window + 0.2),
                                    (wall, self.window_top + 0.2, center + half_window + 0.2),
                                    (wall, self.window_top + 0.2, center - half_window - 0.2)))
                glEnd()
                pane = wall - side * 0.02
                glColor3f(*self.glass_color)
                glBegin(GL_QUADS)
                self._quad(normal, ((pane, self.window_bottom, center - half_window),
                                    (pane, self.window_bottom, center + half_window),
                                    (pane, self.window_top, center + half_window),
                                    (pane, self.window_top, center - half_window)))
                glEnd()
                bar = pane - side * 0.02
                glDisable(GL_LIGHTING)
                glColor3f(*self.frame_color)
                glLineWidth(2.0)
                glBegin(GL_LINES)
                for column in range(1, self.window_columns):
                    along = center - half_window + 2.0 * half_window * column / self.window_columns
                    glVertex3f(bar, self.window_bottom, along)
                    glVertex3f(bar, self.window_top, along)
                for row in range(1, self.window_rows):
                    level = self.window_bottom + (self.window_top - self.window_bottom) * row / self.window_rows
                    glVertex3f(bar, level, center - half_window)
                    glVertex3f(bar, level, center + half_window)
                glEnd()
                glLineWidth(1.0)
                glEnable(GL_LIGHTING)

    def _draw_end_wall(self, end):
        wall_z = end * self.length / 2.0
        normal = (0.0, 0.0, -end)
        glBegin(GL_QUADS)
        glColor3f(*self.brick_color)
        self._quad(normal, ((-self.wall_x, 0.0, wall_z), (self.wall_x, 0.0, wall_z),
                            (self.wall_x, self.brick_height, wall_z), (-self.wall_x, self.brick_height, wall_z)))
        self._shaded_quad((normal,) * 4,
                          ((-self.wall_x, self.brick_height, wall_z), (self.wall_x, self.brick_height, wall_z),
                           (self.wall_x, self.wall_top, wall_z), (-self.wall_x, self.wall_top, wall_z)),
                          (1.0, 1.0, 0.92, 0.92))
        glEnd()
        glBegin(GL_TRIANGLES)
        self._shaded_quad((normal,) * 3,
                          ((-self.wall_x, self.wall_top, wall_z), (self.wall_x, self.wall_top, wall_z),
                           (0.0, self.ridge, wall_z)),
                          (self.eave_shadow, self.eave_shadow, self.ridge_shadow))
        glEnd()

    def _slope_height(self, across, lift):
        return self.wall_top + lift + (self.ridge - self.wall_top) * (1.0 - across / self.wall_x)

    def _slope_pieces(self, hole_half):
        half_length = self.length / 2.0
        near = self.chimney_z - hole_half
        far = self.chimney_z + hole_half
        return ((0.0, -half_length, near), (0.0, far, half_length), (hole_half, near, far))

    def _ceiling_shade(self, across):
        return self.eave_shadow + (self.ridge_shadow - self.eave_shadow) * (1.0 - across / self.wall_x)

    def _draw_roof(self):
        climb = self.ridge - self.wall_top
        slope = math.hypot(climb, self.wall_x)
        glBegin(GL_QUADS)
        for side in (1.0, -1.0):
            inward = (-side * climb / slope, -self.wall_x / slope, 0.0)
            for inner, start, end in self._slope_pieces(self.flue_width / 2.0):
                corners = ((side * self.wall_x, self._slope_height(self.wall_x, 0.0), start),
                           (side * inner, self._slope_height(inner, 0.0), start),
                           (side * inner, self._slope_height(inner, 0.0), end),
                           (side * self.wall_x, self._slope_height(self.wall_x, 0.0), end))
                shades = (self._ceiling_shade(self.wall_x), self._ceiling_shade(inner),
                          self._ceiling_shade(inner), self._ceiling_shade(self.wall_x))
                self._shaded_quad((inward,) * 4, corners, shades)
        glColor3f(*self.roof_color)
        for side in (1.0, -1.0):
            outward = (side * climb / slope, self.wall_x / slope, 0.0)
            for inner, start, end in self._slope_pieces(self.chimney_width / 2.0):
                self._quad(outward, ((side * self.wall_x, self._slope_height(self.wall_x, self.roof_thickness), start),
                                     (side * inner, self._slope_height(inner, self.roof_thickness), start),
                                     (side * inner, self._slope_height(inner, self.roof_thickness), end),
                                     (side * self.wall_x, self._slope_height(self.wall_x, self.roof_thickness), end)))
        glEnd()

    def _draw_chimney_box(self, bottom, top, size, color):
        half = size / 2.0
        near = self.chimney_z - half
        far = self.chimney_z + half
        glColor3f(*color)
        glBegin(GL_QUADS)
        for side in (1.0, -1.0):
            self._quad((0.0, 0.0, side), ((-half, bottom, self.chimney_z + side * half),
                                          (half, bottom, self.chimney_z + side * half),
                                          (half, top, self.chimney_z + side * half),
                                          (-half, top, self.chimney_z + side * half)))
            self._quad((side, 0.0, 0.0), ((side * half, bottom, near), (side * half, bottom, far),
                                          (side * half, top, far), (side * half, top, near)))
        glEnd()

    def _draw_chimney(self):
        shaft_bottom = self._slope_height(self.flue_width / 2.0, 0.0)
        shaft_top = self.ridge + self.roof_thickness + self.chimney_rise
        rim = shaft_top + self.chimney_cap_height
        cap_width = self.chimney_width + self.chimney_cap_overhang * 2.0
        half_cap = cap_width / 2.0
        half_flue = self.flue_width / 2.0
        self._draw_chimney_box(shaft_bottom, shaft_top, self.chimney_width, self.chimney_color)
        self._draw_chimney_box(shaft_top, rim, cap_width, self.chimney_cap_color)
        center = self.chimney_z
        glColor3f(*self.chimney_cap_color)
        glBegin(GL_QUADS)
        for side in (1.0, -1.0):
            self._quad((0.0, 1.0, 0.0), ((-half_cap, rim, center + side * half_cap),
                                         (half_cap, rim, center + side * half_cap),
                                         (half_cap, rim, center + side * half_flue),
                                         (-half_cap, rim, center + side * half_flue)))
            self._quad((0.0, 1.0, 0.0), ((side * half_cap, rim, center - half_flue),
                                         (side * half_cap, rim, center + half_flue),
                                         (side * half_flue, rim, center + half_flue),
                                         (side * half_flue, rim, center - half_flue)))
        glColor3f(*self.flue_color)
        for side in (1.0, -1.0):
            self._quad((0.0, 0.0, -side), ((-half_flue, shaft_bottom, center + side * half_flue),
                                           (half_flue, shaft_bottom, center + side * half_flue),
                                           (half_flue, rim, center + side * half_flue),
                                           (-half_flue, rim, center + side * half_flue)))
            self._quad((-side, 0.0, 0.0), ((side * half_flue, shaft_bottom, center - half_flue),
                                           (side * half_flue, shaft_bottom, center + half_flue),
                                           (side * half_flue, rim, center + half_flue),
                                           (side * half_flue, rim, center - half_flue)))
        glEnd()

    def _arch_profile(self, radius, center_x, side):
        finish = math.acos(-center_x / radius)
        points = []
        for step in range(self.arch_steps + 1):
            angle = finish * step / self.arch_steps
            points.append((side * (center_x + radius * math.cos(angle)), radius * math.sin(angle), angle))
        return points

    def _arch_geometry(self):
        span = self.half_span
        radius = (self.arch_rise ** 2 + span ** 2) / (2.0 * span)
        return radius, span - radius

    def _draw_arch(self, center_z):
        radius, center_x = self._arch_geometry()
        near = center_z + self.arch_depth / 2.0
        far = center_z - self.arch_depth / 2.0
        glBegin(GL_QUADS)
        for side in (1.0, -1.0):
            inner = self._arch_profile(radius, center_x, side)
            outer = self._arch_profile(radius + self.arch_band, center_x, side)
            for step in range(self.arch_steps):
                low, high = inner[step], inner[step + 1]
                low_outer, high_outer = outer[step], outer[step + 1]
                inward_low = (-side * math.cos(low[2]), -math.sin(low[2]), 0.0)
                inward_high = (-side * math.cos(high[2]), -math.sin(high[2]), 0.0)
                self._shaded_quad((inward_low, inward_high, inward_high, inward_low),
                                  ((low[0], low[1], far), (high[0], high[1], far),
                                   (high[0], high[1], near), (low[0], low[1], near)),
                                  (self._arch_shade(low[1]), self._arch_shade(high[1]),
                                   self._arch_shade(high[1]), self._arch_shade(low[1])))
                outward_low = (side * math.cos(low_outer[2]), math.sin(low_outer[2]), 0.0)
                outward_high = (side * math.cos(high_outer[2]), math.sin(high_outer[2]), 0.0)
                self._shaded_quad((outward_low, outward_high, outward_high, outward_low),
                                  ((low_outer[0], low_outer[1], near), (high_outer[0], high_outer[1], near),
                                   (high_outer[0], high_outer[1], far), (low_outer[0], low_outer[1], far)),
                                  (self._arch_shade(low_outer[1]), self._arch_shade(high_outer[1]),
                                   self._arch_shade(high_outer[1]), self._arch_shade(low_outer[1])))
                for face, normal_z in ((near, 1.0), (far, -1.0)):
                    flat = (0.0, 0.0, normal_z)
                    self._shaded_quad((flat,) * 4,
                                      ((low[0], low[1], face), (high[0], high[1], face),
                                       (high_outer[0], high_outer[1], face), (low_outer[0], low_outer[1], face)),
                                      (self._arch_shade(low[1]), self._arch_shade(high[1]),
                                       self._arch_shade(high_outer[1]), self._arch_shade(low_outer[1])))
        glEnd()

    def _corner_boundary(self, side):
        climb = self.ridge - self.wall_top
        roof_run = math.hypot(self.wall_x, climb)
        total = self.wall_top + roof_run
        points = []
        for step in range(self.arch_steps + 1):
            travelled = total * step / self.arch_steps
            if travelled <= self.wall_top:
                points.append((side * self.wall_x, travelled))
            else:
                along = (travelled - self.wall_top) / roof_run
                points.append((side * self.wall_x * (1.0 - along), self.wall_top + climb * along))
        return points

    def _draw_arch_corners(self, center_z):
        radius, center_x = self._arch_geometry()
        glBegin(GL_QUADS)
        for side in (1.0, -1.0):
            arc = self._arch_profile(radius + self.arch_band, center_x, side)
            boundary = self._corner_boundary(side)
            for face, normal_z in ((center_z + self.arch_depth / 2.0, 1.0),
                                   (center_z - self.arch_depth / 2.0, -1.0)):
                flat = (0.0, 0.0, normal_z)
                for step in range(self.arch_steps):
                    corners = ((arc[step][0], arc[step][1], face),
                               (arc[step + 1][0], arc[step + 1][1], face),
                               (boundary[step + 1][0], boundary[step + 1][1], face),
                               (boundary[step][0], boundary[step][1], face))
                    self._shaded_quad((flat,) * 4, corners,
                                      tuple(self._arch_shade(corner[1]) for corner in corners))
        glEnd()

    def _draw_arch_outlines(self, center_z):
        radius, center_x = self._arch_geometry()
        lift = 0.01
        glColor3f(*self.outline_color)
        for side in (1.0, -1.0):
            inner = self._arch_profile(radius, center_x, side)
            boundary = self._corner_boundary(side)
            for face in (center_z + self.arch_depth / 2.0 + lift, center_z - self.arch_depth / 2.0 - lift):
                glBegin(GL_LINE_STRIP)
                for point_x, point_y, angle in inner:
                    glVertex3f(point_x - side * math.cos(angle) * lift, point_y - math.sin(angle) * lift, face)
                glEnd()
                glBegin(GL_LINE_STRIP)
                for point_x, point_y in boundary:
                    glVertex3f(point_x - side * lift, point_y - lift, face)
                glEnd()

    def _stage_columns(self):
        landing_half = self.stage_half_width - self.stage_steps * self.step_run
        columns = [(-landing_half, landing_half, self.stage_base + self.stage_steps * self.step_rise)]
        for step in range(self.stage_steps):
            inner = landing_half + step * self.step_run
            outer = inner + self.step_run
            height = self.stage_base + (self.stage_steps - 1 - step) * self.step_rise
            columns.append((inner, outer, height))
            columns.append((-outer, -inner, height))
        return columns

    def _draw_stage(self):
        back = -self.length / 2.0
        front = back + self.stage_depth
        glColor3f(*self.brick_color)
        glBegin(GL_QUADS)
        for left, right, height in self._stage_columns():
            self._quad((0.0, 0.0, 1.0), ((left, 0.0, front), (right, 0.0, front),
                                         (right, height, front), (left, height, front)))
            self._quad((0.0, 1.0, 0.0), ((left, height, front), (right, height, front),
                                         (right, height, back), (left, height, back)))
            for edge, side in ((left, -1.0), (right, 1.0)):
                self._quad((side, 0.0, 0.0), ((edge, 0.0, front), (edge, 0.0, back),
                                              (edge, height, back), (edge, height, front)))
        glEnd()
        self._draw_side_steps(back, front)

    def _draw_side_steps(self, back, front):
        glColor3f(*self.brick_color)
        glBegin(GL_QUADS)
        flight_width = self.side_step_count * self.side_step_run
        for side in (1.0, -1.0):
            inner = side * self.stage_half_width
            outer = side * (self.stage_half_width + flight_width)
            left, right = min(inner, outer), max(inner, outer)
            for step in range(self.side_step_count):
                height = self.side_step_top * (step + 1) / self.side_step_count
                reach = front + (self.side_step_count - 1 - step) * self.side_step_depth
                self._quad((0.0, 0.0, 1.0), ((left, 0.0, reach), (right, 0.0, reach),
                                             (right, height, reach), (left, height, reach)))
                self._quad((0.0, 1.0, 0.0), ((left, height, reach), (right, height, reach),
                                             (right, height, back), (left, height, back)))
                self._quad((side, 0.0, 0.0), ((outer, 0.0, reach), (outer, 0.0, back),
                                              (outer, height, back), (outer, height, reach)))
        glEnd()

    def _draw_stage_opening(self):
        front = -self.length / 2.0 + self.stage_depth + 0.03
        half = self.opening_width / 2.0
        spring = self.opening_height - half
        glDisable(GL_LIGHTING)
        glColor3f(*self.opening_color)
        glBegin(GL_QUADS)
        glVertex3f(-half, 0.0, front)
        glVertex3f(half, 0.0, front)
        glVertex3f(half, spring, front)
        glVertex3f(-half, spring, front)
        glEnd()
        glBegin(GL_TRIANGLE_FAN)
        glVertex3f(0.0, spring, front)
        for step in range(17):
            angle = math.pi * step / 16
            glVertex3f(half * math.cos(angle), spring + half * math.sin(angle), front)
        glEnd()
        glEnable(GL_LIGHTING)

    def _draw_stage_bricks(self):
        front = -self.length / 2.0 + self.stage_depth + 0.015
        glDisable(GL_LIGHTING)
        glColor3f(*self.mortar_color)
        for left, right, height in self._stage_columns():
            self._draw_brick_lines("z", front, (left, right), height, 1.0)
        glEnable(GL_LIGHTING)

    def _draw_rails(self):
        back = -self.length / 2.0
        rail_z = back + self.stage_depth - 0.15
        landing_half = self.stage_half_width - self.stage_steps * self.step_run
        top = self.stage_base + self.stage_steps * self.step_rise
        glDisable(GL_LIGHTING)
        glColor3f(*self.rail_color)
        glLineWidth(2.0)
        glBegin(GL_LINES)
        for side in (1.0, -1.0):
            start = (side * self.stage_half_width, self.stage_base + self.rail_height, rail_z)
            finish = (side * landing_half, top + self.rail_height, rail_z)
            glVertex3f(*start)
            glVertex3f(*finish)
            for step in range(self.stage_steps + 1):
                along = self.stage_half_width - step * self.step_run
                level = self.stage_base + step * self.step_rise
                glVertex3f(side * along, level, rail_z)
                glVertex3f(side * along, level + self.rail_height, rail_z)
        glVertex3f(-landing_half, top + self.rail_height, rail_z)
        glVertex3f(landing_half, top + self.rail_height, rail_z)
        glEnd()
        glLineWidth(1.0)
        glEnable(GL_LIGHTING)

    def _draw_door(self):
        wall_z = -self.length / 2.0 + 0.02
        base = self.stage_base + self.stage_steps * self.step_rise
        door_width, door_height = self.door_size
        half = door_width / 2.0
        glColor3f(*self.frame_color)
        glBegin(GL_QUADS)
        self._quad((0.0, 0.0, 1.0), ((-half - 0.2, base, wall_z), (half + 0.2, base, wall_z),
                                     (half + 0.2, base + door_height + 0.25, wall_z),
                                     (-half - 0.2, base + door_height + 0.25, wall_z)))
        glColor3f(*self.door_color)
        self._quad((0.0, 0.0, 1.0), ((-half, base, wall_z + 0.02), (half, base, wall_z + 0.02),
                                     (half, base + door_height, wall_z + 0.02),
                                     (-half, base + door_height, wall_z + 0.02)))
        glEnd()

    def _draw_wall_bricks(self):
        half_length = self.length / 2.0
        glDisable(GL_LIGHTING)
        glColor3f(*self.mortar_color)
        for side in (1.0, -1.0):
            self._draw_brick_lines("x", side * (self.wall_x - 0.015), (-half_length, half_length),
                                   self.brick_height, -side)
        for end in (1.0, -1.0):
            self._draw_brick_lines("z", end * (half_length - 0.015), (-self.wall_x, self.wall_x),
                                   self.brick_height, -end)
        glEnable(GL_LIGHTING)

    def _compile(self):
        display_list = glGenLists(1)
        glNewList(display_list, GL_COMPILE)
        self._draw_floor()
        self._draw_side_walls()
        self._draw_end_wall(1.0)
        self._draw_end_wall(-1.0)
        self._draw_roof()
        self._draw_chimney()
        for center_z in self._arch_positions():
            self._draw_arch(center_z)
            self._draw_arch_corners(center_z)
        self._draw_windows()
        self._draw_stage()
        self._draw_door()
        glDisable(GL_LIGHTING)
        self._draw_floor_planks()
        glEnable(GL_LIGHTING)
        self._draw_wall_bricks()
        self._draw_stage_bricks()
        self._draw_stage_opening()
        self._draw_rails()
        glDisable(GL_LIGHTING)
        glLineWidth(self.outline_width)
        for center_z in self._arch_positions():
            self._draw_arch_outlines(center_z)
        glLineWidth(1.0)
        glEnable(GL_LIGHTING)
        glEndList()
        return display_list

    def draw(self):
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        glRotatef(self.facing, 0.0, 1.0, 0.0)
        glScalef(self.size, self.size, self.size)
        glCallList(self.display_list)
        glPopMatrix()
