import math
import os
import sys

import numpy
import pygame
from pygame.locals import DOUBLEBUF, OPENGL
from OpenGL.GL import *
from OpenGL.GLU import gluPerspective

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from lib.unitra.textures import ScreenPicture
from lib.unitra.tv import UnitraT50


class OrbitCamera:

    def __init__(self):
        self.target = (0.0, 0.0, -0.45)
        self.reset()
        self.degrees_per_pixel = 0.3
        self.zoom_factor = 0.9
        self.nearest = 1.2
        self.farthest = 8.0

    def reset(self):
        self.yaw = -22.0
        self.pitch = 8.0
        self.distance = 3.1

    def drag(self, dx, dy):
        self.yaw += dx * self.degrees_per_pixel
        self.pitch = max(-80.0, min(80.0, self.pitch + dy * self.degrees_per_pixel))

    def zoom(self, steps):
        self.distance = max(self.nearest, min(self.farthest, self.distance * self.zoom_factor ** steps))

    def apply(self):
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glTranslatef(0.0, 0.0, -self.distance)
        glRotatef(self.pitch, 1.0, 0.0, 0.0)
        glRotatef(self.yaw, 0.0, 1.0, 0.0)
        glTranslatef(*(-coordinate for coordinate in self.target))


class Studio:

    def __init__(self, table_height):
        self.table_height = table_height
        self.table_color = (0.36, 0.3, 0.24)
        self.table_extent = 3.0
        self.background = (0.09, 0.1, 0.12)
        self.global_ambient = (0.3, 0.3, 0.3, 1.0)
        self.key_light = ((-2.0, 2.6, 3.2, 1.0), (0.95, 0.92, 0.86, 1.0), (1.0, 1.0, 1.0, 1.0))
        self.fill_light = ((2.8, 1.0, 1.6, 1.0), (0.35, 0.37, 0.42, 1.0), (0.25, 0.25, 0.25, 1.0))

    def light(self, light_id, setup):
        position, diffuse, specular = setup
        glEnable(light_id)
        glLightfv(light_id, GL_POSITION, position)
        glLightfv(light_id, GL_DIFFUSE, diffuse)
        glLightfv(light_id, GL_SPECULAR, specular)
        glLightfv(light_id, GL_AMBIENT, (0.0, 0.0, 0.0, 1.0))

    def setup_lights(self):
        glEnable(GL_LIGHTING)
        glLightModelfv(GL_LIGHT_MODEL_AMBIENT, self.global_ambient)
        self.light(GL_LIGHT0, self.key_light)
        self.light(GL_LIGHT1, self.fill_light)

    def render_table(self):
        extent = self.table_extent
        glEnable(GL_COLOR_MATERIAL)
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
        glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, (0.1, 0.1, 0.1, 1.0))
        glColor3f(*self.table_color)
        glBegin(GL_QUADS)
        glNormal3f(0.0, 1.0, 0.0)
        glVertex3f(-extent, self.table_height, extent)
        glVertex3f(extent, self.table_height, extent)
        glVertex3f(extent, self.table_height, -extent)
        glVertex3f(-extent, self.table_height, -extent)
        glEnd()


class TestBroadcast:

    def __init__(self):
        self.width = 256
        self.height = 192
        self.seconds = 0.0
        self.generator = numpy.random.default_rng(5005)
        columns = numpy.arange(self.width, dtype=numpy.float32)
        rows = numpy.arange(self.height, dtype=numpy.float32)
        self.x, self.y = numpy.meshgrid(columns, rows)
        self.programmes = (self.snow, self.colour_bars, self.test_card, self.plasma, self.rolling_rainbow)

    def update(self, seconds):
        self.seconds += seconds

    def snow(self):
        grain = self.generator.integers(0, 256, (self.height, self.width), dtype=numpy.uint8).astype(numpy.float32)
        bands = 25.0 * numpy.sin(self.y * 0.08 + self.seconds * 9.0)
        return numpy.repeat((grain * 0.85 + bands)[..., None], 3, axis=2)

    def colour_bars(self):
        palette = numpy.array(((235, 235, 235), (235, 235, 16), (16, 235, 235), (16, 235, 16),
                               (235, 16, 235), (235, 16, 16), (16, 16, 235), (16, 16, 16)), dtype=numpy.float32)
        bars = palette[(self.x * len(palette) / self.width).astype(int)]
        ramp = numpy.repeat((self.x / self.width * 255.0)[..., None], 3, axis=2)
        return numpy.where((self.y > self.height * 0.78)[..., None], ramp, bars)

    def test_card(self):
        grid = ((self.x % 32) < 2) | ((self.y % 32) < 2)
        dx = self.x - self.width / 2.0
        dy = self.y - self.height / 2.0
        radius = numpy.sqrt(dx * dx + dy * dy)
        ring = numpy.abs(radius - 80.0) < 2.5
        cross = (numpy.abs(dx) < 1.0) | (numpy.abs(dy) < 1.0)
        sweep = numpy.where(radius < 78.0, 0.5 + 0.5 * numpy.sin(numpy.arctan2(dy, dx) * 4.0 - self.seconds * 2.0), 0.4)
        level = numpy.where(grid | ring | cross, 235.0, 60.0 + 100.0 * sweep)
        return numpy.repeat(level[..., None], 3, axis=2)

    def plasma(self):
        time = self.seconds
        value = (numpy.sin(self.x * 0.05 + time) + numpy.sin(self.y * 0.07 - time * 1.3)
                 + numpy.sin((self.x + self.y) * 0.04 + time * 0.7)
                 + numpy.sin(numpy.hypot(self.x - 128.0, self.y - 96.0) * 0.08 - time * 2.0))
        return numpy.stack((128 + 127 * numpy.sin(value * math.pi), 128 + 127 * numpy.sin(value * math.pi + 2.1),
                            128 + 127 * numpy.sin(value * math.pi + 4.2)), axis=2)

    def rolling_rainbow(self):
        phase = (self.y / self.height + self.seconds * 0.25) * 2.0 * math.pi
        return numpy.stack((128 + 127 * numpy.sin(phase), 128 + 127 * numpy.sin(phase + 2.1),
                            128 + 127 * numpy.sin(phase + 4.2)), axis=2)

    def frame(self, channel, brightness, contrast):
        picture = self.programmes[channel]()
        adjusted = (picture - 128.0) * (contrast / 5.0) + 128.0 + (brightness - 5.0) * 22.0
        return numpy.clip(adjusted, 0, 255).astype(numpy.uint8)


