import math

import numpy
from OpenGL.GL import *

from demos.divided.chairs import Chair, build_chairs
from demos.divided.dead_land import DeadLandScene
from lib.animals.dragon import StatueMesh, catmull_rom, mottling, surface_normals, unit_or_fallback
from lib.fantasy.anatomy import smoothstep
from lib.fantasy.scenes.bridge import LavaBridgeScene, SineNoise
from lib.fantasy.scenes.tower import CameraFlight, TowerScene
from lib.fantasy.sorcerer import Sorcerer
from lib.fantasy.tower import DarkTower, DarkTowerModel
from lib.fantasy.vampire import Vampire, VioletVampireModel
from lib.fantasy.werewolf import Werewolf


def draw_mesh(positions, normals, colors, indices):
    glVertexPointer(3, GL_FLOAT, 0, positions)
    glNormalPointer(GL_FLOAT, 0, normals)
    glColorPointer(3, GL_FLOAT, 0, colors)
    glDrawElements(GL_TRIANGLES, len(indices), GL_UNSIGNED_INT, indices)


class TowerWithRoom(DarkTowerModel):

    def __init__(self):
        self.radius_scale = 5.0
        self.added_floors = 5
        self.floor_height = 1.72
        self.floor_gap = 0.18
        self.floor_taper = 0.05
        self.main_flare = 0.3
        self.main_pilaster_count = 24
        self.main_dome_height = 2.5
        self.main_spire_length = 2.25
        self.unique_floors = 2
        self.horned_floors = {0: (16, 1.75)}
        self.repeated_horns = (12, 1.2)
        self.horned_repeats = (0, 2, 4)
        self.horn_clearance = 0.5
        self.floor_window_size = (0.16, 0.3)
        self.floor_window_angles = (0.25, 2.35, -1.85)
        self.floor_window_turn = 0.5
        self.room_window = (0, 0.25, 3.6, 0.16, 0.3)
        self.room_wall_inset = 0.04
        self.room_ceiling_gap = 0.05
        self.room_stone = (0.13, 0.11, 0.10)
        self.room_floor_color = (0.15, 0.12, 0.09)
        self.opening_depth = 0.12
        self.sections = []
        self.floor_instances = []
        self.floor_module = None
        self.floor_glass_module = None
        self.horn_module = None
        super().__init__()
        self.body = self.without_opening(self.body)
        self.glass = self.without_opening(self.glass)
        self.room = self.build_room()

    def enlarge(self):
        main, side = self.towers
        old_radius = main["lower_radius"]
        new_radius = old_radius * self.radius_scale
        bottom, top = -self.foundation_depth, main["ledges"][0]
        self.sections = [(bottom, top, new_radius)]
        upper_radius = main["upper_radius"] * self.radius_scale
        for floor in range(1 + self.added_floors):
            bottom = top + self.floor_gap
            top = bottom + self.floor_height
            self.sections.append((bottom, top, upper_radius - self.floor_taper * floor))
        side = dict(side, center=self.pushed_out(side["center"], new_radius - old_radius))
        self.towers = (dict(main, lower_radius=new_radius, upper_radius=upper_radius), side)
        self.annexes = tuple((self.pushed_out(center, new_radius - old_radius), radius, height)
                             for center, radius, height in self.annexes)
        width, height = self.floor_window_size
        main_windows = [(0, angle, window_height, width, height) for _, angle, window_height, _, _ in
                        (window for window in self.windows[1:] if window[0] == 0)]
        side_windows = [window for window in self.windows if window[0] == 1]
        self.windows = (self.room_window, *main_windows, *side_windows)

    @staticmethod
    def pushed_out(center, distance):
        center = numpy.asarray(center, dtype=numpy.float64)
        direction = center / max(float(numpy.linalg.norm(center)), 1e-9)
        return tuple(center + direction * distance)

    def section_at(self, height):
        for section in self.sections:
            if height <= section[1]:
                return section
        return self.sections[-1]

    def window_place(self, window):
        tower_index, angle, height, half_width, half_height = window
        if tower_index != 0:
            return super().window_place(window)
        radius = self.section_at(height)[2]
        outward = numpy.array((math.sin(angle), 0.0, math.cos(angle)))
        across = numpy.array((math.cos(angle), 0.0, -math.sin(angle)))
        center = numpy.asarray(self.towers[0]["center"], dtype=numpy.float64) + outward * radius + (0.0, height, 0.0)
        return center, outward, across, half_width, half_height

    def horns(self, center, radius, height, count, length, clear_angle=None):
        center = numpy.asarray(center, dtype=numpy.float64)
        for index in range(count):
            angle = 2.0 * math.pi * index / count + 0.2
            if clear_angle is not None and abs(math.remainder(angle - clear_angle, 2.0 * math.pi)) < self.horn_clearance:
                continue
            outward = numpy.array((math.sin(angle), 0.0, math.cos(angle)))
            up = numpy.array((0.0, 1.0, 0.0))
            base = center + outward * radius + up * height
            path = (base, base + outward * 0.3 * length + up * 0.03 * length,
                    base + outward * 0.6 * length + up * 0.25 * length, base + outward * 0.72 * length + up * 0.7 * length)
            centers = catmull_rom(path, 24)
            along = numpy.linspace(0.0, 1.0, len(centers))
            radii = length * 0.075 * (1.0 - along) ** 0.9 + 0.002
            colors = (numpy.asarray(self.horn_base) * (1.0 - along[:, None, None])
                      + numpy.asarray(self.horn_tip) * along[:, None, None])
            self.sculptor.sweep(centers, radii, radii, colors, segments=12, mottle=0.04)

    def build_main_tower(self):
        center = self.towers[0]["center"]
        side_pilasters = self.pilaster_count
        self.pilaster_count = self.main_pilaster_count
        for floor, (bottom, top, radius) in enumerate(self.sections[:self.unique_floors]):
            self.brick_drum(center, radius, bottom, top)
            self.pilasters(center, radius, max(bottom, 0.0) + 0.1, top - 0.06)
            self.ledge(center, radius, top, self.main_flare)
            if floor in self.horned_floors:
                count, length = self.horned_floors[floor]
                self.horns(center, radius + self.main_flare * 0.8, top + 0.1, count, length, self.room_window[1])
        module_radius = self.sections[self.unique_floors][2]
        self.floor_module = self.built_apart(lambda: self.build_floor_module(module_radius))
        self.floor_glass_module = self.built_apart(lambda: self.build_floor_glass(module_radius))
        count, length = self.repeated_horns
        self.horn_module = self.built_apart(lambda: self.horns(
            (0.0, 0.0, 0.0), module_radius + self.main_flare * 0.8, self.floor_height + 0.1, count, length))
        self.pilaster_count = side_pilasters
        for repeat, (bottom, _, radius) in enumerate(self.sections[self.unique_floors:]):
            turn = math.degrees(self.floor_window_turn * (repeat + 1))
            self.floor_instances.append((bottom, radius / module_radius, turn, repeat in self.horned_repeats))
        _, top, radius = self.sections[-1]
        self.dome(center, radius + self.main_flare - 0.05, top + 0.2, self.main_dome_height, self.main_spire_length)

    def built_apart(self, builder):
        kept = self.mesh
        self.mesh = StatueMesh()
        self.sculptor.mesh = self.mesh
        builder()
        arrays = self.mesh.arrays()
        self.mesh = kept
        self.sculptor.mesh = kept
        return arrays

    def module_window_places(self, radius):
        half_width, half_height = self.floor_window_size
        for angle in self.floor_window_angles:
            outward = numpy.array((math.sin(angle), 0.0, math.cos(angle)))
            across = numpy.array((math.cos(angle), 0.0, -math.sin(angle)))
            yield outward * radius + (0.0, self.floor_height / 2.0, 0.0), outward, across, half_width, half_height

    def build_floor_module(self, radius):
        center = (0.0, 0.0, 0.0)
        self.brick_drum(center, radius, 0.0, self.floor_height)
        self.pilasters(center, radius, 0.1, self.floor_height - 0.06)
        self.ledge(center, radius, self.floor_height, self.main_flare)
        for place, outward, across, half_width, half_height in self.module_window_places(radius):
            self.arched_panel(place, outward, across, half_width + 0.025, half_height + 0.02, 0.006,
                              self.window_frame)

    def build_floor_glass(self, radius):
        for place, outward, across, half_width, half_height in self.module_window_places(radius):
            self.arched_panel(place, outward, across, half_width, half_height, 0.009, self.window_glow)

    def build_side_tower(self, tower):
        center = tower["center"]
        first, second = tower["ledges"]
        self.brick_drum(center, tower["lower_radius"], -self.foundation_depth, first)
        self.pilasters(center, tower["lower_radius"], 0.1, first - 0.06)
        self.ledge(center, tower["lower_radius"], first, tower["ledge_flare"])
        self.brick_drum(center, tower["upper_radius"], first + 0.18, second)
        self.pilasters(center, tower["upper_radius"], first + 0.25, second - 0.06)
        self.ledge(center, tower["upper_radius"], second, tower["ledge_flare"])
        lower_horns, upper_horns = tower["horns"]
        lower_length, upper_length = tower["horn_length"]
        self.horns(center, tower["lower_radius"] + tower["ledge_flare"] * 0.8, first + 0.1, lower_horns, lower_length)
        self.horns(center, tower["upper_radius"] + tower["ledge_flare"] * 0.8, second + 0.1, upper_horns,
                   upper_length)
        self.dome(center, tower["upper_radius"] + tower["ledge_flare"] - 0.05, second + 0.2, tower["dome_height"],
                  tower["spire_length"])

    def build_body(self):
        self.enlarge()
        self.build_main_tower()
        self.build_side_tower(self.towers[1])
        for center, radius, height in self.annexes:
            self.brick_drum(center, radius, -self.foundation_depth, height)
            self.lathe(center, ((radius + 0.02, height - 0.06), (radius + 0.025, height), (radius - 0.03, height),
                                (radius - 0.03, height - 0.04), (0.0, height - 0.04)), self.ledge_stone)
        for window in self.windows:
            center, outward, across, half_width, half_height = self.window_place(window)
            self.arched_panel(center, outward, across, half_width + 0.025, half_height + 0.02, 0.006,
                              self.window_frame)

    def opening(self):
        return self.window_place(self.windows[0])

    def room_heights(self):
        center, _, _, _, half_height = self.opening()
        _, top, _ = self.section_at(self.room_window[2])
        return center[1] - half_height - 0.02, top - self.room_ceiling_gap

    def room_radius(self):
        return self.section_at(self.room_window[2])[2] - self.room_wall_inset

    def without_opening(self, arrays):
        positions, normals, colors, indices = arrays
        center, outward, across, half_width, half_height = self.opening()
        triangles = indices.reshape(-1, 3)
        relative = positions[triangles].mean(axis=1) - center
        sideways = relative @ across
        upward = relative[:, 1]
        depth = relative @ outward
        top = half_height + numpy.sqrt(numpy.clip(half_width ** 2 - sideways ** 2, 0.0, None))
        inside = (numpy.abs(sideways) < half_width) & (upward > -half_height) & (upward < top) & (
                depth > -self.opening_depth)
        return positions, normals, colors, numpy.ascontiguousarray(triangles[~inside].reshape(-1))

    def build_room(self):
        mesh = StatueMesh()
        floor, ceiling = self.room_heights()
        radius = self.room_radius()
        _, _, _, half_width, _ = self.opening()
        window_angle = self.room_window[1]
        gap = half_width / radius + 0.02
        angle = numpy.linspace(window_angle + gap, window_angle + 2.0 * math.pi - gap, 160)[None, :]
        height = numpy.linspace(floor, ceiling, 12)[:, None]
        wall = numpy.stack((numpy.sin(angle) * radius * numpy.ones_like(height), height * numpy.ones_like(angle),
                            numpy.cos(angle) * radius * numpy.ones_like(height)), axis=-1)
        inward = -numpy.stack((numpy.sin(angle), numpy.zeros_like(angle), numpy.cos(angle)), axis=-1)
        mesh.add_grid(wall, numpy.broadcast_to(inward, wall.shape),
                      numpy.asarray(self.room_stone) * mottling(wall * 4.0, 0.25)[..., None])
        reach = numpy.linspace(0.0, radius, 16)[:, None]
        around = numpy.linspace(0.0, 2.0 * math.pi, 97)[None, :]
        for level, facing, color in ((floor, 1.0, self.room_floor_color), (ceiling, -1.0, self.room_stone)):
            disc = numpy.stack((numpy.sin(around) * reach, numpy.full((len(reach), around.shape[1]), level),
                                numpy.cos(around) * reach), axis=-1)
            mesh.add_grid(disc, numpy.broadcast_to((0.0, facing, 0.0), disc.shape),
                          numpy.asarray(color) * mottling(disc * 4.0, 0.25)[..., None])
        return mesh.arrays()


