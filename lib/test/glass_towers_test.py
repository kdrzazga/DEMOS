import math
import os
import sys

import pygame
from pygame.locals import DOUBLEBUF, OPENGL
from OpenGL.GL import *
from OpenGL.GLU import gluLookAt, gluNewQuadric, gluPerspective, gluSphere

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from lib.three_mirrors.mirror_renderer import MirrorRenderer
from lib.urban.glass import GlassStreet, GlassStyle, TowerPlan, TowerTier
from lib.urban.shapes import Shapes
from lib.vector3 import Vector3


class BlueLight:

    def __init__(self, slot, center, orbit_radius, orbit_speed, phase, bob_height, bob_speed):
        self.slot = slot
        self.center = center
        self.orbit_radius = orbit_radius
        self.orbit_speed = orbit_speed
        self.phase = phase
        self.bob_height = bob_height
        self.bob_speed = bob_speed
        self.color = (0.25, 0.5, 1.0, 1.0)
        self.highlight = (0.5, 0.7, 1.0, 1.0)
        self.darkness = (0.0, 0.0, 0.0, 1.0)
        self.constant_attenuation = 0.35
        self.linear_attenuation = 0.015
        self.quadratic_attenuation = 0.0025
        self.core_radius = 0.45
        self.core_color = (0.75, 0.88, 1.0)
        self.halo_shells = ((0.9, 0.45), (1.7, 0.18), (3.0, 0.07))
        self.halo_color = (0.3, 0.55, 1.0)
        self.elapsed = 0.0
        self.quadric = None

    def configure(self):
        glEnable(self.slot)
        glLightfv(self.slot, GL_AMBIENT, self.darkness)
        glLightfv(self.slot, GL_DIFFUSE, self.color)
        glLightfv(self.slot, GL_SPECULAR, self.highlight)
        glLightf(self.slot, GL_CONSTANT_ATTENUATION, self.constant_attenuation)
        glLightf(self.slot, GL_LINEAR_ATTENUATION, self.linear_attenuation)
        glLightf(self.slot, GL_QUADRATIC_ATTENUATION, self.quadratic_attenuation)

    def update(self, seconds):
        self.elapsed += seconds

    def position(self):
        angle = self.phase + self.elapsed * self.orbit_speed
        height = self.center.y + self.bob_height * math.sin(self.elapsed * self.bob_speed)
        return Vector3(self.center.x + self.orbit_radius * math.cos(angle), height,
                       self.center.z + self.orbit_radius * math.sin(angle))

    def illuminate(self):
        glLightfv(self.slot, GL_POSITION, (*self.position(), 1.0))

    def draw(self):
        if self.quadric is None:
            self.quadric = gluNewQuadric()
        glPushAttrib(GL_ENABLE_BIT | GL_DEPTH_BUFFER_BIT | GL_COLOR_BUFFER_BIT)
        glDisable(GL_LIGHTING)
        glPushMatrix()
        glTranslatef(*self.position())
        glColor3f(*self.core_color)
        gluSphere(self.quadric, self.core_radius, 16, 12)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE)
        glDepthMask(GL_FALSE)
        for radius, opacity in self.halo_shells:
            glColor4f(*self.halo_color, opacity)
            gluSphere(self.quadric, radius, 16, 12)
        glPopMatrix()
        glPopAttrib()


class LightBeam:

    def __init__(self, spread_degrees, opacity):
        self.spread_degrees = spread_degrees
        self.opacity = opacity
        self.segments = 24

    def draw(self, apex, axis, length, color):
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
        self.shapes = None

    def configure(self):
        glLightfv(self.slot, GL_AMBIENT, self.darkness)
        glLightfv(self.slot, GL_DIFFUSE, self.color)
        glLightfv(self.slot, GL_SPECULAR, self.highlight)
        glLightf(self.slot, GL_SPOT_CUTOFF, self.cutoff_degrees)
        glLightf(self.slot, GL_SPOT_EXPONENT, self.spot_exponent)
        glLightf(self.slot, GL_CONSTANT_ATTENUATION, self.constant_attenuation)
        glLightf(self.slot, GL_LINEAR_ATTENUATION, self.linear_attenuation)
        glLightf(self.slot, GL_QUADRATIC_ATTENUATION, self.quadratic_attenuation)
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
        if self.shapes is None:
            self.shapes = Shapes()
        glPushAttrib(GL_ENABLE_BIT | GL_DEPTH_BUFFER_BIT | GL_COLOR_BUFFER_BIT)
        glDisable(GL_LIGHTING)
        self._draw_fixture()
        if self.switched_on:
            glEnable(GL_BLEND)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE)
            glDepthMask(GL_FALSE)
            glShadeModel(GL_SMOOTH)
            length = self.beam_axis().length() * self.beam_overshoot
            for beam in self.beams:
                beam.draw(self.position, self.beam_axis(), length, self.beam_color)
        glPopAttrib()

    def _draw_fixture(self):
        half = self.fixture_size / 2.0
        x, y, z = self.position
        self.shapes.box(x - half, 0.0, z - half, x + half, y, z + half, self.fixture_color)
        glPushMatrix()
        glTranslatef(*self.position)
        glColor3f(*(self.lens_color if self.switched_on else self.fixture_color))
        gluSphere(self.shapes.quadric, self.lens_radius, 12, 8)
        glPopMatrix()


