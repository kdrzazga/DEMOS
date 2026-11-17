import bisect
import math
import random
from contextlib import contextmanager

from OpenGL.GL import *

from lib.vector3 import Vector3

UP = Vector3(0.0, 1.0, 0.0)


class Ruin:

    def __init__(self, size, height, texture=None, seed=None):
        self.width, self.depth = (size, size) if isinstance(size, (int, float)) else size
        self.height = height
        self.texture = texture
        self.random = random.Random(seed)
        self.concrete_color = (0.58, 0.56, 0.52)
        self.color_variation = 0.07
        self.texture_meters = 4.0
        self.display_list = None

    def compile(self):
        self.display_list = glGenLists(1)
        glNewList(self.display_list, GL_COMPILE)
        self.build()
        glEndList()

    def build(self):
        raise NotImplementedError

    def render(self):
        glCallList(self.display_list)

    def varied_concrete(self):
        shift = self.random.uniform(-self.color_variation, self.color_variation)
        return tuple(min(1.0, max(0.0, channel + shift)) for channel in self.concrete_color)

    @contextmanager
    def textured(self):
        if self.texture is None:
            yield
            return
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, self.texture)
        try:
            yield
        finally:
            glBindTexture(GL_TEXTURE_2D, 0)
            glDisable(GL_TEXTURE_2D)

    def texture_point(self, point, normal):
        x, y, z = point
        across_x, across_y, across_z = abs(normal.x), abs(normal.y), abs(normal.z)
        if across_y >= across_x and across_y >= across_z:
            return x / self.texture_meters, z / self.texture_meters
        if across_x >= across_z:
            return z / self.texture_meters, y / self.texture_meters
        return x / self.texture_meters, y / self.texture_meters

    def emit_quad(self, corners, normal, color):
        glColor3f(*color)
        glNormal3f(*normal)
        for corner in corners:
            glTexCoord2f(*self.texture_point(corner, normal))
            glVertex3f(*corner)

    def emit_box(self, low, high, color):
        left, bottom, back = low
        right, top, front = high
        faces = ((Vector3(0.0, 0.0, 1.0), ((left, bottom, front), (right, bottom, front), (right, top, front), (left, top, front))),
                 (Vector3(0.0, 0.0, -1.0), ((right, bottom, back), (left, bottom, back), (left, top, back), (right, top, back))),
                 (Vector3(1.0, 0.0, 0.0), ((right, bottom, front), (right, bottom, back), (right, top, back), (right, top, front))),
                 (Vector3(-1.0, 0.0, 0.0), ((left, bottom, back), (left, bottom, front), (left, top, front), (left, top, back))),
                 (Vector3(0.0, 1.0, 0.0), ((left, top, front), (right, top, front), (right, top, back), (left, top, back))),
                 (Vector3(0.0, -1.0, 0.0), ((left, bottom, back), (right, bottom, back), (right, bottom, front), (left, bottom, front))))
        for normal, corners in faces:
            self.emit_quad([Vector3(*corner) for corner in corners], normal, color)

    def emit_rod(self, start, end, thickness, color):
        direction = (end - start).normalized()
        helper = UP if abs(direction.y) < 0.9 else Vector3(1.0, 0.0, 0.0)
        first_side = direction.cross(helper).normalized() * (thickness / 2.0)
        second_side = direction.cross(first_side).normalized() * (thickness / 2.0)
        rim = (first_side + second_side, first_side - second_side, -first_side - second_side, -first_side + second_side)
        for index in range(4):
            this_corner, next_corner = rim[index], rim[(index + 1) % 4]
            normal = (this_corner + next_corner).normalized()
            self.emit_quad((start + this_corner, start + next_corner, end + next_corner, end + this_corner), normal, color)


class RuinedWall:

    def __init__(self, origin, along, inward, length, thickness):
        self.origin = origin
        self.along = along
        self.inward = inward
        self.length = length
        self.thickness = thickness
        self.profile = []
        self.profile_positions = []
        self.notches = []
        self.windows = []
        self.color = None

    def set_profile(self, profile):
        self.profile = profile
        self.profile_positions = [position for position, _ in profile]

    def top_at(self, position):
        index = min(max(bisect.bisect_right(self.profile_positions, position), 1), len(self.profile) - 1)
        (start, start_level), (end, end_level) = self.profile[index - 1], self.profile[index]
        span = end - start
        if span <= 1e-6:
            return end_level
        return start_level + (end_level - start_level) * (position - start) / span

    def point(self, position, level, depth):
        return self.origin + self.along * position + self.inward * depth + UP * level

    def window_at(self, position, level):
        return any(left < position < right and bottom < level < top for left, right, bottom, top in self.windows)

    def is_solid(self, position, level):
        return (0.05 < position < self.length - 0.05 and 0.0 < level < self.top_at(position) - 0.03
                and not self.window_at(position, level))

    def top_normal(self, start, end):
        slope = (self.top_at(end) - self.top_at(start)) / max(end - start, 1e-6)
        return (UP - self.along * slope).normalized()


