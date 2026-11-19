import math
import random

from OpenGL.GL import *

from lib.plants.mushroom import (CameraBasis, ColorMesh, GlowSprite, Mushroom, MushroomShape,
                                 PaletteTransition, PaletteVariation)
from lib.vector3 import Vector3


class ForestFloor:
    def __init__(self, bounds, generator):
        self.left, self.right, self.back, self.front = bounds
        self.columns = 44
        self.rows = 36
        self.base = Vector3(0.045, 0.02, 0.06)
        self.tint_strength = 0.08
        self.mesh = self.build(generator)

    def build(self, generator):
        mesh = ColorMesh(GL_TRIANGLES)
        rows = [[self.add_vertex(mesh, generator, row, column) for column in range(self.columns + 1)]
                for row in range(self.rows + 1)]
        for nearer, farther in zip(rows, rows[1:]):
            mesh.band(nearer, farther)
        return mesh.seal()

    def add_vertex(self, mesh, generator, row, column):
        x = self.left + (self.right - self.left) * column / self.columns
        z = self.back + (self.front - self.back) * row / self.rows
        shade = generator.uniform(0.6, 1.4)
        return mesh.vertex(Vector3(x, generator.uniform(-0.06, 0.02), z),
                           ColorMesh.weights(cap=self.tint_strength * shade),
                           self.base * shade)

    def tint(self, palette):
        self.mesh.recolor(palette.matrix())

    def draw(self):
        self.mesh.draw()


class Blade:
    def __init__(self, x, z, generator):
        self.x = x
        self.z = z
        self.height = generator.uniform(0.15, 0.6)
        self.width = self.height * generator.uniform(0.12, 0.25)
        self.heading = generator.uniform(0.0, math.tau)
        self.curl = generator.uniform(0.2, 0.7)
        self.segments = 4
        self.root_color = Vector3(0.025, 0.012, 0.035)
        self.tip_strength = generator.uniform(0.25, 0.5)

    def add_to(self, mesh):
        forward_x, forward_z = math.cos(self.heading), math.sin(self.heading)
        side_x, side_z = -forward_z, forward_x
        left, right = [], []
        for step in range(self.segments + 1):
            progress = step / self.segments
            lean = self.curl * self.height * progress * progress
            center_x, center_z = self.x + forward_x * lean, self.z + forward_z * lean
            height = self.height * progress
            half_width = self.width * 0.5 * (1.0 - progress)
            weights = ColorMesh.weights(cap=self.tip_strength * progress)
            bias = self.root_color * (1.0 - progress)
            left.append(mesh.vertex(Vector3(center_x - side_x * half_width, height, center_z - side_z * half_width),
                                    weights, bias))
            right.append(mesh.vertex(Vector3(center_x + side_x * half_width, height, center_z + side_z * half_width),
                                     weights, bias))
        mesh.band(left, right)


class Undergrowth:
    def __init__(self, mushrooms, bounds, generator):
        left, right, back, front = bounds
        self.scattered_count = 220
        blades = []
        for mushroom in mushrooms:
            for _ in range(int(6 + 10 * mushroom.shape.cap_radius)):
                angle = generator.uniform(0.0, math.tau)
                distance = mushroom.shape.stem_radius + generator.uniform(0.15, 1.2) * mushroom.shape.cap_radius
                blades.append(Blade(mushroom.x + math.cos(angle) * distance,
                                    mushroom.z + math.sin(angle) * distance, generator))
        for _ in range(self.scattered_count):
            blades.append(Blade(generator.uniform(left, right), generator.uniform(back, front), generator))
        mesh = ColorMesh(GL_TRIANGLES)
        for blade in blades:
            blade.add_to(mesh)
        self.mesh = mesh.seal()

    def tint(self, palette):
        self.mesh.recolor(palette.matrix())

    def draw(self):
        self.mesh.draw()