class NightGround:

    def __init__(self):
        self.half_extent = 120.0
        self.cell_size = 3.0
        self.color = (0.06, 0.065, 0.075)
        self.display_list = None

    def draw(self):
        if self.display_list is None:
            self.display_list = glGenLists(1)
            glNewList(self.display_list, GL_COMPILE)
            self._emit()
            glEndList()
        glCallList(self.display_list)

    def _emit(self):
        cells = int(2.0 * self.half_extent / self.cell_size)
        glColor3f(*self.color)
        glNormal3f(0.0, 1.0, 0.0)
        glBegin(GL_QUADS)
        for row in range(cells):
            for column in range(cells):
                near_x = -self.half_extent + column * self.cell_size
                near_z = -self.half_extent + row * self.cell_size
                far_x = near_x + self.cell_size
                far_z = near_z + self.cell_size
                glVertex3f(near_x, 0.0, far_z)
                glVertex3f(far_x, 0.0, far_z)
                glVertex3f(far_x, 0.0, near_z)
                glVertex3f(near_x, 0.0, near_z)
        glEnd()


class GlassTowersScene:

    def __init__(self):
        self.street = GlassStreet([
            TowerPlan([TowerTier(7.0, 9.0, 20.0)], GlassStyle(), seed=3),
            TowerPlan([TowerTier(9.0, 10.0, 28.0), TowerTier(6.5, 7.0, 8.0)], self._greener_style(), seed=8),
            TowerPlan([TowerTier(6.0, 8.0, 16.0)], self._darker_style(), seed=11),
            TowerPlan([TowerTier(10.0, 11.0, 34.0), TowerTier(7.0, 8.0, 10.0), TowerTier(4.0, 4.0, 5.0)],
                      GlassStyle(), seed=5),
            TowerPlan([TowerTier(8.0, 9.0, 24.0)], self._greener_style(), seed=13),
            TowerPlan([TowerTier(7.5, 9.0, 30.0), TowerTier(5.0, 6.0, 6.0)], self._darker_style(), seed=21),
        ], gap=1.2, front_line=0.0)
        self.side_glow = (0.1, 0.2, 0.45, 1.0)
        self.lights = [
            BlueLight(GL_LIGHT0, Vector3(0.0, 5.0, -4.0), 34.0, 0.3, 0.0, 2.0, 0.6),
            BlueLight(GL_LIGHT1, Vector3(0.0, 20.0, -4.0), 31.0, -0.22, math.pi, 10.0, 0.25),
        ]
        for light in self.lights:
            light.color = self.side_glow
        self.flood_distance = 11.0
        self.flood_height = 0.6
        flood_slots = (GL_LIGHT2, GL_LIGHT3, GL_LIGHT4, GL_LIGHT5, GL_LIGHT6, GL_LIGHT7)
        self.flood_lights = [
            FloodLight(slot, Vector3(front.x, self.flood_height, front.z + self.flood_distance), front)
            for slot, front in zip(flood_slots, self.street.front_centers)
        ]
        self.ground = NightGround()
        self.ambient = (0.02, 0.025, 0.04, 1.0)

    def _greener_style(self):
        style = GlassStyle()
        style.pane_tint = (0.14, 0.24, 0.26)
        style.column_width = 1.1
        return style

    def _darker_style(self):
        style = GlassStyle()
        style.pane_tint = (0.1, 0.12, 0.18)
        style.lit_pane_chance = 0.08
        style.floor_height = 0.95
        return style

    def configure(self):
        glLightModelfv(GL_LIGHT_MODEL_AMBIENT, self.ambient)
        glLightModeli(GL_LIGHT_MODEL_LOCAL_VIEWER, GL_TRUE)
        for light in self.every_light():
            light.configure()

    def every_light(self):
        return self.lights + self.flood_lights

    def reflectors(self):
        return self.street.reflectors()

    def change_blur(self, step):
        self.street.set_blur(self.street.blur + step)

    @property
    def blur(self):
        return self.street.blur

    @property
    def flood_lights_on(self):
        return self.flood_lights[0].switched_on

    def toggle_flood_lights(self):
        switched_on = not self.flood_lights_on
        for flood_light in self.flood_lights:
            flood_light.switch(switched_on)

    def update(self, seconds):
        self.street.update(seconds)
        for light in self.lights:
            light.update(seconds)

    def illuminate(self):
        glEnable(GL_LIGHTING)
        for light in self.every_light():
            light.illuminate()

    def draw(self):
        self.ground.draw()
        self.street.draw()
        for light in self.every_light():
            light.draw()


