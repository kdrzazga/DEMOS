import math
import os
import random
import sys
import time

import pygame
from pygame.locals import DOUBLEBUF, OPENGL
from OpenGL.GL import *
from OpenGL.GLU import gluLookAt, gluPerspective, gluSphere

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from lib.three_mirrors.mirror_renderer import MirrorRenderer, ReflectorSet
from lib.urban.glass import GlassStreet, GlassStyle, TowerPlan, TowerTier
from lib.urban.shapes import Shapes
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


class NightGround:

    def __init__(self, half_extent):
        self.half_extent = half_extent
        self.cell_size = 3.0
        self.color = (0.06, 0.065, 0.075)
        self.surface = None

    def prepare(self):
        if self.surface is None:
            self.surface = DisplayList(self._emit)

    def draw(self):
        self.surface.call()

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


class OrbitCamera:

    def __init__(self, target, distance, lowest_height, highest_height):
        self.target = target
        self.distance = distance
        self.lowest_height = lowest_height
        self.highest_height = highest_height
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


class GlassPalette:

    def standard(self):
        return GlassStyle()

    def greener(self):
        style = GlassStyle()
        style.pane_tint = (0.48, 0.8, 0.95)
        style.column_width = 1.1
        return style

    def darker(self):
        style = GlassStyle()
        style.pane_tint = (0.42, 0.62, 0.9)
        style.lit_pane_chance = 0.08
        style.floor_height = 0.95
        return style

    def all_styles(self):
        return (self.standard(), self.greener(), self.darker())


class NightScene:

    def __init__(self, name, streets, ground, camera, fog_density):
        self.name = name
        self.streets = streets
        self.ground = ground
        self.camera = camera
        self.fog_density = fog_density
        self.ambient = (0.02, 0.025, 0.04, 1.0)
        self.side_glow = (0.1, 0.2, 0.45, 1.0)
        self.flood_distance = 11.0
        self.flood_height = 0.6
        self.light_slots = (GL_LIGHT0, GL_LIGHT1, GL_LIGHT2, GL_LIGHT3, GL_LIGHT4, GL_LIGHT5, GL_LIGHT6, GL_LIGHT7)
        self.slots_taken = 0
        self.orbs = []
        self.flood_lights = []
        self.shapes = None
        self.reflector_set = ReflectorSet([facade for street in streets for facade in street.reflectors()])

    def _take_slot(self):
        if self.slots_taken == len(self.light_slots):
            return None
        slot = self.light_slots[self.slots_taken]
        self.slots_taken += 1
        return slot

    def add_orb(self, orb):
        orb.color = self.side_glow
        orb.slot = self._take_slot()
        self.orbs.append(orb)

    def flood_frontages(self, frontages):
        for frontage in frontages:
            slot = self._take_slot()
            if slot is not None:
                self.flood_lights.append(FloodLight(slot, self._flood_position(frontage), frontage.center))

    def _flood_position(self, frontage):
        ahead = frontage.center + frontage.facing * self.flood_distance
        return Vector3(ahead.x, self.flood_height, ahead.z)

    def every_light(self):
        return self.orbs + self.flood_lights

    def prepare(self):
        self.shapes = Shapes()
        self.ground.prepare()
        for street in self.streets:
            street.prepare()

    def configure(self, night):
        glFogf(GL_FOG_DENSITY, self.fog_density)
        glFogfv(GL_FOG_COLOR, night)
        glLightModelfv(GL_LIGHT_MODEL_AMBIENT, self.ambient)
        glLightModeli(GL_LIGHT_MODEL_LOCAL_VIEWER, GL_TRUE)
        for slot in self.light_slots:
            glDisable(slot)
        for light in self.every_light():
            light.configure(self.shapes)

    def change_blur(self, step):
        blur = self.blur + step
        for street in self.streets:
            street.set_blur(blur)

    @property
    def blur(self):
        return self.streets[0].blur

    @property
    def flood_lights_on(self):
        return self.flood_lights[0].switched_on

    def toggle_flood_lights(self):
        switched_on = not self.flood_lights_on
        for flood_light in self.flood_lights:
            flood_light.switch(switched_on)

    def update(self, seconds):
        for street in self.streets:
            street.update(seconds)
        for orb in self.orbs:
            orb.update(seconds)
        self.camera.update(seconds)

    def illuminate(self):
        glEnable(GL_LIGHTING)
        for light in self.every_light():
            light.illuminate()

    def draw(self):
        self.ground.draw()
        for street in self.streets:
            street.draw()
        for light in self.every_light():
            light.draw()