class StackedTower(DarkTower):

    def __init__(self, model):
        super().__init__(model)
        self.display_lists = None

    def compiled(self, arrays):
        number = glGenLists(1)
        glNewList(number, GL_COMPILE)
        self.draw(*arrays)
        glEndList()
        return number

    @staticmethod
    def floor_transform(bottom, scale, turn):
        glPushMatrix()
        glTranslatef(0.0, bottom, 0.0)
        glRotatef(turn, 0.0, 1.0, 0.0)
        glScalef(scale, 1.0, scale)

    @staticmethod
    def draw_glowing(arrays, strength):
        positions, _, colors, indices = arrays
        glVertexPointer(3, GL_FLOAT, 0, positions)
        glColorPointer(3, GL_FLOAT, 0, numpy.ascontiguousarray(numpy.clip(colors * strength, 0.0, 1.0)))
        glDrawElements(GL_TRIANGLES, len(indices), GL_UNSIGNED_INT, indices)

    def render(self):
        model = self.model
        glPushMatrix()
        glTranslatef(*self.position)
        glPushAttrib(GL_LIGHTING_BIT | GL_ENABLE_BIT)
        glEnable(GL_NORMALIZE)
        glDisable(GL_CULL_FACE)
        glEnable(GL_COLOR_MATERIAL)
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
        glLightModeli(GL_LIGHT_MODEL_COLOR_CONTROL, GL_SEPARATE_SPECULAR_COLOR)
        glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, self.specular)
        glMaterialf(GL_FRONT_AND_BACK, GL_SHININESS, self.shininess)
        glEnableClientState(GL_VERTEX_ARRAY)
        glEnableClientState(GL_NORMAL_ARRAY)
        glEnableClientState(GL_COLOR_ARRAY)
        if self.display_lists is None:
            self.display_lists = tuple(self.compiled(arrays) for arrays in (model.body, model.floor_module,
                                                                             model.horn_module))
        body, floor, horns = self.display_lists
        glCallList(body)
        for bottom, scale, turn, horned in model.floor_instances:
            self.floor_transform(bottom, scale, turn)
            glCallList(floor)
            if horned:
                glCallList(horns)
            glPopMatrix()
        glDisable(GL_LIGHTING)
        strength = self.window_strength()
        self.draw_glowing(model.glass, strength)
        for bottom, scale, turn, _ in model.floor_instances:
            self.floor_transform(bottom, scale, turn)
            self.draw_glowing(model.floor_glass_module, strength)
            glPopMatrix()
        glDisableClientState(GL_COLOR_ARRAY)
        glDisableClientState(GL_NORMAL_ARRAY)
        glDisableClientState(GL_VERTEX_ARRAY)
        glPopAttrib()
        glPopMatrix()


