import math

from OpenGL.GL import *
from OpenGL.GLU import gluSphere

from lib.vector3 import Vector3


class DisplayList:

    def __init__(self, emit):
        self.list_id = glGenLists(1)
        glNewList(self.list_id, GL_COMPILE)
        emit()
        glEndList()

    def call(self):
        glCallList(self.list_id)


class BlueLight:

    def __init__(self, center, orbit_radius, orbit_speed, phase, bob_height, bob_speed):
        self.slot = None
        self.center = center
        self.orbit_radius = orbit_radius
        self.orbit_speed = orbit_speed
        self.phase = phase
        self.bob_height = bob_height
        self.bob_speed = bob_speed
        self.darkness = (0.0, 0.0, 0.0, 1.0)
        self.constant_attenuation = 0.35
        self.linear_attenuation = 0.015
        self.quadratic_attenuation = 0.0025
        self.core_radius = 0.45
        self.halo_shells = ((0.9, 0.45), (1.7, 0.18), (3.0, 0.07))
        self.color = (0.1, 0.2, 0.45, 1.0)
        self.highlight = (0.5, 0.7, 1.0, 1.0)
        self.core_color = (0.75, 0.88, 1.0)
        self.halo_color = (0.3, 0.55, 1.0)
        self.elapsed = 0.0
        self.current_position = self._position_at(0.0)
        self.orb = None

    def casts_light(self):
        return self.slot is not None

    def configure(self, shapes):
        if self.orb is None:
            self.orb = DisplayList(lambda: self._emit_orb(shapes))
        if not self.casts_light():
            return
        glEnable(self.slot)
        glLightfv(self.slot, GL_AMBIENT, self.darkness)
        glLightfv(self.slot, GL_DIFFUSE, self.color)
        glLightfv(self.slot, GL_SPECULAR, self.highlight)
        glLightf(self.slot, GL_SPOT_CUTOFF, 180.0)
        glLightf(self.slot, GL_CONSTANT_ATTENUATION, self.constant_attenuation)
        glLightf(self.slot, GL_LINEAR_ATTENUATION, self.linear_attenuation)
        glLightf(self.slot, GL_QUADRATIC_ATTENUATION, self.quadratic_attenuation)

    def update(self, seconds):
        self.elapsed += seconds
        self.current_position = self._position_at(self.elapsed)

    def _position_at(self, elapsed):
        angle = self.phase + elapsed * self.orbit_speed
        height = self.center.y + self.bob_height * math.sin(elapsed * self.bob_speed)
        return Vector3(self.center.x + self.orbit_radius * math.cos(angle), height,
                       self.center.z + self.orbit_radius * math.sin(angle))

    def illuminate(self):
        if self.casts_light():
            glLightfv(self.slot, GL_POSITION, (*self.current_position, 1.0))

    def draw(self):
        glPushMatrix()
        glTranslatef(*self.current_position)
        self.orb.call()
        glPopMatrix()

    def _emit_orb(self, shapes):
        glPushAttrib(GL_ENABLE_BIT | GL_DEPTH_BUFFER_BIT | GL_COLOR_BUFFER_BIT)
        glDisable(GL_LIGHTING)
        glColor3f(*self.core_color)
        gluSphere(shapes.quadric, self.core_radius, 16, 12)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE)
        glDepthMask(GL_FALSE)
        for radius, opacity in self.halo_shells:
            glColor4f(*self.halo_color, opacity)
            gluSphere(shapes.quadric, radius, 16, 12)
        glPopAttrib()


class GreenLight(BlueLight):

    def __init__(self, center, orbit_radius, orbit_speed, phase, bob_height, bob_speed):
        super().__init__(center, orbit_radius, orbit_speed, phase, bob_height, bob_speed)
        self.color = (0.1, 0.45, 0.2, 1.0)
        self.highlight = (0.5, 1.0, 0.7, 1.0)
        self.core_color = (0.75, 1.0, 0.88)
        self.halo_color = (0.3, 1.0, 0.55)


