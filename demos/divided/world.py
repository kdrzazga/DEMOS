import math

import numpy
from OpenGL.GL import *

from demos.divided.dead_land import DeadLandScene
from lib.animals.dragon import StatueMesh, mottling, surface_normals, unit_or_fallback
from lib.fantasy.anatomy import smoothstep
from lib.fantasy.scenes.bridge import LavaBridgeScene, SineNoise
from lib.fantasy.scenes.tower import CameraFlight, TowerScene
from lib.fantasy.sorcerer import Sorcerer
from lib.fantasy.tower import DarkTower, DarkTowerModel


def draw_mesh(positions, normals, colors, indices):
    glVertexPointer(3, GL_FLOAT, 0, positions)
    glNormalPointer(GL_FLOAT, 0, normals)
    glColorPointer(3, GL_FLOAT, 0, colors)
    glDrawElements(GL_TRIANGLES, len(indices), GL_UNSIGNED_INT, indices)


class TowerWithRoom(DarkTowerModel):

    def __init__(self):
        self.room_window = (0, 0.25, 3.6, 0.16, 0.3)
        self.room_wall_inset = 0.04
        self.room_ceiling_gap = 0.05
        self.room_stone = (0.13, 0.11, 0.10)
        self.room_floor_color = (0.15, 0.12, 0.09)
        self.opening_depth = 0.12
        super().__init__()
        self.body = self.without_opening(self.body)
        self.glass = self.without_opening(self.glass)
        self.room = self.build_room()

    def build_body(self):
        self.windows = (self.room_window,) + self.windows[1:]
        super().build_body()

    def opening(self):
        return self.window_place(self.windows[0])

    def room_heights(self):
        center, _, _, _, half_height = self.opening()
        tower = self.towers[self.room_window[0]]
        return center[1] - half_height - 0.02, tower["ledges"][1] - self.room_ceiling_gap

    def room_radius(self):
        return self.towers[self.room_window[0]]["upper_radius"] - self.room_wall_inset

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
        gap = half_width / radius + 0.06
        angle = numpy.linspace(window_angle + gap, window_angle + 2.0 * math.pi - gap, 64)[None, :]
        height = numpy.linspace(floor, ceiling, 12)[:, None]
        wall = numpy.stack((numpy.sin(angle) * radius * numpy.ones_like(height), height * numpy.ones_like(angle),
                            numpy.cos(angle) * radius * numpy.ones_like(height)), axis=-1)
        inward = -numpy.stack((numpy.sin(angle), numpy.zeros_like(angle), numpy.cos(angle)), axis=-1)
        mesh.add_grid(wall, numpy.broadcast_to(inward, wall.shape),
                      numpy.asarray(self.room_stone) * mottling(wall * 4.0, 0.25)[..., None])
        reach = numpy.linspace(0.0, radius, 8)[:, None]
        around = numpy.linspace(0.0, 2.0 * math.pi, 49)[None, :]
        for level, facing, color in ((floor, 1.0, self.room_floor_color), (ceiling, -1.0, self.room_stone)):
            disc = numpy.stack((numpy.sin(around) * reach, numpy.full((len(reach), around.shape[1]), level),
                                numpy.cos(around) * reach), axis=-1)
            mesh.add_grid(disc, numpy.broadcast_to((0.0, facing, 0.0), disc.shape),
                          numpy.asarray(color) * mottling(disc * 4.0, 0.25)[..., None])
        return mesh.arrays()


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
        scene = TowerScene()
        scene.tower = DarkTower(TowerWithRoom())
        super().__init__(scene, offset, scale, scene.terrain_extent)
        self.room_light_color = numpy.array((1.0, 0.55, 0.22))
        self.room_light_attenuation = (0.4, 0.0, 0.5)
        self.sorcerer_height = 1.5
        self.sorcerer_back_from_window = 0.24
        model = scene.tower.model
        floor, ceiling = model.room_heights()
        window, outward = model.window_center()
        self.window = self.to_world(window)
        self.outward = outward
        self.room_light = self.to_world((0.0, (floor + ceiling) / 2.0, 0.0))
        self.sorcerer = Sorcerer(self.sorcerer_height)
        self.sorcerer.acting = False
        self.sorcerer.talking = True
        standing = window - outward * self.sorcerer_back_from_window
        self.sorcerer.position = tuple(self.to_world((standing[0], floor, standing[2])))
        self.sorcerer.yaw = math.atan2(outward[0], outward[2])

    def lava_lights(self):
        return self.river_lights()

    def static_meshes(self):
        return self.scene.terrain, self.scene.scenery, self.scene.tower.model.room

    def update(self, seconds):
        super().update(seconds)
        self.sorcerer.update(seconds)

    def render_effects(self):
        self.begin()
        self.scene.lava.render()
        self.scene.tower.render()
        self.scene.embers.render()
        self.end()
        self.sorcerer.render()


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
                  (57.0, tuple(window + outward * 7.0 + (0.0, 1.5, 0.0)), tower_middle),
                  (67.0, (165.0, 4.0, 13.0), bridge_middle),
                  (79.0, (220.0, 3.5, 10.0), bridge_middle),
                  (89.0, (252.0, 5.6, 9.0), bridge_middle),
                  (96.0, (troll[0] - 3.0, troll[1] + 0.9, 5.5), tuple(troll + (0.0, 0.8, 0.0))),
                  (103.0, (troll[0] + 3.0, troll[1] + 1.6, 5.0), tuple(troll + (0.0, 0.8, 0.0))),
                  (110.0, (troll[0] + 8.0, troll[1] + 3.0, 10.0), bridge_middle),
                  (114.0, (troll[0] + 8.0, troll[1] + 3.0, 10.0), bridge_middle)]
        return dead_land_leg + [(last + time, eye, target) for time, eye, target in onward]

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
