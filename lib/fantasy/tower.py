import math

import numpy
from OpenGL.GL import *

from lib.animals.dragon import Sculptor, StatueMesh, catmull_rom, mottling, normalized, surface_normals, \
    unit_or_fallback


def brick_hash(identifiers):
    return numpy.modf(numpy.abs(numpy.sin(identifiers * 12.9898) * 43758.5453))[0]


class DarkTowerModel:

    def __init__(self):
        self.stone = (0.21, 0.21, 0.23)
        self.mortar = (0.07, 0.07, 0.08)
        self.trim = (0.46, 0.44, 0.41)
        self.ledge_stone = (0.16, 0.15, 0.16)
        self.roof = (0.12, 0.11, 0.13)
        self.horn_base = (0.78, 0.71, 0.55)
        self.horn_tip = (0.92, 0.88, 0.76)
        self.spire = (0.07, 0.07, 0.09)
        self.window_frame = (0.05, 0.045, 0.05)
        self.window_glow = (1.0, 0.62, 0.28)
        self.brick_height = 0.12
        self.brick_width = 0.24
        self.rows_per_brick = 4
        self.columns_per_brick = 6
        self.mortar_depth = 0.008
        self.pilaster_count = 6
        self.towers = (
            {"center": (0.0, 0.0, 0.0), "lower_radius": 0.55, "lower_top": 2.4, "upper_radius": 0.48,
             "upper_top": 4.3, "ledges": (2.4, 4.3), "ledge_flare": 0.14, "horns": (8, 6), "horn_length": (0.7, 0.5),
             "dome_height": 0.5, "spire_length": 0.75},
            {"center": (-0.85, 0.0, -0.6), "lower_radius": 0.34, "lower_top": 1.6, "upper_radius": 0.3,
             "upper_top": 2.6, "ledges": (1.6, 2.6), "ledge_flare": 0.1, "horns": (6, 0), "horn_length": (0.45, 0.0),
             "dome_height": 0.32, "spire_length": 0.45},
        )
        self.annexes = (((0.66, 0.0, 0.22), 0.36, 1.45), ((-0.52, 0.0, 0.3), 0.3, 1.35))
        self.foundation_depth = 0.25
        self.windows = ((0, 0.25, 3.55, 0.075, 0.3), (0, 2.25, 3.6, 0.07, 0.28), (0, -1.9, 3.5, 0.07, 0.28),
                        (0, 0.9, 1.75, 0.065, 0.24), (1, 0.6, 2.15, 0.055, 0.2))
        self.zoom_window = 0
        self.mesh = StatueMesh()
        self.sculptor = Sculptor(self.mesh)
        self.build_body()
        self.body = self.mesh.arrays()
        self.mesh = StatueMesh()
        self.build_window_glass()
        self.glass = self.mesh.arrays()
        self.height = float(self.body[0][:, 1].max())

    def brick_drum(self, center, radius, bottom, top):
        courses = max(1, round((top - bottom) / self.brick_height))
        rows = courses * self.rows_per_brick + 1
        bricks_around = max(8, round(2.0 * math.pi * radius / self.brick_width))
        columns = bricks_around * self.columns_per_brick + 1
        row = numpy.arange(rows)[:, None]
        column = numpy.arange(columns)[None, :]
        heights = bottom + (top - bottom) * row / (rows - 1)
        angles = 2.0 * math.pi * column / (columns - 1)
        course = row // self.rows_per_brick
        shift = (course % 2) * (self.columns_per_brick // 2)
        joint = (row % self.rows_per_brick == 0) | ((column + shift) % self.columns_per_brick == 0)
        brick = course * 1000 + (column + shift) // self.columns_per_brick + int(radius * 1000) * 7
        shade = 0.8 + 0.35 * brick_hash(brick.astype(numpy.float64))
        distance = radius - self.mortar_depth * joint
        center = numpy.asarray(center, dtype=numpy.float64)
        grid = numpy.stack((center[0] + numpy.sin(angles) * distance,
                            numpy.broadcast_to(heights, distance.shape),
                            center[2] + numpy.cos(angles) * distance), axis=-1)
        axis = numpy.stack((numpy.full(rows, center[0]), heights[:, 0], numpy.full(rows, center[2])), axis=-1)
        normals = unit_or_fallback(surface_normals(grid, axis[:, None, :], True), numpy.array((0.0, 1.0, 0.0)))
        colors = numpy.where(joint[..., None], numpy.asarray(self.mortar), numpy.asarray(self.stone) * shade[..., None])
        self.mesh.add_grid(grid, normals, colors * mottling(grid, 0.08)[..., None])

    def lathe(self, center, profile, color, segments=96, mottle=0.06):
        profile = numpy.asarray(profile, dtype=numpy.float64)
        angles = numpy.linspace(0.0, 2.0 * math.pi, segments + 1)[None, :]
        radii, heights = profile[:, 0:1], profile[:, 1:2]
        center = numpy.asarray(center, dtype=numpy.float64)
        grid = numpy.stack((center[0] + numpy.sin(angles) * radii, numpy.broadcast_to(heights, (len(profile),
                                                                                                 segments + 1)),
                            center[2] + numpy.cos(angles) * radii), axis=-1)
        axis = numpy.stack((numpy.full(len(profile), center[0]), heights[:, 0], numpy.full(len(profile), center[2])),
                           axis=-1)
        normals = unit_or_fallback(surface_normals(grid, axis[:, None, :], True), numpy.array((0.0, 1.0, 0.0)))
        colors = numpy.asarray(color) * mottling(grid, mottle)[..., None]
        self.mesh.add_grid(grid, normals, colors)

    def ring(self, center, radius, height, thickness, color):
        self.lathe(center, ((radius - 0.005, height - thickness), (radius + thickness * 0.6, height - thickness * 0.6),
                            (radius + thickness * 0.6, height + thickness * 0.6), (radius - 0.005, height + thickness)),
                   color, mottle=0.04)

    def pilasters(self, center, radius, bottom, top):
        center = numpy.asarray(center, dtype=numpy.float64)
        for index in range(self.pilaster_count):
            angle = 2.0 * math.pi * (index + 0.5) / self.pilaster_count
            outward = numpy.array((math.sin(angle), 0.0, math.cos(angle)))
            base = center + outward * (radius + 0.004)
            self.sculptor.tube((base + (0.0, bottom, 0.0), base + (0.0, (bottom + top) / 2.0, 0.0),
                                base + (0.0, top, 0.0)), ((0.0, 0.022, 0.012), (1.0, 0.022, 0.012)), self.trim,
                               rings=int((top - bottom) / 0.05) + 2, segments=8, up_hint=tuple(outward),
                               cap_start=False, cap_end=False, mottle=0.12)

    def ledge(self, center, radius, height, flare):
        self.lathe(center, ((radius - 0.01, height - 0.06), (radius + 0.01, height - 0.05),
                            (radius + flare * 0.6, height + 0.02), (radius + flare, height + 0.1),
                            (radius + flare, height + 0.18), (radius + flare - 0.03, height + 0.2),
                            (radius - 0.05, height + 0.2)), self.ledge_stone)
        self.ring(center, radius + flare + 0.005, height + 0.14, 0.018, self.trim)

    def dome(self, center, radius, base, height, spire_length):
        profile = [(radius * math.cos(angle) ** 0.6, base + height * math.sin(angle))
                   for angle in numpy.linspace(0.0, math.pi / 2.0, 14)]
        self.lathe(center, profile, self.roof)
        center = numpy.asarray(center, dtype=numpy.float64)
        self.sculptor.spike(center + (0.0, base + height * 0.9, 0.0), (0.0, 1.0, 0.0), spire_length,
                            radius * 0.12, self.spire, rings=10, segments=10)
        for index in range(4):
            angle = index * math.pi / 2.0 + math.pi / 4.0
            outward = numpy.array((math.sin(angle), 0.0, math.cos(angle)))
            self.sculptor.spike(center + outward * radius * 0.55 + (0.0, base + height * 0.55, 0.0),
                                outward * 0.12 + (0.0, 1.0, 0.0), spire_length * 0.45, radius * 0.07, self.spire,
                                rings=8, segments=8)

    def horns(self, center, radius, height, count, length):
        center = numpy.asarray(center, dtype=numpy.float64)
        for index in range(count):
            angle = 2.0 * math.pi * index / count + 0.2
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

    def window_place(self, window):
        tower_index, angle, height, half_width, half_height = window
        tower = self.towers[tower_index]
        radius = tower["upper_radius"] if height > tower["ledges"][0] else tower["lower_radius"]
        outward = numpy.array((math.sin(angle), 0.0, math.cos(angle)))
        across = numpy.array((math.cos(angle), 0.0, -math.sin(angle)))
        center = numpy.asarray(tower["center"], dtype=numpy.float64) + outward * radius + (0.0, height, 0.0)
        return center, outward, across, half_width, half_height

    def window_center(self, index=None):
        center, outward, _, _, _ = self.window_place(self.windows[self.zoom_window if index is None else index])
        return center, outward

    def arched_panel(self, center, outward, across, half_width, half_height, lift, color):
        rows, columns = 18, 6
        upward = numpy.linspace(-half_height, half_height + half_width, rows)[:, None]
        sideways = numpy.linspace(-1.0, 1.0, columns)[None, :]
        arch = numpy.sqrt(numpy.clip(half_width ** 2 - (upward - half_height) ** 2, 0.0, None))
        width = numpy.where(upward > half_height, arch, half_width)
        grid = (center + outward * lift + across * (sideways * width)[..., None]
                + numpy.array((0.0, 1.0, 0.0)) * upward[..., None])
        normals = numpy.broadcast_to(outward, grid.shape)
        brightness = 1.0 - 0.45 * (upward + half_height) / (2.0 * half_height + half_width)
        colors = numpy.asarray(color) * numpy.broadcast_to(brightness, grid.shape[:2])[..., None]
        self.mesh.add_grid(grid, normals, colors)

    def build_body(self):
        for tower in self.towers:
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
            self.horns(center, tower["lower_radius"] + tower["ledge_flare"] * 0.8, first + 0.1, lower_horns,
                       lower_length)
            self.horns(center, tower["upper_radius"] + tower["ledge_flare"] * 0.8, second + 0.1, upper_horns,
                       upper_length)
            self.dome(center, tower["upper_radius"] + tower["ledge_flare"] - 0.05, second + 0.2,
                      tower["dome_height"], tower["spire_length"])
        for center, radius, height in self.annexes:
            self.brick_drum(center, radius, -self.foundation_depth, height)
            self.lathe(center, ((radius + 0.02, height - 0.06), (radius + 0.025, height), (radius - 0.03, height),
                                (radius - 0.03, height - 0.04), (0.0, height - 0.04)), self.ledge_stone)
        for window in self.windows:
            center, outward, across, half_width, half_height = self.window_place(window)
            self.arched_panel(center, outward, across, half_width + 0.025, half_height + 0.02, 0.006,
                              self.window_frame)

    def build_window_glass(self):
        for window in self.windows:
            center, outward, across, half_width, half_height = self.window_place(window)
            self.arched_panel(center, outward, across, half_width, half_height, 0.009, self.window_glow)


class DarkTower:

    def __init__(self, model=None):
        self.model = model or DarkTowerModel()
        self.position = (0.0, 0.0, 0.0)
        self.seconds = 0.0
        self.window_glow = 1.0
        self.flickers_per_second = (2.3, 5.1)
        self.specular = (0.15, 0.15, 0.18, 1.0)
        self.shininess = 16.0

    def update(self, seconds):
        self.seconds += seconds

    def window_strength(self):
        slow, fast = self.flickers_per_second
        return self.window_glow * (0.85 + 0.1 * math.sin(self.seconds * slow * 2.0 * math.pi)
                                   + 0.05 * math.sin(self.seconds * fast * 2.0 * math.pi))

    @staticmethod
    def draw(positions, normals, colors, indices):
        glVertexPointer(3, GL_FLOAT, 0, positions)
        glNormalPointer(GL_FLOAT, 0, normals)
        glColorPointer(3, GL_FLOAT, 0, colors)
        glDrawElements(GL_TRIANGLES, len(indices), GL_UNSIGNED_INT, indices)

    def render(self):
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
        self.draw(*self.model.body)
        glDisable(GL_LIGHTING)
        positions, _, colors, indices = self.model.glass
        strength = self.window_strength()
        glVertexPointer(3, GL_FLOAT, 0, positions)
        glColorPointer(3, GL_FLOAT, 0, numpy.ascontiguousarray(numpy.clip(colors * strength, 0.0, 1.0)))
        glDrawElements(GL_TRIANGLES, len(indices), GL_UNSIGNED_INT, indices)
        glDisableClientState(GL_COLOR_ARRAY)
        glDisableClientState(GL_NORMAL_ARRAY)
        glDisableClientState(GL_VERTEX_ARRAY)
        glPopAttrib()
        glPopMatrix()
