import math
import os
import sys

import pygame
from pygame.locals import DOUBLEBUF, OPENGL
from OpenGL.GL import *
from OpenGL.GLU import gluLookAt, gluPerspective

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from lib.fantasy.demon import Demon, RamDemonModel
from lib.fantasy.gargoyle import Gargoyle, GargoyleModel
from lib.fantasy.scenes.bridge import LavaBridgeScene
from lib.fantasy.scenes.tower import TowerScene
from lib.fantasy.pazure import Pazure
from lib.fantasy.sorcerer import Sorcerer
from lib.fantasy.troll import Troll
from lib.fantasy.vampire import Vampire
from lib.fantasy.werewolf import Werewolf


class SummoningCircle:

    def __init__(self, radius):
        self.radius = radius
        self.color = (1.0, 0.22, 0.05)
        self.segments = 96
        self.rune_count = 24
        self.star_points = 5
        self.pulses_per_second = 0.55
        self.seconds = 0.0

    def update(self, seconds):
        self.seconds += seconds

    def brightness(self):
        return 0.75 + 0.25 * math.sin(self.seconds * self.pulses_per_second * 2.0 * math.pi)

    def ring(self, radius):
        glBegin(GL_LINE_LOOP)
        for step in range(self.segments):
            angle = 2.0 * math.pi * step / self.segments
            glVertex3f(radius * math.cos(angle), 0.0, radius * math.sin(angle))
        glEnd()

    def render(self):
        strength = self.brightness()
        red, green, blue = self.color
        glPushAttrib(GL_ENABLE_BIT | GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT | GL_LINE_BIT)
        glDisable(GL_LIGHTING)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE)
        glDepthMask(GL_FALSE)
        glBegin(GL_TRIANGLE_FAN)
        glColor4f(red, green, blue, 0.55 * strength)
        glVertex3f(0.0, 0.0, 0.0)
        glColor4f(red, green, blue, 0.0)
        for step in range(self.segments + 1):
            angle = 2.0 * math.pi * step / self.segments
            glVertex3f(1.3 * self.radius * math.cos(angle), 0.0, 1.3 * self.radius * math.sin(angle))
        glEnd()
        glLineWidth(2.0)
        glColor4f(red, green * 1.6, blue, 0.9 * strength)
        self.ring(self.radius)
        self.ring(self.radius * 0.86)
        inner = self.radius * 0.86
        glBegin(GL_LINE_LOOP)
        for point in range(self.star_points):
            angle = math.pi / 2.0 + 2.0 * math.pi * (point * 2 % self.star_points) / self.star_points
            glVertex3f(inner * math.cos(angle), 0.0, inner * math.sin(angle))
        glEnd()
        glBegin(GL_LINES)
        for rune in range(self.rune_count):
            angle = 2.0 * math.pi * rune / self.rune_count + self.seconds * 0.1
            tilt = 0.06 if rune % 2 else -0.06
            glVertex3f(inner * 1.03 * math.cos(angle), 0.0, inner * 1.03 * math.sin(angle))
            glVertex3f(self.radius * 0.97 * math.cos(angle + tilt), 0.0, self.radius * 0.97 * math.sin(angle + tilt))
        glEnd()
        glPopAttrib()


class GargoyleRow:

    def __init__(self, height, shades, spacing):
        self.gargoyles = []
        for index, shade in enumerate(shades):
            gargoyle = Gargoyle(height, GargoyleModel(shade))
            gargoyle.position = ((index - (len(shades) - 1) / 2.0) * spacing, 0.0, 0.0)
            self.gargoyles.append(gargoyle)

    @property
    def talking(self):
        return self.gargoyles[0].talking

    @talking.setter
    def talking(self, value):
        for gargoyle in self.gargoyles:
            gargoyle.talking = value

    @property
    def acting(self):
        return self.gargoyles[0].acting

    @acting.setter
    def acting(self, value):
        for gargoyle in self.gargoyles:
            gargoyle.acting = value

    def restart(self):
        for gargoyle in self.gargoyles:
            gargoyle.restart()

    def update(self, seconds):
        for gargoyle in self.gargoyles:
            gargoyle.update(seconds)

    def focus(self):
        return 0.0, 0.0

    def render(self):
        for gargoyle in self.gargoyles:
            gargoyle.render()


