import math

import numpy
from OpenGL.GL import (
    GL_BLEND,
    GL_COLOR_ARRAY,
    GL_COLOR_BUFFER_BIT,
    GL_COMPILE,
    GL_DEPTH_BUFFER_BIT,
    GL_ENABLE_BIT,
    GL_FALSE,
    GL_FLOAT,
    GL_LIGHTING,
    GL_ONE_MINUS_SRC_ALPHA,
    GL_QUADS,
    GL_SRC_ALPHA,
    GL_TEXTURE_2D,
    GL_TEXTURE_COORD_ARRAY,
    GL_VERTEX_ARRAY,
    glBegin,
    glBlendFunc,
    glCallList,
    glColor4f,
    glColorPointer,
    glDepthMask,
    glDisable,
    glDisableClientState,
    glDrawArrays,
    glEnable,
    glEnableClientState,
    glEnd,
    glEndList,
    glGenLists,
    glNewList,
    glNormal3f,
    glPopAttrib,
    glPopMatrix,
    glPushAttrib,
    glPushMatrix,
    glRotatef,
    glTexCoordPointer,
    glTranslatef,
    glVertex3f,
    glVertexPointer,
)

from lib.vector3 import Vector3


class CompiledShape:

    def __init__(self, emit):
        self.list_id = glGenLists(1)
        glNewList(self.list_id, GL_COMPILE)
        emit()
        glEndList()

    def call(self):
        glCallList(self.list_id)


class WetStreet:

    def __init__(self, palette, left, right, near, far):
        self.palette = palette
        self.left = left
        self.right = right
        self.near = near
        self.far = far
        self.cell_size = 4.0
        self.stripe_color = (0.75, 0.8, 0.78, 0.35)
        self.crossings = []
        self.surface = None
        self.markings = None

    def add_crossing(self, center_x, center_z, length, along_x):
        self.crossings.append((center_x, center_z, length, along_x))

    def prepare(self):
        self.surface = CompiledShape(self._emit_surface)
        self.markings = CompiledShape(self._emit_markings)

    def draw(self):
        glPushAttrib(GL_ENABLE_BIT | GL_COLOR_BUFFER_BIT)
        glDisable(GL_LIGHTING)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        self.surface.call()
        self.markings.call()
        glPopAttrib()

    def _emit_surface(self):
        glColor4f(*self.palette.asphalt)
        glNormal3f(0.0, 1.0, 0.0)
        glBegin(GL_QUADS)
        x = self.left
        while x < self.right:
            z = self.far
            while z < self.near:
                glVertex3f(x, 0.0, z + self.cell_size)
                glVertex3f(x + self.cell_size, 0.0, z + self.cell_size)
                glVertex3f(x + self.cell_size, 0.0, z)
                glVertex3f(x, 0.0, z)
                z += self.cell_size
            x += self.cell_size
        glEnd()

    def _emit_markings(self):
        glColor4f(*self.stripe_color)
        stripe_width = 0.5
        stripe_gap = 0.6
        lift = 0.02
        glBegin(GL_QUADS)
        for center_x, center_z, length, along_x in self.crossings:
            stripes = int(length / (stripe_width + stripe_gap))
            start = -length / 2.0
            for index in range(stripes):
                offset = start + index * (stripe_width + stripe_gap)
                if along_x:
                    corners = ((center_x + offset, center_z - 2.0), (center_x + offset + stripe_width, center_z - 2.0),
                               (center_x + offset + stripe_width, center_z + 2.0), (center_x + offset, center_z + 2.0))
                else:
                    corners = ((center_x - 2.0, center_z + offset), (center_x + 2.0, center_z + offset),
                               (center_x + 2.0, center_z + offset + stripe_width), (center_x - 2.0, center_z + offset + stripe_width))
                for corner_x, corner_z in corners:
                    glVertex3f(corner_x, lift, corner_z)
        glEnd()


class StreetLamps:

    def __init__(self, palette):
        self.palette = palette
        self.lamps = []
        self.pole_height = 7.5
        self.arm_reach = 2.2
        self.pole_color = (0.06, 0.07, 0.07)
        self.glow_size = 1.6
        self.body = None

    def add(self, base, arm_direction):
        self.lamps.append((base, arm_direction))

    def lamp_heads(self):
        return [base + arm * self.arm_reach + Vector3(0.0, self.pole_height, 0.0) for base, arm in self.lamps]

    def glow_arrays(self):
        heads = self.lamp_heads()
        tint = (*self.palette.street_lamp, 0.9)
        return [tuple(head) for head in heads], [self.glow_size] * len(heads), [tint] * len(heads)

    def prepare(self, shapes):
        self.body = CompiledShape(lambda: self._emit(shapes))

    def draw(self):
        self.body.call()

    def _emit(self, shapes):
        for base, arm in self.lamps:
            shapes.box(base.x - 0.09, 0.0, base.z - 0.09, base.x + 0.09, self.pole_height, base.z + 0.09, self.pole_color)
            tip = base + arm * self.arm_reach
            shapes.box(min(base.x, tip.x) - 0.06, self.pole_height - 0.12, min(base.z, tip.z) - 0.06,
                       max(base.x, tip.x) + 0.06, self.pole_height, max(base.z, tip.z) + 0.06, self.pole_color)