class StreetSceneBuilder:

    def __init__(self, palette):
        self.palette = palette

    def build(self):
        street = GlassStreet.centered([
            TowerPlan([TowerTier(7.0, 9.0, 20.0)], self.palette.standard(), seed=3),
            TowerPlan([TowerTier(9.0, 10.0, 28.0), TowerTier(6.5, 7.0, 8.0)], self.palette.greener(), seed=8),
            TowerPlan([TowerTier(6.0, 8.0, 16.0)], self.palette.darker(), seed=11),
            TowerPlan([TowerTier(10.0, 11.0, 34.0), TowerTier(7.0, 8.0, 10.0), TowerTier(4.0, 4.0, 5.0)],
                      self.palette.standard(), seed=5),
            TowerPlan([TowerTier(8.0, 9.0, 24.0)], self.palette.greener(), seed=13),
            TowerPlan([TowerTier(7.5, 9.0, 30.0), TowerTier(5.0, 6.0, 6.0)], self.palette.darker(), seed=21),
        ], gap=1.2, front_line=0.0)
        camera = OrbitCamera(Vector3(0.0, 18.0, -4.0), 64.0, 4.0, 30.0)
        scene = NightScene("Street", [street], NightGround(120.0), camera, fog_density=0.009)
        scene.flood_frontages(street.frontages)
        scene.add_orb(BlueLight(Vector3(0.0, 5.0, -4.0), 34.0, 0.3, 0.0, 2.0, 0.6))
        scene.add_orb(BlueLight(Vector3(0.0, 20.0, -4.0), 31.0, -0.22, math.pi, 10.0, 0.25))
        return scene


class CityLine:

    def __init__(self, towers_per_side, front_line, height_range):
        self.towers_per_side = towers_per_side
        self.front_line = front_line
        self.height_range = height_range


