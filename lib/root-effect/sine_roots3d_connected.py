import math

from OpenGL.GL import *

from sine_roots3d import SineRoots3D


class SineConnection:
    def __init__(self, random):
        self.amplitude = random.uniform(0.25, 0.6)
        self.wavelength = random.uniform(2.0, 3.5)
        self.phase = random.uniform(0.0, 2 * math.pi)
        self.phase_speed = random.uniform(0.8, 1.6) * random.choice((-1.0, 1.0))
        self.thickness = random.uniform(0.14, 0.24)
        self.sample_spacing = 0.12
        self.height_above_floor = 0.0

    def advance(self, delta_seconds):
        self.phase += self.phase_speed * delta_seconds

    def centre_line(self, start, end):
        start_x, start_z = start
        end_x, end_z = end
        length = math.hypot(end_x - start_x, end_z - start_z)
        direction_x, direction_z = (end_x - start_x) / length, (end_z - start_z) / length
        sample_count = max(8, int(length / self.sample_spacing))
        points = []
        for index in range(sample_count + 1):
            progress = index / sample_count
            distance = progress * length
            envelope = math.sin(math.pi * progress)
            sway = self.amplitude * envelope * math.sin(2 * math.pi * distance / self.wavelength + self.phase)
            points.append((start_x + direction_x * distance - direction_z * sway,
                           start_z + direction_z * distance + direction_x * sway))
        return points

    @staticmethod
    def side_normals(points):
        normals = []
        for index in range(len(points)):
            before_x, before_z = points[max(index - 1, 0)]
            after_x, after_z = points[min(index + 1, len(points) - 1)]
            tangent_x, tangent_z = after_x - before_x, after_z - before_z
            tangent_length = math.hypot(tangent_x, tangent_z) or 1.0
            normals.append((-tangent_z / tangent_length, tangent_x / tangent_length))
        return normals

    def draw_half(self, points, normals, color, side):
        half_width = self.thickness / 2
        glBegin(GL_QUAD_STRIP)
        for (x, z), (normal_x, normal_z) in zip(points, normals):
            glColor4f(*color, 1.0)
            glVertex3f(x, self.height_above_floor, z)
            glColor4f(*color, 0.0)
            glVertex3f(x + normal_x * half_width * side, self.height_above_floor, z + normal_z * half_width * side)
        glEnd()

    def draw(self, start, end, color):
        if start == end:
            return
        points = self.centre_line(start, end)
        normals = self.side_normals(points)
        self.draw_half(points, normals, color, 1.0)
        self.draw_half(points, normals, color, -1.0)


class ConnectedSineRoots3D(SineRoots3D):
    def __init__(self, seed=None):
        super().__init__(seed)
        self.neighbours_per_patch = 2
        self.longest_connection = 9.0
        self.connection_color = (0.09, 0.08, 0.08)
        self.are_connections_visible = True
        self.connections_appear_at_seconds = 5.0
        self.blink_period_seconds = 7.0
        self.blink_off_seconds = 2.0
        self.elapsed_seconds = 0.0
        self.connections = {}

    def restart(self):
        super().restart()
        self.elapsed_seconds = 0.0

    def set_root_color(self, color):
        super().set_root_color(color)
        self.connection_color = tuple(channel / 255 for channel in color)

    def is_connection_time(self):
        seconds_since_appearing = self.elapsed_seconds - self.connections_appear_at_seconds
        if seconds_since_appearing < 0.0:
            return False
        seconds_into_period = seconds_since_appearing % self.blink_period_seconds
        return seconds_into_period < self.blink_period_seconds - self.blink_off_seconds

    def toggle_connections(self):
        self.are_connections_visible = not self.are_connections_visible

    def connection_between(self, first, second):
        key = (min(id(first), id(second)), max(id(first), id(second)))
        if key not in self.connections:
            self.connections[key] = SineConnection(self.random)
        return self.connections[key]

    def connected_pairs(self):
        patches = self.field.patches
        pairs = {}
        for patch in patches:
            nearby = []
            for other in patches:
                if other is patch:
                    continue
                distance = math.hypot(other.x - patch.x, other.z - patch.z)
                if distance <= self.longest_connection:
                    nearby.append((distance, other))
            nearby.sort(key=lambda entry: entry[0])
            for _, other in nearby[:self.neighbours_per_patch]:
                first, second = sorted((patch, other), key=id)
                pairs[(id(first), id(second))] = (first, second)
        return pairs.values()

    def update(self, delta_seconds):
        super().update(delta_seconds)
        self.elapsed_seconds += delta_seconds
        for connection in self.connections.values():
            connection.advance(delta_seconds)

    def draw_connections(self):
        glPushAttrib(GL_ENABLE_BIT | GL_CURRENT_BIT)
        glDisable(GL_TEXTURE_2D)
        for first, second in self.connected_pairs():
            connection = self.connection_between(first, second)
            connection.draw((first.x, first.z), (second.x, second.z), self.connection_color)
        glPopAttrib()
        glColor4f(1.0, 1.0, 1.0, 1.0)

    def draw_scene(self):
        if self.are_connections_visible and self.is_connection_time():
            self.draw_connections()
        super().draw_scene()