class Spore:
    def __init__(self, bounds, slot, generator):
        self.left, self.right, self.bottom, self.top, self.back, self.front = bounds
        self.slot = slot
        self.generator = generator
        self.core_color = Vector3(1.0, 1.0, 1.0)
        self.respawn(generator.uniform(self.bottom, self.top))

    def respawn(self, height):
        generator = self.generator
        self.x = generator.uniform(self.left, self.right)
        self.y = height
        self.z = generator.uniform(self.back, self.front)
        self.rise = generator.uniform(0.08, 0.35)
        self.drift_amount = generator.uniform(0.05, 0.25)
        self.drift_speed = generator.uniform(0.3, 0.9)
        self.drift_phase = generator.uniform(0.0, math.tau)
        self.size = generator.uniform(0.025, 0.07)
        self.twinkle_speed = generator.uniform(1.5, 4.0)
        self.twinkle_phase = generator.uniform(0.0, math.tau)

    def update(self, delta, elapsed):
        angle = elapsed * self.drift_speed + self.drift_phase
        self.x += math.cos(angle) * self.drift_amount * delta
        self.z += math.sin(angle * 0.7) * self.drift_amount * delta
        self.y += self.rise * delta
        if self.y > self.top:
            self.respawn(self.bottom)

    def draw(self, elapsed, camera, sprite, palettes):
        twinkle = 0.55 + 0.45 * math.sin(elapsed * self.twinkle_speed + self.twinkle_phase)
        position = Vector3(self.x, self.y, self.z)
        sprite.draw(position, self.size * 4.0, palettes[self.slot].glow, 0.35 * twinkle, camera)
        sprite.draw(position, self.size, self.core_color, 0.8 * twinkle, camera)


class Bokeh:
    def __init__(self, position, radius, slot, generator):
        self.position = position
        self.radius = radius
        self.slot = slot
        self.shade = generator.uniform(0.4, 1.0)
        self.alpha = generator.uniform(0.05, 0.18)
        self.pulse_speed = generator.uniform(0.1, 0.4)
        self.pulse_phase = generator.uniform(0.0, math.tau)

    def draw(self, elapsed, camera, sprite, palettes):
        pulse = 0.7 + 0.3 * math.sin(elapsed * self.pulse_speed + self.pulse_phase)
        sprite.draw(self.position, self.radius, palettes[self.slot].glow * self.shade, self.alpha * pulse, camera)


class BokehBackdrop:
    def __init__(self, slot_count, generator):
        self.count = 70
        self.lights = [Bokeh(Vector3(generator.uniform(-30.0, 30.0), generator.uniform(-2.0, 16.0), generator.uniform(-45.0, -28.0)),
                             generator.uniform(0.6, 2.2),
                             generator.randrange(slot_count),
                             generator)
                       for _ in range(self.count)]

    def draw(self, elapsed, camera, sprite, palettes):
        for light in self.lights:
            light.draw(elapsed, camera, sprite, palettes)


class Planting:
    def __init__(self, mushroom, slot, variation):
        self.mushroom = mushroom
        self.slot = slot
        self.variation = variation

    def refresh(self, palettes):
        self.mushroom.tint(self.variation.apply(palettes[self.slot]))