class CitySceneBuilder:

    def __init__(self, palette):
        self.palette = palette
        self.avenue_width = 16.0
        self.side_road_width = 14.0
        self.side_line_towers = 4
        self.side_line_floods = 2
        self.line_flood_counts = (3, 1, 1)
        self.side_line_heights = (20.0, 40.0)
        self.lines = (CityLine(6, 0.0, (16.0, 34.0)),
                      CityLine(3, -30.0, (26.0, 46.0)),
                      CityLine(1, -60.0, (40.0, 60.0)))
        self.gap = 1.2
        self.width_range = (6.0, 10.0)
        self.depth_range = (8.0, 12.0)
        self.setback_height_range = (5.0, 12.0)
        self.setback_shrink = 0.72
        self.most_setbacks = 2
        self.orb_margin = 12.0
        self.camera_margin = 50.0
        self.randomness = random.Random(2026)
        self.planned = 0

    def build(self):
        streets = []
        for line in self.lines:
            streets.extend(self._split_line(line))
        streets.append(self._side_line(streets[0]))
        towers = [tower for street in streets for tower in street.towers]
        center = self._center_of(towers)
        reach = max(math.hypot(tower.x - center.x, tower.z - center.z) for tower in towers) + self.orb_margin
        camera = OrbitCamera(Vector3(center.x, 22.0, center.z), reach + self.camera_margin, 10.0, 60.0)
        camera.orbit_speed = 0.05
        scene = NightScene("City", streets, NightGround(220.0), camera, fog_density=0.0045)
        scene.flood_frontages(self._lit_frontages(streets))
        scene.add_orb(BlueLight(Vector3(center.x, 8.0, center.z), reach, 0.18, 0.0, 4.0, 0.5))
        scene.add_orb(BlueLight(Vector3(center.x, 34.0, center.z), reach - 4.0, -0.12, math.pi, 12.0, 0.2))
        return scene

    def _lit_frontages(self, streets):
        line_streets = [streets[index:index + 2] for index in range(0, 2 * len(self.lines), 2)]
        side_street = streets[-1]
        chosen = []
        for halves, flood_count in zip(line_streets, self.line_flood_counts):
            line_frontages = [frontage for half in halves for frontage in half.frontages]
            chosen.extend(self._spread(line_frontages, flood_count, lambda frontage: frontage.center.x))
        chosen.extend(self._spread(side_street.frontages, self.side_line_floods, lambda frontage: frontage.center.z))
        return chosen

    def _spread(self, frontages, count, position_of):
        if count == 1:
            return [max(frontages, key=lambda frontage: frontage.height)]
        first = min(position_of(frontage) for frontage in frontages)
        last = max(position_of(frontage) for frontage in frontages)
        remaining = list(frontages)
        chosen = []
        for slot in range(count):
            target = first + (last - first) * (slot + 0.5) / count
            nearest = min(remaining, key=lambda frontage: abs(position_of(frontage) - target))
            remaining.remove(nearest)
            chosen.append(nearest)
        return chosen

    def _center_of(self, towers):
        xs = [tower.x for tower in towers]
        zs = [tower.z for tower in towers]
        return Vector3((min(xs) + max(xs)) / 2.0, 0.0, (min(zs) + max(zs)) / 2.0)

    def _split_line(self, line):
        along = Vector3(1.0, 0.0, 0.0)
        facing = Vector3(0.0, 0.0, 1.0)
        half_avenue = self.avenue_width / 2.0
        left_plans = self._plans(line.towers_per_side, line.height_range)
        right_plans = self._plans(line.towers_per_side, line.height_range)
        left_start = Vector3(-half_avenue - GlassStreet.length_of(left_plans, self.gap), 0.0, line.front_line)
        right_start = Vector3(half_avenue, 0.0, line.front_line)
        return [GlassStreet(left_plans, self.gap, left_start, along, facing),
                GlassStreet(right_plans, self.gap, right_start, along, facing)]

    def _side_line(self, first_line_left):
        front_x = first_line_left.front_start.x - self.side_road_width
        plans = self._plans(self.side_line_towers, self.side_line_heights)
        start = Vector3(front_x, 0.0, first_line_left.front_start.z + GlassStreet.length_of(plans, self.gap))
        return GlassStreet(plans, self.gap, start, Vector3(0.0, 0.0, -1.0), Vector3(1.0, 0.0, 0.0))

    def _plans(self, count, height_range):
        return [self._plan(height_range) for _ in range(count)]

    def _plan(self, height_range):
        width = round(self.randomness.uniform(*self.width_range) * 2.0) / 2.0
        depth = round(self.randomness.uniform(*self.depth_range) * 2.0) / 2.0
        tiers = [TowerTier(width, depth, round(self.randomness.uniform(*height_range)))]
        for _ in range(self.randomness.randint(0, self.most_setbacks)):
            previous = tiers[-1]
            tiers.append(TowerTier(previous.width * self.setback_shrink, previous.depth * self.setback_shrink,
                                   round(self.randomness.uniform(*self.setback_height_range))))
        style = self.randomness.choice(self.palette.all_styles())
        self.planned += 1
        return TowerPlan(tiers, style, seed=self.planned)


class ReflectionGovernor:

    def __init__(self, renderer, frames_per_second):
        self.renderer = renderer
        self.target_frame_seconds = 1.0 / frames_per_second
        self.slow_ratio = 1.12
        self.fast_ratio = 1.03
        self.smoothing = 0.1
        self.fewest = 2
        self.most = 16
        self.cut_after = 0.5
        self.grow_after = 2.0
        self.smoothed_frame_seconds = self.target_frame_seconds
        self.since_change = 0.0
        self.renderer.reflection_budget = 8

    def observe(self, frame_seconds):
        self.smoothed_frame_seconds += (frame_seconds - self.smoothed_frame_seconds) * self.smoothing
        self.since_change += frame_seconds
        budget = self.renderer.reflection_budget
        if self.is_slow() and self.since_change >= self.cut_after and budget > self.fewest:
            self._settle(budget - 1)
        elif self.is_fast() and self.since_change >= self.grow_after and budget < self.most:
            self._settle(budget + 1)

    def is_slow(self):
        return self.smoothed_frame_seconds > self.target_frame_seconds * self.slow_ratio

    def is_fast(self):
        return self.smoothed_frame_seconds < self.target_frame_seconds * self.fast_ratio

    def _settle(self, budget):
        self.renderer.reflection_budget = budget
        self.since_change = 0.0

    @property
    def frames_per_second(self):
        return 1.0 / max(self.smoothed_frame_seconds, 1e-6)