class BigTowerScene(TowerScene):

    def __init__(self):
        self.wide_plateau_radius = 5.2
        self.river_shift = 4.5
        self.wide_terrain_extent = ((-12.0, 13.0), (-12.0, 10.0))
        super().__init__()

    def river_center(self, depth):
        return super().river_center(depth) + self.river_shift

    def build_terrain(self):
        self.plateau_radius = self.wide_plateau_radius
        self.terrain_extent = self.wide_terrain_extent
        return super().build_terrain()


class Region:

    def __init__(self, scene, offset, scale, local_rect):
        self.scene = scene
        self.offset = numpy.asarray(offset, dtype=numpy.float64)
        self.scale = scale
        (left, right), (back, front) = local_rect
        self.rect = (self.offset[0] + scale * left, self.offset[0] + scale * right,
                     self.offset[2] + scale * back, self.offset[2] + scale * front)
        self.awake_distance = 70.0

    def to_world(self, point):
        return self.offset + self.scale * numpy.asarray(point, dtype=numpy.float64)

    def height(self, x, z):
        return self.scale * self.scene.ground_height((x - self.offset[0]) / self.scale,
                                                     (z - self.offset[2]) / self.scale)

    def clamped(self, x, z):
        left, right, back, front = self.rect
        return numpy.clip(x, left, right), numpy.clip(z, back, front)

    def distance_outside(self, x, z):
        inside_x, inside_z = self.clamped(x, z)
        return numpy.hypot(x - inside_x, z - inside_z)

    def edge_height(self, x, z):
        return self.height(*self.clamped(x, z))

    def contains(self, x, z):
        left, right, back, front = self.rect
        return (x > left) & (x < right) & (z > back) & (z < front)

    def awake(self, eye):
        return float(self.distance_outside(eye[0], eye[2])) < self.awake_distance

    def begin(self):
        glPushMatrix()
        glTranslatef(*self.offset)
        glScalef(self.scale, self.scale, self.scale)

    @staticmethod
    def end():
        glPopMatrix()

    def scaled_attenuation(self, attenuation):
        constant, linear, quadratic = attenuation
        return constant, linear / self.scale, quadratic / self.scale ** 2

    def river_lights(self):
        scene = self.scene
        lights = []
        for depth, strength in zip(scene.lava_light_depths, scene.lava_light_strengths()):
            local = (float(scene.river_center(depth)), float(scene.lava_level(depth)) + scene.lava_light_height, depth)
            lights.append((self.to_world(local), scene.lava_light_color * strength,
                           self.scaled_attenuation(scene.lava_light_attenuation)))
        return lights

    def update(self, seconds):
        self.scene.update(seconds)


