import math
import os
import sys

import pygame
from pygame.locals import DOUBLEBUF, OPENGL
from OpenGL.GL import *
from OpenGL.GLU import gluLookAt, gluPerspective

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from lib.amiga.amiga_ball import AmigaBall
from lib.three_mirrors import MirrorCorner
from lib.vector3 import Vector3


class BouncingAmigaBall:

    def __init__(self, corner):
        self.corner = corner
        self.ball = AmigaBall(radius=0.9)
        self.position = Vector3(corner.size * 0.55, corner.size * 0.7, corner.size * 0.4)
        self.velocity = Vector3(1.6, 0.0, 1.1)
        self.gravity = 9.0
        self.bounce_speed = 7.0

    def update(self, seconds):
        self.ball.update(seconds)
        self.velocity = self.velocity + Vector3(0.0, -self.gravity * seconds, 0.0)
        self.position = self.position + self.velocity * seconds
        self.bounce_inside_corner()

    def bounce_inside_corner(self):
        low = self.ball.radius
        high = self.corner.size - self.ball.radius
        x, y, z = self.position
        vx, vy, vz = self.velocity
        if x < low or x > high:
            vx = -vx
            x = min(max(x, low), high)
        if z < low or z > high:
            vz = -vz
            z = min(max(z, low), high)
        if y < low:
            vy = self.bounce_speed
            y = low
        self.position = Vector3(x, y, z)
        self.velocity = Vector3(vx, vy, vz)

    def draw(self):
        glPushMatrix()
        glTranslatef(*self.position)
        self.ball.render()
        glPopMatrix()
        glDisable(GL_TEXTURE_2D)


class CornerScene:

    def __init__(self, corner):
        self.actors = [BouncingAmigaBall(corner)]

    def update(self, seconds):
        for actor in self.actors:
            actor.update(seconds)

    def draw(self):
        for actor in self.actors:
            actor.draw()


class OrbitingCamera:

    def __init__(self, corner):
        self.target = Vector3(corner.size * 0.4, corner.size * 0.3, corner.size * 0.4)
        self.distance = corner.size * 2.2
        self.central_azimuth = math.radians(45.0)
        self.azimuth_swing = math.radians(22.0)
        self.central_elevation = math.radians(30.0)
        self.elevation_swing = math.radians(10.0)
        self.azimuth_rate = 0.25
        self.elevation_rate = 0.17
        self.elapsed = 0.0
        self.paused = False

    def toggle_pause(self):
        self.paused = not self.paused

    def update(self, seconds):
        if not self.paused:
            self.elapsed += seconds

    def eye(self):
        azimuth = self.central_azimuth + self.azimuth_swing * math.sin(self.elapsed * self.azimuth_rate)
        elevation = self.central_elevation + self.elevation_swing * math.sin(self.elapsed * self.elevation_rate)
        offset = Vector3(math.cos(elevation) * math.sin(azimuth),
                         math.sin(elevation),
                         math.cos(elevation) * math.cos(azimuth))
        return self.target + offset * self.distance

    def look(self):
        gluLookAt(*self.eye(), *self.target, 0.0, 1.0, 0.0)


class ThreeMirrorsTest:

    def __init__(self):
        self.window_size = (1280, 720)
        self.frames_per_second = 60
        self.background = (0.02, 0.02, 0.06, 1.0)
        self.field_of_view = 45.0
        self.caption = ("Three Mirrors - reflections: {}, shade: {}, blur: {:.1f}  "
                        "(UP/DOWN reflections, C Y R P B U G shades, +/- blur, SPACE camera, ESC quit)")
        self.blur_step = 0.1
        self.sharpen_keys = (pygame.K_MINUS, pygame.K_KP_MINUS)
        self.blur_keys = (pygame.K_PLUS, pygame.K_EQUALS, pygame.K_KP_PLUS)
        self.shade_keys = {
            pygame.K_c: "cyan",
            pygame.K_y: "yellow",
            pygame.K_r: "red",
            pygame.K_p: "pink",
            pygame.K_b: "light blue",
            pygame.K_u: "purple",
            pygame.K_g: "light green",
        }
        self.unshaded = "clear"
        self.shade = self.unshaded
        pygame.init()
        pygame.display.gl_set_attribute(pygame.GL_STENCIL_SIZE, 8)
        pygame.display.set_mode(self.window_size, DOUBLEBUF | OPENGL)
        self.clock = pygame.time.Clock()
        self.corner = MirrorCorner(size=6.0)
        self.scene = CornerScene(self.corner)
        self.camera = OrbitingCamera(self.corner)
        self.running = True
        self.init_gl()
        self.show_caption()

    def init_gl(self):
        glViewport(0, 0, *self.window_size)
        glEnable(GL_DEPTH_TEST)
        glDepthFunc(GL_LEQUAL)
        glDisable(GL_LIGHTING)
        glDisable(GL_CULL_FACE)
        glEnable(GL_LINE_SMOOTH)
        glClearColor(*self.background)
        glClearStencil(0)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(self.field_of_view, self.window_size[0] / self.window_size[1], 0.1, 200.0)
        glMatrixMode(GL_MODELVIEW)

    def show_caption(self):
        pygame.display.set_caption(self.caption.format(self.corner.max_reflections, self.shade,
                                                       self.corner.mirrors[0].blur))

    def change_blur(self, step):
        for mirror in self.corner.mirrors:
            mirror.set_blur(mirror.blur + step)
        self.show_caption()

    def toggle_shade(self, name):
        self.shade = self.unshaded if self.shade == name else name
        for mirror in self.corner.mirrors:
            mirror.apply_shade(self.shade)
        self.show_caption()

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
            self.corner.change_reflections(1)
            self.show_caption()
        elif key == pygame.K_DOWN:
            self.corner.change_reflections(-1)
            self.show_caption()
        elif key == pygame.K_SPACE:
            self.camera.toggle_pause()
        elif key in self.blur_keys:
            self.change_blur(self.blur_step)
        elif key in self.sharpen_keys:
            self.change_blur(-self.blur_step)
        elif key in self.shade_keys:
            self.toggle_shade(self.shade_keys[key])

    def draw(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT | GL_STENCIL_BUFFER_BIT)
        glLoadIdentity()
        self.camera.look()
        self.corner.render(self.scene, self.camera.eye())
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
    ThreeMirrorsTest().run()