class CarModel:

    def __init__(self, body_color, is_taxi):
        self.body_color = body_color
        self.is_taxi = is_taxi
        self.length = 4.4
        self.width = 1.8
        self.cabin_color = (0.05, 0.07, 0.08)
        self.wheel_color = (0.02, 0.02, 0.02)
        self.roof_sign_color = (1.0, 0.95, 0.7)
        self.shape = None

    def prepare(self, shapes):
        self.shape = CompiledShape(lambda: self._emit(shapes))

    def _emit(self, shapes):
        half_length = self.length / 2.0
        half_width = self.width / 2.0
        shapes.box(-half_length, 0.35, -half_width, half_length, 1.05, half_width, self.body_color)
        shapes.box(-1.2, 1.05, -half_width + 0.12, 1.0, 1.6, half_width - 0.12, self.cabin_color)
        for wheel_x in (-1.4, 1.4):
            for wheel_z in (-half_width, half_width - 0.25):
                shapes.box(wheel_x - 0.35, 0.0, wheel_z, wheel_x + 0.35, 0.65, wheel_z + 0.25, self.wheel_color)
        if self.is_taxi:
            shapes.box(-0.35, 1.6, -0.3, 0.35, 1.85, 0.3, self.roof_sign_color)

    def call(self):
        self.shape.call()


class Lane:

    def __init__(self, start, end):
        self.start = start
        self.end = end
        self.length = (end - start).length()
        self.direction = (end - start).normalized()
        self.heading_degrees = math.degrees(math.atan2(-self.direction.z, self.direction.x))

    def point_at(self, distance):
        return self.start + self.direction * (distance % self.length)


class Car:

    def __init__(self, model, lane, distance, speed):
        self.model = model
        self.lane = lane
        self.distance = distance
        self.speed = speed
        self.headlight_spots = ((2.2, 0.75, 0.6), (2.2, 0.75, -0.6))
        self.taillight_spots = ((-2.22, 0.8, 0.65), (-2.22, 0.8, -0.65))

    def update(self, seconds):
        self.distance += self.speed * seconds

    def position(self):
        return self.lane.point_at(self.distance)

    def draw(self):
        position = self.position()
        glPushMatrix()
        glTranslatef(*position)
        glRotatef(self.lane.heading_degrees, 0.0, 1.0, 0.0)
        self.model.call()
        glPopMatrix()

    def light_points(self):
        position = self.position()
        forward = self.lane.direction
        side = Vector3(-forward.z, 0.0, forward.x)
        heads = [position + forward * along + Vector3(0.0, rise, 0.0) + side * across
                 for along, rise, across in self.headlight_spots]
        tails = [position + forward * along + Vector3(0.0, rise, 0.0) + side * across
                 for along, rise, across in self.taillight_spots]
        return heads, tails


class Traffic:

    def __init__(self, palette, randomness):
        self.palette = palette
        self.randomness = randomness
        self.models = [CarModel(color, index < 2) for index, color in enumerate(palette.car_bodies)]
        self.cars = []
        self.headlight_size = 0.9
        self.taillight_size = 0.55
        self.speed_range = (6.0, 11.0)

    def add_lane(self, lane, car_count):
        spacing = lane.length / car_count
        for index in range(car_count):
            distance = index * spacing + self.randomness.uniform(0.0, spacing * 0.5)
            self.cars.append(Car(self.randomness.choice(self.models), lane, distance,
                                 self.randomness.uniform(*self.speed_range)))

    def prepare(self, shapes):
        for model in self.models:
            model.prepare(shapes)

    def update(self, seconds):
        for car in self.cars:
            car.update(seconds)

    def draw(self):
        for car in self.cars:
            car.draw()

    def glow_arrays(self):
        centers = []
        sizes = []
        tints = []
        for car in self.cars:
            heads, tails = car.light_points()
            for point in heads:
                centers.append(tuple(point))
                sizes.append(self.headlight_size)
                tints.append((*self.palette.headlight, 1.0))
            for point in tails:
                centers.append(tuple(point))
                sizes.append(self.taillight_size)
                tints.append((*self.palette.taillight, 1.0))
        return centers, sizes, tints