class DeadLandRegion(Region):

    def __init__(self, scene):
        super().__init__(scene, (0.0, 0.0, 0.0), 1.0, scene.terrain_extent)

    def lava_lights(self):
        return self.scene.lava_lights()

    def static_meshes(self):
        return self.scene.static_meshes()

    def render_effects(self):
        self.scene.render_effects()


class TowerRegion(Region):

    def __init__(self, offset, scale):
        scene = BigTowerScene()
        scene.tower = StackedTower(TowerWithRoom())
        super().__init__(scene, offset, scale, scene.terrain_extent)
        self.room_light_color = numpy.array((1.0, 0.55, 0.22))
        self.room_light_attenuation = (0.4, 0.0, 0.5)
        self.sorcerer_height = 1.5
        self.sorcerer_back_from_window = 0.24
        self.room_light_back_from_window = 0.6
        model = scene.tower.model
        floor, ceiling = model.room_heights()
        window, outward = model.window_center()
        self.window = self.to_world(window)
        self.outward = outward
        lamp = window - outward * self.room_light_back_from_window
        self.room_light = self.to_world((lamp[0], (floor + ceiling) / 2.0, lamp[2]))
        self.sorcerer = Sorcerer(self.sorcerer_height)
        self.sorcerer.acting = False
        self.sorcerer.talking = True
        standing = window - outward * self.sorcerer_back_from_window
        self.sorcerer.position = tuple(self.to_world((standing[0], floor, standing[2])))
        self.sorcerer.yaw = math.atan2(outward[0], outward[2])
        self.werewolf_size = 1.3
        self.chair_count = 5
        self.chair_ring_radius = 1.0
        self.chair_spacing = 0.3
        self.chair_width = 0.58
        self.vampire_chair = 1
        self.werewolf_chair = 0
        self.violet_vampire_size = 0.8
        self.violet_vampire_chair = 2
        self.seated_eye_height = 1.0
        self.arch_pass_height = 0.85
        self.vampire = Vampire(self.sorcerer_height)
        self.werewolf = Werewolf(self.sorcerer_height * self.werewolf_size)
        self.violet_vampire = Vampire(self.sorcerer_height * self.violet_vampire_size, VioletVampireModel())
        self.chairs = self.place_chairs(floor, math.atan2(outward[0], outward[2]))
        self.chair_mesh = build_chairs(self.chairs)
        self.vampire.sit(self.chairs[self.vampire_chair])
        self.werewolf.sit(self.chairs[self.werewolf_chair])
        self.violet_vampire.sit(self.chairs[self.violet_vampire_chair])
        self.sitters = (self.vampire, self.werewolf, self.violet_vampire)

    def place_chairs(self, floor, facing):
        seat_height, seat_depth = self.vampire.natural_seat()
        chairs = []
        for slot in range(self.chair_count):
            angle = facing + (slot - (self.chair_count - 1) / 2.0) * self.chair_spacing
            back = self.to_world((math.sin(angle) * self.chair_ring_radius, floor,
                                  math.cos(angle) * self.chair_ring_radius))
            chairs.append(Chair((back[0], back[2]), back[1], angle, seat_height, self.chair_width, seat_depth))
        return chairs

    def lava_lights(self):
        return self.river_lights()

    def static_meshes(self):
        return self.scene.terrain, self.scene.scenery, self.scene.tower.model.room

    def update(self, seconds):
        super().update(seconds)
        self.sorcerer.update(seconds)
        for sitter in self.sitters:
            sitter.update(seconds)

    def render_effects(self):
        self.begin()
        self.scene.lava.render()
        self.scene.tower.render()
        self.scene.embers.render()
        self.end()
        glEnableClientState(GL_VERTEX_ARRAY)
        glEnableClientState(GL_NORMAL_ARRAY)
        glEnableClientState(GL_COLOR_ARRAY)
        draw_mesh(*self.chair_mesh)
        glDisableClientState(GL_COLOR_ARRAY)
        glDisableClientState(GL_NORMAL_ARRAY)
        glDisableClientState(GL_VERTEX_ARRAY)
        self.sorcerer.render()
        for sitter in self.sitters:
            sitter.render()


