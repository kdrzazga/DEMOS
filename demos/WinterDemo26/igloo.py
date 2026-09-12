import math
from OpenGL.GL import *


class Igloo:
    def __init__(self, x, z, ground_height, base_radius=3.5, layers_count=6, blocks_per_layer=16):
        self.x = x
        self.z = z
        self.ground_height = ground_height
        self.base_radius = base_radius
        self.layers_count = layers_count
        self.blocks_per_layer = blocks_per_layer
        self.door_layers = 1
        self.door_half_angle = math.radians(24.0)
        self.ceiling_hole_radius = base_radius * 0.03
        self.tunnel_radius = base_radius * 0.42
        self.tunnel_near_z = base_radius * 0.82
        self.tunnel_far_z = self.tunnel_near_z + base_radius * 0.5
        self.block_color = (0.95, 0.97, 1.0)
        self.outline_color = (0.85, 1.0, 1.0)
        self.doorway_color = (1.0, 0.62, 0.22)
        self.inner_color = (0.88, 0.80, 0.72)
        self.inner_scale = 0.96
        self.display_list = self._compile()

    def _dome_point(self, latitude, longitude):
        ring_radius = self.base_radius * math.cos(latitude)
        return (ring_radius * math.cos(longitude),
                self.base_radius * math.sin(latitude),
                ring_radius * math.sin(longitude))

    def _dome_blocks(self):
        blocks = []
        half_pi = math.pi / 2.0
        top_latitude = math.acos(self.ceiling_hole_radius / self.base_radius)
        for layer in range(self.layers_count):
            latitude_low = top_latitude * layer / self.layers_count
            latitude_high = top_latitude * (layer + 1) / self.layers_count
            for block in range(self.blocks_per_layer):
                longitude_low = 2.0 * math.pi * block / self.blocks_per_layer
                longitude_high = 2.0 * math.pi * (block + 1) / self.blocks_per_layer
                longitude_center = (longitude_low + longitude_high) / 2.0
                if layer < self.door_layers and abs(longitude_center - half_pi) < self.door_half_angle:
                    continue
                blocks.append((self._dome_point(latitude_low, longitude_low),
                               self._dome_point(latitude_low, longitude_high),
                               self._dome_point(latitude_high, longitude_high),
                               self._dome_point(latitude_high, longitude_low)))
        return blocks

    def _tunnel_blocks(self):
        blocks = []
        rings = 3
        slices = 8
        for ring in range(rings):
            z_near = self.tunnel_near_z + (self.tunnel_far_z - self.tunnel_near_z) * ring / rings
            z_far = self.tunnel_near_z + (self.tunnel_far_z - self.tunnel_near_z) * (ring + 1) / rings
            for slice_index in range(slices):
                angle_low = math.pi * slice_index / slices
                angle_high = math.pi * (slice_index + 1) / slices
                blocks.append(((self.tunnel_radius * math.cos(angle_low), self.tunnel_radius * math.sin(angle_low), z_near),
                               (self.tunnel_radius * math.cos(angle_high), self.tunnel_radius * math.sin(angle_high), z_near),
                               (self.tunnel_radius * math.cos(angle_high), self.tunnel_radius * math.sin(angle_high), z_far),
                               (self.tunnel_radius * math.cos(angle_low), self.tunnel_radius * math.sin(angle_low), z_far)))
        return blocks

    def _sphere_normal(self, point):
        length = math.sqrt(point[0] * point[0] + point[1] * point[1] + point[2] * point[2])
        if length == 0.0:
            return 0.0, 1.0, 0.0
        return point[0] / length, point[1] / length, point[2] / length

    def _axis_normal(self, point):
        length = math.sqrt(point[0] * point[0] + point[1] * point[1])
        if length == 0.0:
            return 0.0, 1.0, 0.0
        return point[0] / length, point[1] / length, 0.0

    def _compile(self):
        dome_blocks = self._dome_blocks()
        tunnel_blocks = self._tunnel_blocks()
        display_list = glGenLists(1)
        glNewList(display_list, GL_COMPILE)

        glColor3f(*self.block_color)
        glBegin(GL_QUADS)
        for corners in dome_blocks:
            for point in corners:
                glNormal3f(*self._sphere_normal(point))
                glVertex3f(*point)
        for corners in tunnel_blocks:
            for point in corners:
                glNormal3f(*self._axis_normal(point))
                glVertex3f(*point)
        glEnd()

        glColor3f(*self.inner_color)
        glBegin(GL_QUADS)
        for corners in dome_blocks:
            for point in corners:
                normal = self._sphere_normal(point)
                glNormal3f(-normal[0], -normal[1], -normal[2])
                glVertex3f(point[0] * self.inner_scale, point[1] * self.inner_scale, point[2] * self.inner_scale)
        glEnd()

        glDisable(GL_LIGHTING)
        glLineWidth(1.3)
        glColor3f(*self.outline_color)
        outline_scale = 1.006
        for corners in dome_blocks + tunnel_blocks:
            glBegin(GL_LINE_LOOP)
            for point in corners:
                glVertex3f(point[0] * outline_scale, point[1] * outline_scale, point[2] * outline_scale)
            glEnd()

        glEnable(GL_LIGHTING)

        glEndList()
        return display_list

    def _draw_doorway(self, glow):
        glDisable(GL_LIGHTING)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glColor4f(self.doorway_color[0] * glow, self.doorway_color[1] * glow, self.doorway_color[2] * glow, 0.5)
        slices = 8
        glBegin(GL_TRIANGLE_FAN)
        glVertex3f(0.0, self.tunnel_radius * 0.1, self.tunnel_near_z)
        for slice_index in range(slices + 1):
            angle = math.pi * slice_index / slices
            glVertex3f(self.tunnel_radius * math.cos(angle), self.tunnel_radius * math.sin(angle), self.tunnel_near_z)
        glEnd()
        glDisable(GL_BLEND)
        glEnable(GL_LIGHTING)

    def _blend(self, start, end, factor):
        return tuple(start[axis] + (end[axis] - start[axis]) * factor for axis in range(3))

    def enter_igloo(self, current_eye, progress):
        base = self.base_radius
        progress = max(0.0, min(1.0, progress))

        mouth = (self.x, self.ground_height + self.tunnel_radius * 0.55, self.z + self.tunnel_far_z)
        front = (self.x, self.ground_height + self.tunnel_radius * 0.7, self.z + self.tunnel_far_z + base * 0.7)
        inside = (self.x, self.ground_height + base * 0.4, self.z + base * 0.8)
        half_point = self._blend(current_eye, mouth, 0.5)

        if progress < 0.4:
            eye = self._blend(current_eye, half_point, progress / 0.4)
        elif progress < 0.7:
            eye = self._blend(half_point, front, (progress - 0.4) / 0.3)
        else:
            eye = self._blend(front, inside, (progress - 0.7) / 0.3)

        target_door = (self.x, self.ground_height + self.tunnel_radius * 0.5, self.z + base * 0.2)
        target_inside = (self.x, self.ground_height + base * 0.25, self.z - base * 0.6)
        look_shift = progress * progress * (3.0 - 2.0 * progress)
        target = self._blend(target_door, target_inside, look_shift)
        return eye, target

    def draw(self, doorway_glow=1.0):
        glPushMatrix()
        glTranslatef(self.x, self.ground_height, self.z)
        glCallList(self.display_list)
        self._draw_doorway(doorway_glow)
        glPopMatrix()