class Exhibit:

    def __init__(self, name, creature, lights, ambient, background, look_at_height, orbit_distance, props=()):
        self.name = name
        self.creature = creature
        self.lights = lights
        self.ambient = ambient
        self.background = background
        self.look_at_height = look_at_height
        self.orbit_distance = orbit_distance
        self.props = props

    def restart(self):
        self.creature.restart()

    def update(self, seconds):
        self.creature.update(seconds)
        for prop in self.props:
            prop.update(seconds)

    def render(self):
        self.creature.render()
        for prop in self.props:
            prop.render()


class FantasyTest:

    def __init__(self):
        self.window_size = (1280, 720)
        self.frames_per_second = 60
        self.field_of_view = 32.0
        self.orbit_yaw = 0.0
        self.orbit_pitch = 0.08
        self.closest_distance = 1.2
        self.farthest_distance = 20.0
        self.zoom_step = 1.1
        self.spin_radians_per_second = 0.35
        self.drag_radians_per_pixel = 0.008
        self.demon_height = 1.0
        self.hover_height = 0.3
        self.circle_radius = 0.55
        self.troll_height = 0.9
        self.ram_demon_height = 0.95
        self.sorcerer_height = 1.0
        self.vampire_height = 1.0
        self.werewolf_height = 1.3
        self.gargoyle_height = 0.8
        self.gargoyle_spacing = 1.1
        self.spinning = False
        self.scene_camera = True
        self.paused = False
        self.dragging = False
        self.light_ids = (GL_LIGHT0, GL_LIGHT1, GL_LIGHT2)
        self.caption = "{} - {:.0f} fps  (1-9,0/TAB exhibit, C scene camera, A act/idle, T talk, drag to orbit, wheel zoom, SPACE spin, W wings, P pause, R restart, ESC quit)"
        pygame.init()
        pygame.display.set_mode(self.window_size, DOUBLEBUF | OPENGL)
        self.clock = pygame.time.Clock()
        self.demon = Demon(self.demon_height)
        self.demon.levitation = self.hover_height
        self.troll = Troll(self.troll_height)
        self.ram_demon = Demon(self.ram_demon_height, RamDemonModel())
        self.ram_demon.levitation = self.hover_height
        self.ram_demon.flaps_per_second = 0.95
        self.ram_demon.flap_degrees = 30.0
        self.ram_demon_circle = SummoningCircle(self.circle_radius)
        self.ram_demon_circle.color = (1.0, 0.45, 0.08)
        self.sorcerer = Sorcerer(self.sorcerer_height)
        self.lava_bridge = LavaBridgeScene()
        self.tower_scene = TowerScene()
        self.pazure = Pazure(1.0)
        self.pazure.yaw = -math.pi / 2.0
        self.vampire = Vampire(self.vampire_height)
        self.werewolf = Werewolf(self.werewolf_height)
        self.gargoyles = GargoyleRow(self.gargoyle_height, ("grey", "light grey", "brown"), self.gargoyle_spacing)
        self.exhibits = [
            Exhibit("Demon", self.demon,
                    (((0.2, -0.7, 0.7, 0.0), (1.0, 0.36, 0.16, 1.0)),
                     ((-0.6, 0.8, -0.5, 0.0), (0.45, 0.55, 0.62, 1.0)),
                     ((0.3, 0.5, 1.0, 0.0), (0.42, 0.34, 0.32, 1.0))),
                    (0.14, 0.12, 0.12, 1.0), (0.02, 0.02, 0.03, 1.0), 0.5, 4.2,
                    (SummoningCircle(self.circle_radius),)),
            Exhibit("Troll", self.troll,
                    (((-0.5, 0.8, 0.6, 0.0), (0.82, 0.86, 0.78, 1.0)),
                     ((0.7, 0.3, -0.6, 0.0), (0.25, 0.55, 0.55, 1.0)),
                     ((0.4, -0.3, 0.8, 0.0), (0.30, 0.26, 0.18, 1.0))),
                    (0.16, 0.22, 0.22, 1.0), (0.03, 0.09, 0.10, 1.0), 0.6, 3.8),
            Exhibit("Ram demon", self.ram_demon,
                    (((0.2, -0.7, 0.7, 0.0), (1.0, 0.62, 0.30, 1.0)),
                     ((-0.6, 0.8, -0.5, 0.0), (0.55, 0.45, 0.70, 1.0)),
                     ((0.3, 0.5, 1.0, 0.0), (0.40, 0.36, 0.40, 1.0))),
                    (0.13, 0.12, 0.14, 1.0), (0.02, 0.02, 0.03, 1.0), 0.5, 3.6,
                    (self.ram_demon_circle,)),
            Exhibit("Sorcerer", self.sorcerer,
                    (((-0.4, 0.7, -0.6, 0.0), (0.50, 0.55, 0.72, 1.0)),
                     ((0.5, 0.4, 0.8, 0.0), (0.34, 0.24, 0.46, 1.0)),
                     ((-0.3, -0.4, 0.6, 0.0), (0.22, 0.12, 0.30, 1.0))),
                    (0.08, 0.07, 0.12, 1.0), (0.03, 0.03, 0.06, 1.0), 0.5, 3.4),
            Exhibit("Lava bridge", self.lava_bridge,
                    (((0.0, 1.0, 0.0, 0.0), (0.0, 0.0, 0.0, 1.0)),) * 3,
                    (0.02, 0.02, 0.02, 1.0), (0.01, 0.008, 0.015, 1.0), 0.7, 7.5),
            Exhibit("Dark tower", self.tower_scene,
                    (((0.0, 1.0, 0.0, 0.0), (0.0, 0.0, 0.0, 1.0)),) * 3,
                    (0.02, 0.02, 0.03, 1.0), (0.025, 0.03, 0.06, 1.0), 2.5, 12.0),
            Exhibit("Pazure", self.pazure,
                    (((-0.5, 0.8, 0.6, 0.0), (0.95, 0.86, 0.76, 1.0)),
                     ((0.6, 0.4, -0.7, 0.0), (0.35, 0.40, 0.50, 1.0)),
                     ((0.3, -0.2, 0.8, 0.0), (0.25, 0.20, 0.18, 1.0))),
                    (0.18, 0.16, 0.15, 1.0), (0.08, 0.09, 0.11, 1.0), 0.55, 3.6),
            Exhibit("Vampire", self.vampire,
                    (((-0.5, 0.8, 0.7, 0.0), (0.70, 0.76, 0.95, 1.0)),
                     ((0.3, 0.3, -0.9, 0.0), (0.65, 0.12, 0.10, 1.0)),
                     ((0.4, -0.4, 0.6, 0.0), (0.22, 0.14, 0.30, 1.0))),
                    (0.11, 0.11, 0.15, 1.0), (0.03, 0.02, 0.05, 1.0), 0.6, 3.0),
            Exhibit("Werewolf", self.werewolf,
                    (((-0.4, 0.8, 0.7, 0.0), (0.78, 0.84, 0.95, 1.0)),
                     ((0.6, 0.3, -0.7, 0.0), (0.30, 0.50, 0.40, 1.0)),
                     ((0.3, -0.4, 0.8, 0.0), (0.22, 0.24, 0.26, 1.0))),
                    (0.14, 0.15, 0.17, 1.0), (0.06, 0.07, 0.08, 1.0), 0.8, 3.6),
            Exhibit("Gargoyles", self.gargoyles,
                    (((-0.4, 0.8, 0.7, 0.0), (0.85, 0.85, 0.88, 1.0)),
                     ((0.6, 0.4, -0.7, 0.0), (0.35, 0.38, 0.48, 1.0)),
                     ((0.3, -0.3, 0.8, 0.0), (0.25, 0.23, 0.22, 1.0))),
                    (0.16, 0.16, 0.18, 1.0), (0.05, 0.05, 0.07, 1.0), 0.45, 4.2)]
        for exhibit in self.exhibits:
            exhibit.creature.talking = True
        self.exhibit_index = 0
        self.orbit_distance = self.exhibit.orbit_distance
        self.running = True
        self.setup_gl()

    @property
    def exhibit(self):
        return self.exhibits[self.exhibit_index]

    def show_exhibit(self, index):
        self.exhibit_index = index % len(self.exhibits)
        self.orbit_distance = self.exhibit.orbit_distance
        self.apply_lighting()

    def apply_lighting(self):
        exhibit = self.exhibit
        glClearColor(*exhibit.background)
        for light, (_, color) in zip(self.light_ids, exhibit.lights):
            glLightfv(light, GL_DIFFUSE, color)
            glLightfv(light, GL_SPECULAR, color)
        glLightModelfv(GL_LIGHT_MODEL_AMBIENT, exhibit.ambient)

    def setup_gl(self):
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
        for light in self.light_ids:
            glEnable(light)
        self.apply_lighting()
        glShadeModel(GL_SMOOTH)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(self.field_of_view, self.window_size[0] / self.window_size[1], 0.05, 50.0)
        glMatrixMode(GL_MODELVIEW)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_SPACE:
                    self.spinning = not self.spinning
                elif event.key == pygame.K_w:
                    creature = self.exhibit.creature
                    if hasattr(creature, "flapping"):
                        creature.flapping = not creature.flapping
                elif event.key == pygame.K_c:
                    self.scene_camera = not self.scene_camera
                elif event.key == pygame.K_t:
                    for exhibit in self.exhibits:
                        exhibit.creature.talking = not exhibit.creature.talking
                elif event.key == pygame.K_a:
                    for exhibit in self.exhibits:
                        exhibit.creature.acting = not exhibit.creature.acting
                        exhibit.restart()
                elif event.key == pygame.K_p:
                    self.paused = not self.paused
                elif event.key == pygame.K_r:
                    self.exhibit.restart()
                elif event.key == pygame.K_TAB:
                    self.show_exhibit(self.exhibit_index + 1)
                elif event.key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5, pygame.K_6, pygame.K_7,
                                   pygame.K_8, pygame.K_9, pygame.K_0):
                    self.show_exhibit((event.key - pygame.K_1) % 10)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self.dragging = True
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                self.dragging = False
            elif event.type == pygame.MOUSEMOTION and self.dragging:
                self.orbit_yaw -= event.rel[0] * self.drag_radians_per_pixel
                self.orbit_pitch = max(-0.5, min(1.3, self.orbit_pitch + event.rel[1] * self.drag_radians_per_pixel))
            elif event.type == pygame.MOUSEWHEEL:
                self.orbit_distance *= self.zoom_step ** -event.y
                self.orbit_distance = max(self.closest_distance, min(self.farthest_distance, self.orbit_distance))

    def update(self, seconds):
        if not self.paused:
            self.exhibit.update(seconds)
        if self.spinning and not self.dragging:
            self.orbit_yaw += self.spin_radians_per_second * seconds

    def draw(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        horizontal = self.orbit_distance * math.cos(self.orbit_pitch)
        look_at_height = self.exhibit.look_at_height
        focus_x, focus_z = self.exhibit.creature.focus()
        eye = (focus_x + horizontal * math.sin(self.orbit_yaw),
               look_at_height + self.orbit_distance * math.sin(self.orbit_pitch),
               focus_z + horizontal * math.cos(self.orbit_yaw))
        target = (focus_x, look_at_height, focus_z)
        scene_view = getattr(self.exhibit.creature, "camera_view", None)
        if self.scene_camera and scene_view is not None:
            eye, target = scene_view()
        gluLookAt(*eye, *target, 0.0, 1.0, 0.0)
        for light, (direction, _) in zip(self.light_ids, self.exhibit.lights):
            glLightfv(light, GL_POSITION, direction)
        self.exhibit.render()
        pygame.display.flip()

    def run(self):
        while self.running:
            seconds = self.clock.tick(self.frames_per_second) / 1000.0
            self.handle_events()
            self.update(seconds)
            self.draw()
            pygame.display.set_caption(self.caption.format(self.exhibit.name, self.clock.get_fps()))
        pygame.quit()


if __name__ == "__main__":
    FantasyTest().run()