class CrowdArea:

    def __init__(self, left, right, near, far):
        self.left = left
        self.right = right
        self.near = near
        self.far = far


class Crowd:

    def __init__(self, areas, people_per_area, walker_regions, randomness):
        self.areas = areas
        self.walker_regions = walker_regions
        self.height_range = (1.55, 1.9)
        self.width_ratio = 0.5
        self.speed_range = (0.4, 1.3)
        self.dark_tints = ((0.05, 0.05, 0.06), (0.09, 0.08, 0.08), (0.12, 0.12, 0.11), (0.06, 0.09, 0.09))
        self.bright_tints = ((0.5, 0.12, 0.15), (0.12, 0.45, 0.45), (0.55, 0.5, 0.2))
        self.bright_chance = 0.12
        self.opacity = 0.82
        rows = []
        for area_index, area in enumerate(areas):
            for _ in range(people_per_area):
                rows.append(self._person(area_index, area, randomness))
        self.positions = numpy.array([row[0] for row in rows], dtype=numpy.float32)
        self.velocities = numpy.array([row[1] for row in rows], dtype=numpy.float32)
        self.heights = numpy.array([row[2] for row in rows], dtype=numpy.float32)
        self.area_index = numpy.array([row[3] for row in rows], dtype=numpy.int32)
        texture_rows = [walker_regions[randomness.randrange(len(walker_regions))].corners() for _ in rows]
        self.texture_corners = numpy.array(texture_rows, dtype=numpy.float32).reshape(-1, 2)
        self.colors = numpy.repeat(numpy.array([row[4] for row in rows], dtype=numpy.float32), 4, axis=0)
        self.lows = numpy.array([[areas[index].left, areas[index].far] for index in self.area_index], dtype=numpy.float32)
        self.highs = numpy.array([[areas[index].right, areas[index].near] for index in self.area_index], dtype=numpy.float32)

    def _person(self, area_index, area, randomness):
        position = (randomness.uniform(area.left, area.right), 0.0, randomness.uniform(area.far, area.near))
        speed = randomness.uniform(*self.speed_range) * randomness.choice((-1.0, 1.0))
        velocity = (speed, 0.0, 0.0) if randomness.random() < 0.5 else (0.0, 0.0, speed)
        height = randomness.uniform(*self.height_range)
        tint = randomness.choice(self.bright_tints if randomness.random() < self.bright_chance else self.dark_tints)
        return position, velocity, height, area_index, (*tint, self.opacity)

    def update(self, seconds):
        self.positions += self.velocities * seconds
        span = self.highs - self.lows
        flat = self.positions[:, [0, 2]]
        wrapped = self.lows + numpy.mod(flat - self.lows, span)
        self.positions[:, 0] = wrapped[:, 0]
        self.positions[:, 2] = wrapped[:, 1]

    def draw(self, atlas_texture, right):
        right_step = numpy.array((right.x, 0.0, right.z), dtype=numpy.float32)
        half_widths = (self.heights * self.width_ratio * 0.5)[:, None]
        up_steps = numpy.zeros((len(self.heights), 3), dtype=numpy.float32)
        up_steps[:, 1] = self.heights
        left_feet = self.positions - right_step * half_widths
        right_feet = self.positions + right_step * half_widths
        corners = numpy.stack((left_feet, right_feet, right_feet + up_steps, left_feet + up_steps), axis=1)
        glPushAttrib(GL_ENABLE_BIT | GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glDisable(GL_LIGHTING)
        glEnable(GL_TEXTURE_2D)
        atlas_texture.bind()
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glDepthMask(GL_FALSE)
        glEnableClientState(GL_VERTEX_ARRAY)
        glEnableClientState(GL_TEXTURE_COORD_ARRAY)
        glEnableClientState(GL_COLOR_ARRAY)
        glVertexPointer(3, GL_FLOAT, 0, corners.reshape(-1, 3))
        glTexCoordPointer(2, GL_FLOAT, 0, self.texture_corners)
        glColorPointer(4, GL_FLOAT, 0, self.colors)
        glDrawArrays(GL_QUADS, 0, 4 * len(self.heights))
        glDisableClientState(GL_COLOR_ARRAY)
        glDisableClientState(GL_TEXTURE_COORD_ARRAY)
        glDisableClientState(GL_VERTEX_ARRAY)
        glPopAttrib()