class MushroomForest:
    def __init__(self, palettes, seed):
        self.generator = random.Random(seed)
        self.left = -12.0
        self.right = 12.0
        self.back = -18.0
        self.front = 3.0
        self.hero_count = 3
        self.hero_scale = (2.0, 2.6)
        self.hero_x = (-8.0, 8.0)
        self.hero_z = (-12.0, -3.0)
        self.cluster_count = 8
        self.cluster_size = (3, 7)
        self.cluster_spread = 2.5
        self.cluster_scale = (0.35, 1.3)
        self.placement_attempts = 12
        self.spore_count = 140
        self.spore_ceiling = 7.0
        self.slot_count = 4
        self.recolor_duration = 2.5
        self.fog_color = (0.035, 0.01, 0.06, 1.0)
        self.fog_start = 8.0
        self.fog_end = 34.0
        self.sky_color = self.fog_color
        self.elapsed = 0.0
        self.sprite = GlowSprite(20)
        self.slots = [PaletteTransition(palettes[index % len(palettes)]) for index in range(self.slot_count)]
        self.plantings = self.plant()
        self.mushrooms = [planting.mushroom for planting in self.plantings]
        for mushroom in self.mushrooms:
            mushroom.prepare()
        self.floor = ForestFloor((self.left - 20.0, self.right + 20.0, self.back - 30.0, self.front + 8.0), self.generator)
        self.undergrowth = Undergrowth(self.mushrooms, (self.left, self.right, self.back, self.front), self.generator)
        spore_bounds = (self.left, self.right, 0.0, self.spore_ceiling, self.back, self.front)
        self.spores = [Spore(spore_bounds, self.generator.randrange(self.slot_count), self.generator)
                       for _ in range(self.spore_count)]
        self.bokeh = BokehBackdrop(self.slot_count, self.generator)
        self.ambient_key = None
        self.refresh()

    def palettes(self):
        return [slot.current for slot in self.slots]

    def plant(self):
        generator = self.generator
        plantings = []
        for hero in range(self.hero_count):
            self.try_plant(plantings, self.hero_x, self.hero_z, self.hero_scale, hero % self.slot_count)
        for cluster in range(self.cluster_count):
            center_x = generator.uniform(self.left + 2.0, self.right - 2.0)
            center_z = generator.uniform(self.back + 2.0, self.front - 2.0)
            spread = self.cluster_spread
            for _ in range(generator.randint(*self.cluster_size)):
                self.try_plant(plantings, (center_x - spread, center_x + spread),
                               (center_z - spread, center_z + spread), self.cluster_scale, cluster % self.slot_count)
        return plantings

    def try_plant(self, plantings, x_range, z_range, scale_range, slot):
        generator = self.generator
        for _ in range(self.placement_attempts):
            shape = MushroomShape.random(generator, generator.uniform(*scale_range))
            variation = PaletteVariation(generator)
            candidate = Mushroom(generator.uniform(*x_range), generator.uniform(*z_range), shape,
                                 variation.apply(self.slots[slot].current), generator.randrange(1 << 30))
            if all(self.apart(candidate, planting.mushroom) for planting in plantings):
                plantings.append(Planting(candidate, slot, variation))
                return

    def apart(self, first, second):
        base_distance = math.hypot(first.x - second.x, first.z - second.z)
        if base_distance < (first.shape.stem_radius + second.shape.stem_radius) * 2.0 + 0.2:
            return False
        first_low, first_high = first.cap_span()
        second_low, second_high = second.cap_span()
        first_cap, second_cap = first.cap_center(), second.cap_center()
        cap_distance = math.hypot(first_cap.x - second_cap.x, first_cap.z - second_cap.z)
        caps_level = first_low < second_high and second_low < first_high
        if caps_level and cap_distance < 0.9 * (first.shape.cap_radius + second.shape.cap_radius):
            return False
        return not (self.pierces(first, second) or self.pierces(second, first))

    def pierces(self, capped, other):
        cap = capped.cap_center()
        distance = math.hypot(cap.x - other.x, cap.z - other.z)
        return other.stem_top() > capped.cap_span()[0] and distance < capped.shape.cap_radius + other.shape.stem_radius

    def recolor(self, palettes):
        for index, slot in enumerate(self.slots):
            slot.retarget(palettes[index % len(palettes)], self.recolor_duration)

    def refresh(self):
        palettes = self.palettes()
        for planting in self.plantings:
            planting.refresh(palettes)
        ambient = palettes[0]
        if ambient.key() != self.ambient_key:
            self.ambient_key = ambient.key()
            self.floor.tint(ambient)
            self.undergrowth.tint(ambient)

    def update(self, delta):
        self.elapsed += delta
        for slot in self.slots:
            slot.update(delta)
        self.refresh()
        for spore in self.spores:
            spore.update(delta, self.elapsed)

    def draw(self):
        camera = CameraBasis.from_modelview()
        glPushAttrib(GL_ALL_ATTRIB_BITS)
        glDisable(GL_LIGHTING)
        glDisable(GL_TEXTURE_2D)
        glDisable(GL_CULL_FACE)
        glEnable(GL_DEPTH_TEST)
        glDepthMask(GL_TRUE)
        glShadeModel(GL_SMOOTH)
        self.draw_solid()
        self.draw_glow(camera)
        glPopAttrib()

    def draw_solid(self):
        glEnable(GL_FOG)
        glFogi(GL_FOG_MODE, GL_LINEAR)
        glFogf(GL_FOG_START, self.fog_start)
        glFogf(GL_FOG_END, self.fog_end)
        glFogfv(GL_FOG_COLOR, self.fog_color)
        self.floor.draw()
        self.undergrowth.draw()
        for mushroom in self.mushrooms:
            mushroom.draw_body(self.elapsed)

    def draw_glow(self, camera):
        palettes = self.palettes()
        glFogfv(GL_FOG_COLOR, (0.0, 0.0, 0.0, 1.0))
        glEnable(GL_BLEND)
        glDepthMask(GL_FALSE)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE)
        for mushroom in self.mushrooms:
            mushroom.draw_ground_glow(self.elapsed)
        for mushroom in self.mushrooms:
            mushroom.draw_glow(self.elapsed, camera)
        for spore in self.spores:
            spore.draw(self.elapsed, camera, self.sprite, palettes)
        glDisable(GL_FOG)
        self.bokeh.draw(self.elapsed, camera, self.sprite, palettes)