class BridgeRegion(Region):

    def __init__(self, offset, scale):
        scene = LavaBridgeScene()
        super().__init__(scene, offset, scale, (scene.terrain_extent, (scene.river_start, scene.river_end)))
        self.troll_spot = self.to_world((scene.troll_spot, scene.deck_top, 0.0))

    def lava_lights(self):
        return self.river_lights()

    def static_meshes(self):
        return self.scene.terrain, self.scene.structures

    def render_effects(self):
        self.begin()
        self.scene.lava.render()
        self.scene.troll.render()
        self.scene.embers.render()
        self.end()


class DividedWorld:

    def __init__(self, seed=29):
        self.generator = numpy.random.default_rng(seed)
        self.seconds = 0.0
        self.dead_land = DeadLandScene()
        self.tower = TowerRegion((126.0, 0.0, 0.0), 2.5)
        self.bridge = BridgeRegion((265.0, 0.0, 0.0), 2.0)
        self.regions = (DeadLandRegion(self.dead_land), self.tower, self.bridge)
        self.extent = ((-215.0, 300.0), (-46.0, 26.0))
        self.filler_step = 1.0
        self.edge_blend = 10.0
        self.world_ends = (-195.0, 285.0)
        self.ground_color = (0.11, 0.10, 0.095)
        self.mountain_color = (0.09, 0.095, 0.11)
        self.mountain_line = -31.0
        self.mountain_retreat = 11.0
        self.mountain_span = (-230.0, 320.0)
        self.lava_light_slots = 6
        self.specular = (0.06, 0.06, 0.08, 1.0)
        self.ground_noise = SineNoise(self.generator, 5, 0.35, 2)
        self.detail_noise = SineNoise(self.generator, 4, 1.6, 2)
        self.ridge_noise = SineNoise(self.generator, 5, 1.0, 1)
        self.sky = self.dead_land.sky
        self.filler = self.build_filler()
        self.mountains = self.build_mountains()
        self.flight = CameraFlight(self.flight_keyframes())

    def barren_height(self, x, z):
        left, right = self.world_ends
        return (0.36 + 0.24 * self.ground_noise(x, z) + 0.06 * self.detail_noise(x, z)
                + 0.12 * numpy.clip(-z - 10.0, 0.0, None) ** 1.3 + 0.08 * numpy.clip(z - 14.0, 0.0, None) ** 1.3
                + 0.08 * numpy.clip(left - x, 0.0, None) ** 1.3 + 0.08 * numpy.clip(x - right, 0.0, None) ** 1.3)

    def ground_height(self, x, z):
        x = numpy.asarray(x, dtype=numpy.float64)
        z = numpy.asarray(z, dtype=numpy.float64)
        height = self.barren_height(x, z)
        for region in self.regions:
            closeness = 1.0 - smoothstep(region.distance_outside(x, z) / self.edge_blend)
            height = height + (region.edge_height(x, z) - height) * closeness
        return height

    def build_filler(self):
        (left, right), (back, front) = self.extent
        xs = numpy.arange(left, right + 1e-6, self.filler_step)
        zs = numpy.arange(back, front + 1e-6, self.filler_step)
        z, x = numpy.meshgrid(zs, xs, indexing="ij")
        grid = numpy.stack((x, self.ground_height(x, z), z), axis=-1)
        normals = unit_or_fallback(surface_normals(grid, grid - (0.0, 1.0, 0.0), False), numpy.array((0.0, 1.0, 0.0)))
        cracks = numpy.abs(self.detail_noise(x * 2.7, z * 2.7)) < 0.05
        colors = (numpy.asarray(self.ground_color) * mottling(grid * 0.6, 0.3)[..., None]
                  * numpy.where(cracks, 0.6, 1.0)[..., None])
        covered = numpy.zeros(x.shape, dtype=bool)
        for region in self.regions:
            covered |= region.contains(x, z)
        rows, columns = x.shape
        row = numpy.arange(rows - 1)[:, None]
        column = numpy.arange(columns - 1)[None, :]
        hidden = covered[:-1, :-1] & covered[1:, :-1] & covered[:-1, 1:] & covered[1:, 1:]
        corner = (row * columns + column)[~hidden]
        quads = numpy.stack((corner, corner + columns, corner + 1, corner + 1, corner + columns, corner + columns + 1),
                            axis=-1)
        return (numpy.ascontiguousarray(grid.reshape(-1, 3).astype(numpy.float32)),
                numpy.ascontiguousarray(normals.reshape(-1, 3).astype(numpy.float32)),
                numpy.ascontiguousarray(colors.reshape(-1, 3).astype(numpy.float32)),
                numpy.ascontiguousarray(quads.reshape(-1).astype(numpy.uint32)))

    def mountain_line_at(self, x):
        left, right, _, _ = self.tower.rect
        middle = (left + right) / 2.0
        reach = (right - left) / 2.0 + 25.0
        return self.mountain_line - self.mountain_retreat * smoothstep((reach - numpy.abs(x - middle)) / 20.0)

    def build_mountains(self):
        mesh = StatueMesh()
        for retreat, peak, base, wiggle, offset in ((0.0, 7.5, 2.5, 0.22, 0.0), (6.0, 3.2, 1.2, 0.35, 1.7)):
            x = numpy.linspace(*self.mountain_span, 2400)
            rise = numpy.linspace(0.0, 1.0, 14)[:, None]
            ridge = 1.0 - numpy.abs(numpy.sin(x * wiggle + offset))
            noise = 0.5 + 0.5 * self.ridge_noise(x * 0.1 + offset)
            heights = base + (peak - base) * noise * (0.45 + 0.55 * ridge ** 2) + 0.4 * self.ridge_noise(
                x * 0.55 + offset)
            depth = self.mountain_line_at(x) + retreat + 2.5 * self.ridge_noise(x * 0.16 + offset + 3.0)
            spread = depth[None, :] + (1.0 - rise) * heights[None, :] * 0.9
            grid = numpy.stack((numpy.broadcast_to(x, spread.shape), -1.5 + rise * (heights[None, :] + 1.5), spread),
                               axis=-1)
            behind = numpy.stack((x, numpy.full_like(x, -3.0), depth - 6.0), axis=-1)[None, :, :]
            normals = unit_or_fallback(surface_normals(grid, behind, False), numpy.array((0.0, 1.0, 0.0)))
            colors = numpy.asarray(self.mountain_color) * mottling(grid * 0.2, 0.25)[..., None]
            mesh.add_grid(grid, normals, colors)
        return mesh.arrays()

    def flight_keyframes(self):
        window = self.tower.window
        outward = self.tower.outward
        tower_base = self.tower.offset
        tower_middle = tuple(tower_base + (0.0, 6.0, 0.0))
        troll = self.bridge.troll_spot
        bridge_middle = tuple(self.bridge.offset + (0.0, 2.4, 0.0))
        dead_land_leg = self.dead_land.flight_keyframes()[:-1]
        last = dead_land_leg[-1][0]
        onward = [(6.0, (26.0, 3.0, 7.0), tower_middle),
                  (16.0, (66.0, 3.6, 8.0), tower_middle),
                  (26.0, (100.0, 4.2, 16.0), tuple(tower_base + (0.0, 8.0, 0.0))),
                  (34.0, (116.0, 6.5, 15.0), tuple(window)),
                  (40.0, tuple(window + outward * 3.0 + (0.0, 0.3, 0.0)), tuple(window - outward * 0.5)),
                  (45.0, tuple(window + outward * 1.0), tuple(window - outward * 0.9 - (0.0, 0.25, 0.0))),
                  (51.0, tuple(window + outward * 1.0), tuple(window - outward * 0.9 - (0.0, 0.25, 0.0))),
                  *self.room_shot(51.0),
                  (81.0, tuple(window + outward * 7.0 + (0.0, 1.5, 0.0)), tower_middle),
                  (91.0, (165.0, 4.0, 13.0), bridge_middle),
                  (103.0, (220.0, 3.5, 10.0), bridge_middle),
                  (113.0, (252.0, 5.6, 9.0), bridge_middle),
                  (120.0, (troll[0] - 3.0, troll[1] + 0.9, 5.5), tuple(troll + (0.0, 0.8, 0.0))),
                  (127.0, (troll[0] + 3.0, troll[1] + 1.6, 5.0), tuple(troll + (0.0, 0.8, 0.0))),
                  (134.0, (troll[0] + 8.0, troll[1] + 3.0, 10.0), bridge_middle),
                  (138.0, (troll[0] + 8.0, troll[1] + 3.0, 10.0), bridge_middle)]
        return dead_land_leg + [(last + time, eye, target) for time, eye, target in onward]

    def room_shot(self, start):
        tower = self.tower
        window = tower.window
        outward = tower.outward
        across = numpy.array((outward[2], 0.0, -outward[0]))
        lift = numpy.array((0.0, 1.0, 0.0))
        floor = tower.chairs[0].floor
        seated = numpy.mean([numpy.asarray(sitter.position) for sitter in tower.sitters], axis=0)
        toward_window = window - seated
        toward_window[1] = 0.0
        toward_window /= numpy.linalg.norm(toward_window)
        middle = seated + lift * tower.seated_eye_height
        in_arch = window - outward * 0.1 + lift * tower.arch_pass_height
        over_sorcerer = window - outward * 1.2 + lift * (tower.arch_pass_height + 0.1)
        descending = window - outward * 2.0 + across * 0.5 + lift * 0.45
        heads = {sitter: numpy.asarray(sitter.position) + lift * (sitter.height * 0.62) for sitter in tower.sitters}
        shots = [(3.0, in_arch, window - outward * 3.0 - lift * 0.3),
                 (5.5, over_sorcerer, heads[tower.violet_vampire]),
                 (8.5, descending, heads[tower.violet_vampire]),
                 (13.0, seated + toward_window * 1.9 + across * 0.8 + (0.0, floor + 1.25 - seated[1], 0.0), middle),
                 (19.0, seated + toward_window * 1.5 - across * 1.0 + (0.0, floor + 1.15 - seated[1], 0.0),
                  heads[tower.werewolf]),
                 (22.5, over_sorcerer, window + outward * 2.0 + lift * 0.6),
                 (25.0, in_arch, window + outward * 4.0 + lift * 0.6),
                 (27.0, window + outward * 0.8 + lift * 0.7, window + outward * 6.0 + lift * 0.8)]
        return [(start + time, tuple(eye), tuple(target)) for time, eye, target in shots]

    def camera_view(self):
        return self.flight.view(self.seconds)

    def restart(self):
        self.seconds = 0.0

    def update(self, seconds):
        self.seconds += seconds
        eye, _ = self.camera_view()
        for region in self.regions:
            if region.awake(eye):
                region.update(seconds)

    def setup_lights(self, eye):
        dead_land = self.dead_land
        for light in range(8):
            glDisable(GL_LIGHT0 + light)
        glLightModelfv(GL_LIGHT_MODEL_AMBIENT, dead_land.ambient)
        glEnable(GL_LIGHT0)
        glLightfv(GL_LIGHT0, GL_POSITION, (*dead_land.moon_direction, 0.0))
        glLightfv(GL_LIGHT0, GL_DIFFUSE, dead_land.moonlight_color)
        glLightfv(GL_LIGHT0, GL_SPECULAR, dead_land.moonlight_specular)
        glLightfv(GL_LIGHT0, GL_AMBIENT, (0.0, 0.0, 0.0, 1.0))
        lights = [light for region in self.regions for light in region.lava_lights()]
        lights.sort(key=lambda light: float(numpy.linalg.norm(light[0] - eye)))
        for number, (position, color, attenuation) in enumerate(lights[:self.lava_light_slots]):
            self.point_light(GL_LIGHT1 + number, position, color, attenuation)
        self.point_light(GL_LIGHT7, self.tower.room_light, self.tower.room_light_color,
                         self.tower.room_light_attenuation)

    @staticmethod
    def point_light(light, position, color, attenuation):
        constant, linear, quadratic = attenuation
        glEnable(light)
        glLightfv(light, GL_POSITION, (*position, 1.0))
        glLightfv(light, GL_DIFFUSE, (*color, 1.0))
        glLightfv(light, GL_SPECULAR, (*color, 1.0))
        glLightfv(light, GL_AMBIENT, (0.0, 0.0, 0.0, 1.0))
        glLightf(light, GL_CONSTANT_ATTENUATION, constant)
        glLightf(light, GL_LINEAR_ATTENUATION, linear)
        glLightf(light, GL_QUADRATIC_ATTENUATION, quadratic)

    def render(self, eye):
        dead_land = self.dead_land
        glPushAttrib(GL_LIGHTING_BIT | GL_ENABLE_BIT | GL_FOG_BIT | GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT
                     | GL_POINT_BIT | GL_CURRENT_BIT)
        glEnable(GL_LIGHTING)
        glEnable(GL_NORMALIZE)
        glDisable(GL_CULL_FACE)
        glEnable(GL_COLOR_MATERIAL)
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
        glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, self.specular)
        glMaterialf(GL_FRONT_AND_BACK, GL_SHININESS, 12.0)
        glMaterialfv(GL_FRONT_AND_BACK, GL_EMISSION, (0.0, 0.0, 0.0, 1.0))
        self.setup_lights(numpy.asarray(eye))
        glEnable(GL_FOG)
        glFogi(GL_FOG_MODE, GL_EXP2)
        glFogf(GL_FOG_DENSITY, dead_land.fog_density)
        glFogfv(GL_FOG_COLOR, dead_land.fog_color)
        self.sky.render()
        glEnableClientState(GL_VERTEX_ARRAY)
        glEnableClientState(GL_NORMAL_ARRAY)
        glEnableClientState(GL_COLOR_ARRAY)
        draw_mesh(*self.filler)
        draw_mesh(*self.mountains)
        for region in self.regions:
            region.begin()
            for mesh in region.static_meshes():
                draw_mesh(*mesh)
            region.end()
        glDisableClientState(GL_COLOR_ARRAY)
        glDisableClientState(GL_NORMAL_ARRAY)
        glDisableClientState(GL_VERTEX_ARRAY)
        for region in self.regions:
            region.render_effects()
        glPopAttrib()