class StreetCamera:

    def __init__(self):
        self.target = Vector3(0.0, 18.0, -4.0)
        self.distance = 64.0
        self.lowest_height = 4.0
        self.highest_height = 30.0
        self.orbit_speed = 0.07
        self.rise_speed = 0.13
        self.elapsed = 0.0
        self.paused = False

    def toggle_pause(self):
        self.paused = not self.paused

    def update(self, seconds):
        if not self.paused:
            self.elapsed += seconds

    def eye(self):
        angle = self.elapsed * self.orbit_speed
        middle = (self.lowest_height + self.highest_height) / 2.0
        swing = (self.highest_height - self.lowest_height) / 2.0
        height = middle - swing * math.cos(self.elapsed * self.rise_speed)
        return Vector3(self.target.x + self.distance * math.sin(angle), height,
                       self.target.z + self.distance * math.cos(angle))

    def look(self):
        gluLookAt(*self.eye(), *self.target, 0.0, 1.0, 0.0)


class GlassTowersTest:

    def __init__(self):
        self.window_size = (1280, 720)
        self.frames_per_second = 60
        self.night = (0.008, 0.01, 0.02, 1.0)
        self.fog_density = 0.009
        self.field_of_view = 50.0
        self.blur_step = 0.05
        self.blur_keys = (pygame.K_PLUS, pygame.K_EQUALS, pygame.K_KP_PLUS)
        self.sharpen_keys = (pygame.K_MINUS, pygame.K_KP_MINUS)
        self.caption = ("Glass Towers - reflections: {}, blur: {:.2f}, flood lights: {}  "
                        "(UP/DOWN reflections, +/- blur, F flood lights, SPACE camera, ESC quit)")
        pygame.init()
        pygame.display.gl_set_attribute(pygame.GL_STENCIL_SIZE, 8)
        pygame.display.set_mode(self.window_size, DOUBLEBUF | OPENGL)
        self.clock = pygame.time.Clock()
        self.scene = GlassTowersScene()
        self.camera = StreetCamera()
        self.renderer = MirrorRenderer(max_reflections=1, reflection_limit=2)
        self.running = True
        self.init_gl()
        self.show_caption()

    def init_gl(self):
        glViewport(0, 0, *self.window_size)
        glEnable(GL_DEPTH_TEST)
        glDepthFunc(GL_LEQUAL)
        glDisable(GL_CULL_FACE)
        glEnable(GL_NORMALIZE)
        glShadeModel(GL_SMOOTH)
        glEnable(GL_COLOR_MATERIAL)
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
        glClearColor(*self.night)
        glClearStencil(0)
        glEnable(GL_FOG)
        glFogi(GL_FOG_MODE, GL_EXP2)
        glFogf(GL_FOG_DENSITY, self.fog_density)
        glFogfv(GL_FOG_COLOR, self.night)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(self.field_of_view, self.window_size[0] / self.window_size[1], 0.5, 400.0)
        glMatrixMode(GL_MODELVIEW)
        self.scene.configure()

    def show_caption(self):
        pygame.display.set_caption(self.caption.format(self.renderer.max_reflections, self.scene.blur,
                                                       "on" if self.scene.flood_lights_on else "off"))

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                self.handle_key(event.key)

    def handle_key(self, key):
        if key == pygame.K_ESCAPE:
            self.running = False
        elif key == pygame.K_UP:
            self.renderer.change_reflections(1)
        elif key == pygame.K_DOWN:
            self.renderer.change_reflections(-1)
        elif key in self.blur_keys:
            self.scene.change_blur(self.blur_step)
        elif key in self.sharpen_keys:
            self.scene.change_blur(-self.blur_step)
        elif key == pygame.K_f:
            self.scene.toggle_flood_lights()
        elif key == pygame.K_SPACE:
            self.camera.toggle_pause()
        self.show_caption()

    def draw(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT | GL_STENCIL_BUFFER_BIT)
        glLoadIdentity()
        self.camera.look()
        self.renderer.render(self.scene.reflectors(), self.scene, self.camera.eye())
        pygame.display.flip()

    def run(self):
        while self.running:
            seconds = self.clock.tick(self.frames_per_second) / 1000.0
            self.handle_events()
            self.scene.update(seconds)
            self.camera.update(seconds)
            self.draw()
        pygame.quit()


if __name__ == "__main__":
    GlassTowersTest().run()
