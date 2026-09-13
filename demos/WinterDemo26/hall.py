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

        self.stage_half_width = 4.6
        self.stage_depth = 1.8
        self.stage_base = 2.2
        self.stage_steps = 5
        self.step_rise = 0.42
        self.step_run = 0.6
        self.opening_width = 3.2
        self.opening_height = 2.7
        self.door_size = (1.1, 2.0)
        self.side_step_count = 3
        self.rail_height = 0.9

        self.plaster_color = (0.60, 0.58, 0.56)
        self.ceiling_color = (0.54, 0.52, 0.52)
        self.brick_color = (0.42, 0.16, 0.11)
        self.mortar_color = (0.46, 0.40, 0.36)
        self.glass_color = (0.55, 0.62, 0.66)
        self.frame_color = (0.62, 0.62, 0.62)
        self.floor_color = (0.40, 0.28, 0.18)
        self.plank_color = (0.24, 0.16, 0.10)
        self.opening_color = (0.05, 0.04, 0.04)
        self.door_color = (0.50, 0.50, 0.48)
        self.rail_color = (0.18, 0.18, 0.20)

        self.wall_x = self.half_span + self.arch_band
        self.display_list = self._compile()

    def _quad(self, normal, corners):
        glNormal3f(*normal)
        for corner in corners:
            glVertex3f(*corner)

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
            glColor3f(*self.plaster_color)
            self._quad(normal, ((wall, self.brick_height, -half_length), (wall, self.brick_height, half_length),
                                (wall, self.wall_top, half_length), (wall, self.wall_top, -half_length)))
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
        glColor3f(*self.plaster_color)
        self._quad(normal, ((-self.wall_x, self.brick_height, wall_z), (self.wall_x, self.brick_height, wall_z),
                            (self.wall_x, self.wall_top, wall_z), (-self.wall_x, self.wall_top, wall_z)))
        glEnd()
        glBegin(GL_TRIANGLES)
        self._quad(normal, ((-self.wall_x, self.wall_top, wall_z), (self.wall_x, self.wall_top, wall_z),
                            (0.0, self.ridge, wall_z)))
        glEnd()

    def _draw_roof(self):
        half_length = self.length / 2.0
        climb = self.ridge - self.wall_top
        slope = math.hypot(climb, self.wall_x)
        glColor3f(*self.ceiling_color)
        glBegin(GL_QUADS)
        for side in (1.0, -1.0):
            normal = (-side * climb / slope, -self.wall_x / slope, 0.0)
            self._quad(normal, ((side * self.wall_x, self.wall_top, -half_length),
                                (0.0, self.ridge, -half_length),
                                (0.0, self.ridge, half_length),
                                (side * self.wall_x, self.wall_top, half_length)))
        glEnd()

    def _arch_profile(self, radius, center_x, side):
        finish = math.acos(-center_x / radius)
        points = []
        for step in range(self.arch_steps + 1):
            angle = finish * step / self.arch_steps
            points.append((side * (center_x + radius * math.cos(angle)), radius * math.sin(angle), angle))
        return points

    def _draw_arch(self, center_z):
        span = self.half_span
        radius = (self.arch_rise ** 2 + span ** 2) / (2.0 * span)
        center_x = span - radius
        near = center_z + self.arch_depth / 2.0
        far = center_z - self.arch_depth / 2.0
        glColor3f(*self.plaster_color)
        glBegin(GL_QUADS)
        for side in (1.0, -1.0):
            inner = self._arch_profile(radius, center_x, side)
            outer = self._arch_profile(radius + self.arch_band, center_x, side)
            for step in range(self.arch_steps):
                low, high = inner[step], inner[step + 1]
                middle = (low[2] + high[2]) / 2.0
                self._quad((-side * math.cos(middle), -math.sin(middle), 0.0),
                           ((low[0], low[1], far), (high[0], high[1], far),
                            (high[0], high[1], near), (low[0], low[1], near)))
                low_outer, high_outer = outer[step], outer[step + 1]
                middle = (low_outer[2] + high_outer[2]) / 2.0
                self._quad((side * math.cos(middle), math.sin(middle), 0.0),
                           ((low_outer[0], low_outer[1], near), (high_outer[0], high_outer[1], near),
                            (high_outer[0], high_outer[1], far), (low_outer[0], low_outer[1], far)))
                for face, normal_z in ((near, 1.0), (far, -1.0)):
                    self._quad((0.0, 0.0, normal_z),
                               ((low[0], low[1], face), (high[0], high[1], face),
                                (high_outer[0], high_outer[1], face), (low_outer[0], low_outer[1], face)))
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
        for side in (1.0, -1.0):
            for step in range(self.side_step_count):
                inner = self.stage_half_width + step * self.step_run
                outer = inner + self.step_run
                height = self.stage_base * (self.side_step_count - step) / (self.side_step_count + 1)
                left, right = (inner, outer) if side > 0.0 else (-outer, -inner)
                reach = front - step * 0.1
                self._quad((0.0, 0.0, 1.0), ((left, 0.0, reach), (right, 0.0, reach),
                                             (right, height, reach), (left, height, reach)))
                self._quad((0.0, 1.0, 0.0), ((left, height, reach), (right, height, reach),
                                             (right, height, back), (left, height, back)))
                edge = right if side > 0.0 else left
                self._quad((side, 0.0, 0.0), ((edge, 0.0, reach), (edge, 0.0, back),
                                              (edge, height, back), (edge, height, reach)))
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
            glVertex3f(side * landing_half, top + self.rail_height, rail_z)
            glVertex3f(0.0, top + self.rail_height, back + 0.2)
            for step in range(self.stage_steps + 1):
                along = self.stage_half_width - step * self.step_run
                level = self.stage_base + step * self.step_rise
                glVertex3f(side * along, level, rail_z)
                glVertex3f(side * along, level + self.rail_height, rail_z)
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
        for center_z in self._arch_positions():
            self._draw_arch(center_z)
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
        glEndList()
        return display_list

    def draw(self):
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        glRotatef(self.facing, 0.0, 1.0, 0.0)
        glScalef(self.size, self.size, self.size)
        glCallList(self.display_list)
        glPopMatrix()