class Ruin1(Ruin):

    def __init__(self, size, height, texture=None, seed=None):
        super().__init__(size, height, texture, seed)
        self.wall_thickness = 0.35
        self.floor_height = 3.2
        self.bay_width = 2.8
        self.wall_margin = 0.9
        self.window_width = 1.3
        self.window_height = 1.6
        self.sill_height = 0.9
        self.blown_window_chance = 0.08
        self.blown_window_growth = (0.3, 0.9)
        self.top_segment_span = (0.7, 2.2)
        self.top_wander = min(0.6, height * 0.05)
        self.top_wander_limit = min(2.5, height * 0.15)
        self.collapse_span = (0.08, 0.38)
        self.collapse_waves = (0.6, 1.8)
        self.notch_chance = 0.16
        self.notch_drop = (min(1.5, height * 0.1), min(6.0, height * 0.3))
        self.crack_spacing = 3.0
        self.crack_step = 0.3
        self.crack_steps = (6, 26)
        self.crack_turn = 0.45
        self.crack_spread = 1.1
        self.crack_branch_chance = 0.1
        self.crack_width = 0.08
        self.crack_lift = 0.012
        self.crack_color = (0.11, 0.10, 0.09)
        self.window_crack_chance = 0.18
        self.walls = self.make_walls()
        self.compile()

    def make_walls(self):
        half_width, half_depth, thickness = self.width / 2.0, self.depth / 2.0, self.wall_thickness
        layouts = ((Vector3(-half_width, 0.0, half_depth), Vector3(1.0, 0.0, 0.0), Vector3(0.0, 0.0, -1.0), self.width),
                   (Vector3(half_width, 0.0, -half_depth), Vector3(-1.0, 0.0, 0.0), Vector3(0.0, 0.0, 1.0), self.width),
                   (Vector3(half_width, 0.0, half_depth - thickness), Vector3(0.0, 0.0, -1.0), Vector3(-1.0, 0.0, 0.0),
                    self.depth - 2.0 * thickness),
                   (Vector3(-half_width, 0.0, -half_depth + thickness), Vector3(0.0, 0.0, 1.0), Vector3(1.0, 0.0, 0.0),
                    self.depth - 2.0 * thickness))
        walls = []
        for origin, along, inward, length in layouts:
            wall = RuinedWall(origin, along, inward, length, thickness)
            wall.color = self.varied_concrete()
            self.shape_top(wall)
            self.cut_windows(wall)
            walls.append(wall)
        return walls

    def shape_top(self, wall):
        collapse = self.random.uniform(*self.collapse_span)
        waves = self.random.uniform(*self.collapse_waves)
        phase = self.random.uniform(0.0, 2.0 * math.pi)
        wander = 0.0
        position = 0.0
        profile = []
        while True:
            broad = self.height * (1.0 - collapse * (0.5 + 0.5 * math.sin(position / wall.length * math.pi * waves + phase)))
            level = broad + wander
            if 0.0 < position < wall.length and self.random.random() < self.notch_chance:
                level -= self.random.uniform(*self.notch_drop)
                wall.notches.append(position)
            profile.append((position, min(self.height, max(self.floor_height * 0.5, level))))
            if position >= wall.length:
                break
            wander = max(-self.top_wander_limit, min(self.top_wander_limit, wander + self.random.gauss(0.0, self.top_wander)))
            position = min(wall.length, position + self.random.uniform(*self.top_segment_span))
        wall.set_profile(profile)

    def cut_windows(self, wall):
        bay_count = max(1, int((wall.length - 2.0 * self.wall_margin) / self.bay_width))
        bay_span = (wall.length - 2.0 * self.wall_margin) / bay_count
        floor_count = int(self.height / self.floor_height) + 1
        for floor in range(floor_count):
            bottom = floor * self.floor_height + self.sill_height
            for bay in range(bay_count):
                center = self.wall_margin + bay_span * (bay + 0.5)
                half_width, height = self.window_width / 2.0, self.window_height
                if self.random.random() < self.blown_window_chance:
                    half_width = min(bay_span / 2.0 - 0.2, half_width + self.random.uniform(*self.blown_window_growth) / 2.0)
                    height = min(self.floor_height - 0.5, height + self.random.uniform(*self.blown_window_growth))
                left, right = center - half_width, center + half_width
                if bottom < min(wall.top_at(left), wall.top_at(right)) - 0.3:
                    wall.windows.append((left, right, bottom, bottom + height))

    def build(self):
        with self.textured():
            glBegin(GL_QUADS)
            for wall in self.walls:
                self.emit_wall(wall)
            glEnd()
        glBegin(GL_QUADS)
        for wall in self.walls:
            for path in self.crack_paths(wall):
                self.emit_crack(wall, path)
        glEnd()

    def column_edges(self, wall):
        edges = set(wall.profile_positions)
        for left, right, _, _ in wall.windows:
            edges.update((left, right))
        return sorted(edges)

    def solid_spans(self, wall, middle):
        holes = sorted((bottom, top) for left, right, bottom, top in wall.windows if left < middle < right)
        spans = []
        start = 0.0
        for bottom, top in holes:
            if bottom > start:
                spans.append((start, bottom))
            start = top
        spans.append((start, math.inf))
        return spans

    def emit_wall(self, wall):
        outer_normal, inner_normal = -wall.inward, wall.inward
        thickness = wall.thickness
        edges = self.column_edges(wall)
        for left, right in zip(edges, edges[1:]):
            if right - left < 1e-4:
                continue
            left_top, right_top = wall.top_at(left), wall.top_at(right)
            for bottom, top in self.solid_spans(wall, (left + right) / 2.0):
                left_end, right_end = min(top, left_top), min(top, right_top)
                if left_end <= bottom and right_end <= bottom:
                    continue
                left_end, right_end = max(left_end, bottom), max(right_end, bottom)
                face = ((left, bottom), (right, bottom), (right, right_end), (left, left_end))
                self.emit_quad([wall.point(u, v, 0.0) for u, v in face], outer_normal, wall.color)
                self.emit_quad([wall.point(u, v, thickness) for u, v in face], inner_normal, wall.color)
                if top > min(left_top, right_top):
                    cap = (wall.point(left, left_end, 0.0), wall.point(right, right_end, 0.0),
                           wall.point(right, right_end, thickness), wall.point(left, left_end, thickness))
                    self.emit_quad(cap, wall.top_normal(left, right), wall.color)
        self.emit_window_reveals(wall)
        self.emit_wall_ends(wall)

    def emit_window_reveals(self, wall):
        thickness = wall.thickness
        for left, right, bottom, top in wall.windows:
            for side, normal in ((left, wall.along), (right, -wall.along)):
                side_top = min(top, wall.top_at(side))
                if side_top > bottom:
                    jamb = (wall.point(side, bottom, 0.0), wall.point(side, side_top, 0.0),
                            wall.point(side, side_top, thickness), wall.point(side, bottom, thickness))
                    self.emit_quad(jamb, normal, wall.color)
            lowest_top = min(wall.top_at(left), wall.top_at(right))
            if lowest_top > bottom:
                sill = (wall.point(left, bottom, 0.0), wall.point(right, bottom, 0.0),
                        wall.point(right, bottom, thickness), wall.point(left, bottom, thickness))
                self.emit_quad(sill, UP, wall.color)
            if lowest_top > top:
                lintel = (wall.point(left, top, 0.0), wall.point(right, top, 0.0),
                          wall.point(right, top, thickness), wall.point(left, top, thickness))
                self.emit_quad(lintel, -UP, wall.color)

    def emit_wall_ends(self, wall):
        for position, normal in ((0.0, -wall.along), (wall.length, wall.along)):
            level = wall.top_at(position)
            end = (wall.point(position, 0.0, 0.0), wall.point(position, level, 0.0),
                   wall.point(position, level, wall.thickness), wall.point(position, 0.0, wall.thickness))
            self.emit_quad(end, normal, wall.color)

    def crack_starts(self, wall):
        starts = [(position, wall.top_at(position) - 0.05, 0.0) for position in wall.notches]
        for _ in range(int(wall.length / self.crack_spacing) + 1):
            position = self.random.uniform(0.3, wall.length - 0.3)
            starts.append((position, wall.top_at(position) - 0.05, 0.0))
        for left, right, bottom, top in wall.windows:
            if self.random.random() < self.window_crack_chance:
                corner = self.random.choice(((left - 0.05, bottom - 0.05, 0.0), (right + 0.05, bottom - 0.05, 0.0),
                                             (left - 0.05, top + 0.05, math.pi), (right + 0.05, top + 0.05, math.pi)))
                starts.append(corner)
        return starts

    def crack_paths(self, wall):
        paths = []
        for position, level, heading in self.crack_starts(wall):
            heading += self.random.uniform(-0.5, 0.5)
            self.grow_crack(wall, position, level, heading, self.random.randint(*self.crack_steps), paths)
        return paths

    def grow_crack(self, wall, position, level, heading, steps, paths):
        if not wall.is_solid(position, level):
            return
        base_heading = heading
        path = [(position, level)]
        for _ in range(steps):
            heading += self.random.uniform(-self.crack_turn, self.crack_turn)
            heading = max(base_heading - self.crack_spread, min(base_heading + self.crack_spread, heading))
            position += math.sin(heading) * self.crack_step
            level -= math.cos(heading) * self.crack_step
            if not wall.is_solid(position, level):
                break
            path.append((position, level))
            if self.random.random() < self.crack_branch_chance:
                branch_heading = heading + self.random.choice((-1.0, 1.0)) * self.random.uniform(0.5, 0.9)
                self.grow_crack(wall, position, level, branch_heading, steps // 2, paths)
        if len(path) > 1:
            paths.append(path)

    def emit_crack(self, wall, path):
        count = len(path)
        for index in range(count - 1):
            (start_u, start_v), (end_u, end_v) = path[index], path[index + 1]
            step_u, step_v = end_u - start_u, end_v - start_v
            step_length = math.hypot(step_u, step_v) or 1.0
            across_u, across_v = -step_v / step_length, step_u / step_length
            start_half = self.crack_width * (1.0 - 0.8 * index / count) / 2.0
            end_half = self.crack_width * (1.0 - 0.8 * (index + 1) / count) / 2.0
            ribbon = ((start_u - across_u * start_half, start_v - across_v * start_half),
                      (end_u - across_u * end_half, end_v - across_v * end_half),
                      (end_u + across_u * end_half, end_v + across_v * end_half),
                      (start_u + across_u * start_half, start_v + across_v * start_half))
            for depth, normal in ((-self.crack_lift, -wall.inward), (wall.thickness + self.crack_lift, wall.inward)):
                self.emit_quad([wall.point(u, v, depth) for u, v in ribbon], normal, self.crack_color)


class Ruin2(Ruin):

    def __init__(self, size, height, texture=None, seed=None):
        super().__init__(size, height, texture, seed)
        self.floor_height = 3.6
        self.bay_target = 5.0
        self.column_size = 0.5
        self.beam_height = 0.55
        self.beam_width = 0.4
        self.collapse_span = (0.15, 0.45)
        self.column_wander = 0.6
        self.broken_column_chance = 0.65
        self.broken_column_part = (0.15, 0.75)
        self.fallen_beam_chance = 0.08
        self.stub_reach = (0.2, 0.55)
        self.rebar_color = (0.30, 0.17, 0.10)
        self.rebar_thickness = 0.035
        self.rebar_length = (0.4, 1.3)
        self.rebar_bend = 0.35
        self.floor_count = max(1, int(height / self.floor_height))
        self.columns_x = self.column_line(self.width)
        self.columns_z = self.column_line(self.depth)
        self.column_tops = self.make_column_tops()
        self.broken_ends = []
        self.compile()

    def column_line(self, span):
        count = max(2, round(span / self.bay_target) + 1)
        start = -span / 2.0 + self.column_size / 2.0
        step = (span - self.column_size) / (count - 1)
        return [start + step * index for index in range(count)]

    def make_column_tops(self):
        collapse = self.random.uniform(*self.collapse_span)
        waves_x, waves_z = self.random.uniform(0.5, 1.5), self.random.uniform(0.5, 1.5)
        phase_x, phase_z = self.random.uniform(0.0, 2.0 * math.pi), self.random.uniform(0.0, 2.0 * math.pi)
        tops = {}
        for column_x, x in enumerate(self.columns_x):
            for column_z, z in enumerate(self.columns_z):
                shape = (0.5 + 0.25 * math.sin(x / self.width * math.pi * waves_x + phase_x)
                         + 0.25 * math.sin(z / self.depth * math.pi * waves_z + phase_z))
                floors = self.floor_count * (1.0 - collapse * shape) + self.random.gauss(0.0, self.column_wander)
                floors = max(1, min(self.floor_count, round(floors)))
                top = floors * self.floor_height
                if floors < self.floor_count and self.random.random() < self.broken_column_chance:
                    top += self.random.uniform(*self.broken_column_part) * self.floor_height
                tops[(column_x, column_z)] = top
        return tops

    def build(self):
        with self.textured():
            glBegin(GL_QUADS)
            self.emit_columns()
            self.emit_beams()
            glEnd()
        glBegin(GL_QUADS)
        self.emit_rebar()
        glEnd()

    def emit_columns(self):
        half = self.column_size / 2.0
        for (column_x, column_z), top in self.column_tops.items():
            x, z = self.columns_x[column_x], self.columns_z[column_z]
            self.emit_box((x - half, 0.0, z - half), (x + half, top, z + half), self.varied_concrete())
            self.broken_ends.append((Vector3(x, top, z), UP, half))

    def neighbour_pairs(self):
        for column_x in range(len(self.columns_x)):
            for column_z in range(len(self.columns_z)):
                if column_x + 1 < len(self.columns_x):
                    yield (column_x, column_z), (column_x + 1, column_z)
                if column_z + 1 < len(self.columns_z):
                    yield (column_x, column_z), (column_x, column_z + 1)

    def column_center(self, column):
        return Vector3(self.columns_x[column[0]], 0.0, self.columns_z[column[1]])

    def emit_beams(self):
        half_column = self.column_size / 2.0
        for first, second in self.neighbour_pairs():
            start, end = self.column_center(first), self.column_center(second)
            direction = (end - start).normalized()
            span = (end - start).length() - self.column_size
            for floor in range(1, self.floor_count + 1):
                level = floor * self.floor_height
                first_holds = self.column_tops[first] >= level
                second_holds = self.column_tops[second] >= level
                if not (first_holds or second_holds) or self.random.random() < self.fallen_beam_chance:
                    continue
                if first_holds and second_holds:
                    self.emit_beam(start + direction * half_column, span, direction, level)
                    continue
                anchor, toward = (start, direction) if first_holds else (end, -direction)
                reach = span * self.random.uniform(*self.stub_reach)
                self.emit_beam(anchor + toward * half_column, reach, toward, level)
                broken_end = anchor + toward * (half_column + reach) + UP * (level - self.beam_height / 2.0)
                self.broken_ends.append((broken_end, toward, self.beam_width / 2.0))

    def emit_beam(self, start, length, direction, level):
        end = start + direction * length
        half_width = self.beam_width / 2.0
        low = Vector3(min(start.x, end.x) - (half_width if direction.x == 0.0 else 0.0), level - self.beam_height,
                      min(start.z, end.z) - (half_width if direction.z == 0.0 else 0.0))
        high = Vector3(max(start.x, end.x) + (half_width if direction.x == 0.0 else 0.0), level,
                       max(start.z, end.z) + (half_width if direction.z == 0.0 else 0.0))
        self.emit_box(low, high, self.varied_concrete())

    def emit_rebar(self):
        for center, direction, half in self.broken_ends:
            helper = UP if abs(direction.y) < 0.9 else Vector3(1.0, 0.0, 0.0)
            first_side = direction.cross(helper).normalized()
            second_side = direction.cross(first_side).normalized()
            for side_sign, other_sign in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
                root = center + first_side * (side_sign * half * 0.7) + second_side * (other_sign * half * 0.7)
                length = self.random.uniform(*self.rebar_length)
                bend = (first_side * self.random.uniform(-1.0, 1.0) + second_side * self.random.uniform(-1.0, 1.0)
                        - UP * self.random.uniform(0.0, 0.6)) * self.rebar_bend
                middle = root + direction * (length * 0.5)
                tip = middle + (direction + bend).normalized() * (length * 0.5)
                self.emit_rod(root - direction * 0.05, middle, self.rebar_thickness, self.rebar_color)
                self.emit_rod(middle, tip, self.rebar_thickness, self.rebar_color)