class LightBeam:

    def __init__(self, spread_degrees, opacity):
        self.spread_degrees = spread_degrees
        self.opacity = opacity
        self.segments = 24

    def emit(self, apex, axis, length, color):
        direction = axis.normalized()
        helper = Vector3(1.0, 0.0, 0.0) if abs(direction.x) < 0.9 else Vector3(0.0, 0.0, 1.0)
        side = direction.cross(helper).normalized()
        lift = direction.cross(side).normalized()
        rim_radius = length * math.tan(math.radians(self.spread_degrees))
        rim_center = apex + direction * length
        glBegin(GL_TRIANGLE_FAN)
        glColor4f(*color, self.opacity)
        glVertex3f(*apex)
        glColor4f(*color, 0.0)
        for segment in range(self.segments + 1):
            angle = 2.0 * math.pi * segment / self.segments
            rim_point = rim_center + side * (rim_radius * math.cos(angle)) + lift * (rim_radius * math.sin(angle))
            glVertex3f(*rim_point)
        glEnd()


class FloodLight:

    def __init__(self, slot, position, aim):
        self.slot = slot
        self.position = position
        self.aim = aim
        self.color = (0.5, 0.9, 2.4, 1.0)
        self.highlight = (0.6, 0.85, 1.4, 1.0)
        self.darkness = (0.0, 0.0, 0.0, 1.0)
        self.cutoff_degrees = 65.0
        self.spot_exponent = 1.5
        self.constant_attenuation = 1.0
        self.linear_attenuation = 0.0
        self.quadratic_attenuation = 0.0005
        self.beam_color = (0.3, 0.55, 1.0)
        self.beams = (LightBeam(16.0, 0.16), LightBeam(5.0, 0.3))
        self.beam_overshoot = 1.05
        self.fixture_size = 0.45
        self.fixture_color = (0.05, 0.05, 0.06)
        self.lens_radius = 0.22
        self.lens_color = (0.7, 0.85, 1.0)
        self.switched_on = True
        self.shining_look = None
        self.dark_look = None

    def configure(self, shapes):
        glLightfv(self.slot, GL_AMBIENT, self.darkness)
        glLightfv(self.slot, GL_DIFFUSE, self.color)
        glLightfv(self.slot, GL_SPECULAR, self.highlight)
        glLightf(self.slot, GL_SPOT_CUTOFF, self.cutoff_degrees)
        glLightf(self.slot, GL_SPOT_EXPONENT, self.spot_exponent)
        glLightf(self.slot, GL_CONSTANT_ATTENUATION, self.constant_attenuation)
        glLightf(self.slot, GL_LINEAR_ATTENUATION, self.linear_attenuation)
        glLightf(self.slot, GL_QUADRATIC_ATTENUATION, self.quadratic_attenuation)
        if self.shining_look is None:
            self.shining_look = DisplayList(lambda: self._emit_look(shapes, True))
            self.dark_look = DisplayList(lambda: self._emit_look(shapes, False))
        self.switch(self.switched_on)

    def switch(self, switched_on):
        self.switched_on = switched_on
        if switched_on:
            glEnable(self.slot)
        else:
            glDisable(self.slot)

    def beam_axis(self):
        return self.aim - self.position

    def illuminate(self):
        glLightfv(self.slot, GL_POSITION, (*self.position, 1.0))
        glLightfv(self.slot, GL_SPOT_DIRECTION, tuple(self.beam_axis().normalized()))

    def draw(self):
        (self.shining_look if self.switched_on else self.dark_look).call()

    def _emit_look(self, shapes, shining):
        glPushAttrib(GL_ENABLE_BIT | GL_DEPTH_BUFFER_BIT | GL_COLOR_BUFFER_BIT)
        glDisable(GL_LIGHTING)
        half = self.fixture_size / 2.0
        x, y, z = self.position
        shapes.box(x - half, 0.0, z - half, x + half, y, z + half, self.fixture_color)
        glPushMatrix()
        glTranslatef(*self.position)
        glColor3f(*(self.lens_color if shining else self.fixture_color))
        gluSphere(shapes.quadric, self.lens_radius, 12, 8)
        glPopMatrix()
        if shining:
            glEnable(GL_BLEND)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE)
            glDepthMask(GL_FALSE)
            length = self.beam_axis().length() * self.beam_overshoot
            for beam in self.beams:
                beam.emit(self.position, self.beam_axis(), length, self.beam_color)
        glPopAttrib()


class GreenFloodLight(FloodLight):

    def __init__(self, slot, position, aim):
        super().__init__(slot, position, aim)
        self.color = (0.5, 2.2, 0.9, 1.0)
        self.highlight = (0.6, 1.4, 0.85, 1.0)
        self.beam_color = (0.3, 1.0, 0.55)
        self.lens_color = (0.7, 1.0, 0.85)