class GlassTowersTest:

    def __init__(self):
        self.window_size = (1280, 720)
        self.frames_per_second = 60
        self.longest_step = 0.1
        self.night = (0.008, 0.01, 0.02, 1.0)
        self.field_of_view = 50.0
        self.blur_step = 0.05
        self.blur_keys = (pygame.K_PLUS, pygame.K_EQUALS, pygame.K_KP_PLUS)
        self.sharpen_keys = (pygame.K_MINUS, pygame.K_KP_MINUS)
        self.caption_interval = 0.5
        self.caption = ("Glass Towers [{}] {:.0f} fps - reflections: {} (walls {}), blur: {:.2f}, flood lights: {}  "
                        "(TAB scene, UP/DOWN reflections, +/- blur, F flood lights, SPACE camera, ESC quit)")
        pygame.init()
        pygame.display.gl_set_attribute(pygame.GL_STENCIL_SIZE, 8)
        pygame.display.set_mode(self.window_size, DOUBLEBUF | OPENGL)
        pygame.display.set_caption("Glass Towers - building scenes...")
        self.clock = pygame.time.Clock()
        self.renderer = MirrorRenderer(max_reflections=1, reflection_limit=2)
        self.governor = ReflectionGovernor(self.renderer, self.frames_per_second)
        self.init_gl()
        palette = GlassPalette()
        self.scenes = [StreetSceneBuilder(palette).build(), CitySceneBuilder(palette).build()]
        for scene in self.scenes:
            scene.prepare()
        self.scene_index = 0
        self.scene.configure(self.night)
        self.since_caption = self.caption_interval
        self.running = True

    @property
    def scene(self):
        return self.scenes[self.scene_index]

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
        glHint(GL_FOG_HINT, GL_FASTEST)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(self.field_of_view, self.window_size[0] / self.window_size[1], 0.5, 500.0)
        glMatrixMode(GL_MODELVIEW)

    def next_scene(self):
        self.scene_index = (self.scene_index + 1) % len(self.scenes)
        self.scene.configure(self.night)

    def show_caption(self):
        pygame.display.set_caption(self.caption.format(
            self.scene.name, self.governor.frames_per_second, self.renderer.max_reflections,
            self.renderer.reflection_budget, self.scene.blur, "on" if self.scene.flood_lights_on else "off"))

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                self.handle_key(event.key)

    def handle_key(self, key):
        if key == pygame.K_ESCAPE:
            self.running = False
        elif key == pygame.K_TAB:
            self.next_scene()
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
            self.scene.camera.toggle_pause()

    def draw(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT | GL_STENCIL_BUFFER_BIT)
        glLoadIdentity()
        self.scene.camera.look()
        self.renderer.render(self.scene.reflector_set, self.scene, self.scene.camera.eye())
        pygame.display.flip()

    def refresh_caption(self, seconds):
        self.since_caption += seconds
        if self.since_caption >= self.caption_interval:
            self.since_caption = 0.0
            self.show_caption()

    def run(self):
        previous_moment = time.perf_counter()
        while self.running:
            self.clock.tick(self.frames_per_second)
            moment = time.perf_counter()
            frame_seconds = moment - previous_moment
            previous_moment = moment
            step = min(frame_seconds, self.longest_step)
            self.handle_events()
            self.scene.update(step)
            self.draw()
            self.governor.observe(frame_seconds)
            self.refresh_caption(frame_seconds)
        pygame.quit()


if __name__ == "__main__":
    GlassTowersTest().run()