class UnitraTestApp:

    def __init__(self):
        self.window_size = (1280, 800)
        self.field_of_view = 40.0
        self.slider_speed = 6.0
        self.selected_slider = 0
        self.dragging = False
        self.running = True
        pygame.init()
        pygame.display.set_mode(self.window_size, DOUBLEBUF | OPENGL)
        self.clock = pygame.time.Clock()
        self.tv = UnitraT50()
        self.camera = OrbitCamera()
        self.studio = Studio(-self.tv.cabinet.half_height - self.tv.feet.height)
        self.broadcast = TestBroadcast()
        self.picture = ScreenPicture(self.broadcast.width, self.broadcast.height)
        self.tv.show(self.picture)
        self.channel_keys = {pygame.K_1: 0, pygame.K_2: 1, pygame.K_3: 2, pygame.K_4: 3, pygame.K_5: 4}
        self.toggles = {pygame.K_p: self.tv.toggle_power, pygame.K_t: self.tv.toggle_treble,
                        pygame.K_h: self.tv.toggle_headphones, pygame.K_r: self.camera.reset}

    def setup_projection(self):
        width, height = self.window_size
        glViewport(0, 0, width, height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(self.field_of_view, width / height, 0.05, 50.0)
        glEnable(GL_DEPTH_TEST)
        glClearColor(*self.studio.background, 1.0)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                self.handle_key(event.key)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self.dragging = True
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                self.dragging = False
            elif event.type == pygame.MOUSEMOTION and self.dragging:
                self.camera.drag(*event.rel)
            elif event.type == pygame.MOUSEWHEEL:
                self.camera.zoom(event.y)

    def handle_key(self, key):
        if key == pygame.K_ESCAPE:
            self.running = False
        elif key in self.channel_keys:
            self.tv.select_channel(self.channel_keys[key])
        elif key in self.toggles:
            self.toggles[key]()
        elif key == pygame.K_UP:
            self.selected_slider = (self.selected_slider - 1) % len(self.tv.sliders)
        elif key == pygame.K_DOWN:
            self.selected_slider = (self.selected_slider + 1) % len(self.tv.sliders)

    def handle_held_keys(self, seconds):
        pressed = pygame.key.get_pressed()
        direction = pressed[pygame.K_RIGHT] - pressed[pygame.K_LEFT]
        if direction:
            self.tv.sliders[self.selected_slider].nudge(direction * self.slider_speed * seconds)

    def update(self, seconds):
        self.handle_held_keys(seconds)
        self.tv.update(seconds)
        self.broadcast.update(seconds)
        if self.tv.powered and self.tv.channel is not None:
            brightness, contrast, volume = (slider.value for slider in self.tv.sliders)
            self.picture.upload(self.broadcast.frame(self.tv.channel, brightness, contrast))
        self.update_caption()

    def update_caption(self):
        names = self.tv.layout.slider_labels
        readings = ["%s%s %.1f" % (">" if index == self.selected_slider else "", name, slider.target)
                    for index, (name, slider) in enumerate(zip(names, self.tv.sliders))]
        channel = "-" if self.tv.channel is None else str(self.tv.channel + 1)
        state = "on" if self.tv.powered else "off"
        pygame.display.set_caption("UNITRA T50 05 | sieć %s | program %s | %s | 1-5 P T H, arrows, drag, wheel, R"
                                   % (state, channel, " | ".join(readings)))

    def render(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        self.camera.apply()
        self.studio.setup_lights()
        self.studio.render_table()
        self.tv.render()
        pygame.display.flip()

    def run(self):
        self.setup_projection()
        while self.running:
            seconds = self.clock.tick(60) / 1000.0
            self.handle_events()
            self.update(seconds)
            self.render()
        self.picture.destroy()
        self.tv.destroy()
        pygame.quit()


if __name__ == "__main__":
    UnitraTestApp().run()
