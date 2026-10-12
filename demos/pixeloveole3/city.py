import random

from demos.pixeloveole3.residential import Footprint
from demos.pixeloveole3.roofs import HipRoof
from demos.pixeloveole3.vegetation import Grove


class Block:
    def __init__(self, footprint, height, wall_color, roof=None, floor_height=3.0, window_spacing=2.6):
        self.footprint = footprint
        self.height = height
        self.wall_color = wall_color
        self.roof = roof
        self.floor_height = floor_height
        self.window_spacing = window_spacing
        self.window_color = tuple(component * 0.42 for component in wall_color)
        self.cap_color = tuple(component * 0.82 for component in wall_color)

    def draw(self, shapes):
        footprint = self.footprint
        shapes.box(footprint.x0, 0.0, footprint.z0, footprint.x1, self.height, footprint.z1, self.wall_color)
        for _, x, z, yaw, length in footprint.faces():
            with shapes.frame(x, 0.0, z, yaw):
                self._draw_windows(shapes, length)
        if self.roof:
            self.roof.draw(shapes)
        else:
            shapes.box(footprint.x0 - 0.2, self.height, footprint.z0 - 0.2, footprint.x1 + 0.2, self.height + 0.5,
                       footprint.z1 + 0.2, self.cap_color)

    def _draw_windows(self, shapes, length):
        columns = int(length / self.window_spacing)
        if columns < 1:
            return
        floor = 0
        while True:
            bottom = 1.3 + floor * self.floor_height
            if bottom + 1.4 > self.height - 0.6:
                break
            for column in range(columns):
                center = (column + 0.5) * length / columns
                shapes.box(center - 0.6, bottom, 0.0, center + 0.6, bottom + 1.4, 0.05, self.window_color)
            floor += 1


class ChurchTower:
    def __init__(self, x, z, width, height, body_color, spire_color):
        self.x = x
        self.z = z
        self.width = width
        self.height = height
        self.body_color = body_color
        self.spire_color = spire_color
        self.trim_color = tuple(component * 0.85 for component in body_color)
        self.opening_color = (0.18, 0.18, 0.20)

    def draw(self, shapes):
        x, z, half, height = self.x, self.z, self.width / 2.0, self.height
        shapes.box(x - half, 0.0, z - half, x + half, height, z + half, self.body_color)
        shapes.box(x - half - 0.3, height, z - half - 0.3, x + half + 0.3, height + 0.6, z + half + 0.3,
                   self.trim_color)
        for level in (height * 0.55, height * 0.8):
            shapes.box(x - 0.5, level, z + half, x + 0.5, level + 2.4, z + half + 0.05, self.opening_color)
            shapes.box(x - half - 0.05, level, z - 0.5, x - half, level + 2.4, z + 0.5, self.opening_color)
            shapes.box(x + half, level, z - 0.5, x + half + 0.05, level + 2.4, z + 0.5, self.opening_color)
        belfry = height + 0.6
        shapes.cylinder(x, belfry, z, half * 0.85, half * 0.85, 5.0, self.body_color, 8)
        shapes.cylinder(x, belfry + 5.0, z, half * 0.95, half * 0.3, 3.0, self.spire_color, 8)
        shapes.cylinder(x, belfry + 8.0, z, 0.6, 0.6, 2.0, self.body_color, 8)
        shapes.cylinder(x, belfry + 10.0, z, 0.9, 0.0, 9.0, self.spire_color, 8)
        shapes.sphere(x, belfry + 19.2, z, 0.35, (0.80, 0.68, 0.30), slices=8, stacks=6)


class DistantCity:
    def __init__(self, roof_texture, seed=11):
        self.roof_texture = roof_texture
        self.generator = random.Random(seed)
        self.walls = ((0.93, 0.92, 0.88), (0.90, 0.84, 0.70), (0.90, 0.72, 0.66), (0.84, 0.76, 0.62),
                      (0.80, 0.80, 0.78), (0.94, 0.88, 0.80))
        self.roofs = ((0.82, 0.42, 0.29), (0.74, 0.37, 0.27), (0.86, 0.50, 0.36), (0.50, 0.50, 0.52))
        self.blocks = []
        self.towers = []
        self.tree_positions = []
        self.tower_specs = ((45.0, -215.0, 7.0, 34.0), (128.0, -262.0, 8.0, 40.0), (215.0, -235.0, 6.5, 30.0),
                            (-95.0, -250.0, 7.0, 32.0))
        self._populate_grid()
        self._populate_street_row()
        self._add_landmarks()
        self.grove = Grove(self.tree_positions, seed=seed + 1)

    def _is_reserved(self, x0, z0, x1, z1):
        for x, z in ((x0, z0), (x1, z0), (x0, z1), (x1, z1), ((x0 + x1) / 2.0, (z0 + z1) / 2.0)):
            if -4.0 <= x <= 100.0 and -70.0 <= z <= 34.0:
                return True
            if -46.0 <= x <= 0.0 and z <= 40.0:
                return True
            if z >= 8.0 and x >= -46.0 and z <= 40.0:
                return True
            if z > 36.0 and -160.0 <= x <= 160.0:
                return True
            for tower_x, tower_z, _, _ in self.tower_specs:
                if abs(x - tower_x) < 16.0 and tower_z - 45.0 < z < tower_z + 14.0:
                    return True
        return False

    def _hip_roof(self, footprint, height, color):
        rise = min(footprint.x1 - footprint.x0, footprint.z1 - footprint.z0) * 0.42
        return HipRoof(footprint.x0 - 0.4, footprint.z0 - 0.4, footprint.x1 + 0.4, footprint.z1 + 0.4, height, rise,
                       color, self.roof_texture)

    def _house(self, footprint, height):
        generator = self.generator
        wall = generator.choice(self.walls)
        if height > 14.0 and generator.random() < 0.6:
            return Block(footprint, height, wall)
        return Block(footprint, height, wall, self._hip_roof(footprint, height, generator.choice(self.roofs)))

    def _populate_grid(self, spacing=26.0):
        generator = self.generator
        x = -330.0
        while x <= 330.0:
            z = -350.0
            while z <= 150.0:
                center_x = x + generator.uniform(-5.0, 5.0)
                center_z = z + generator.uniform(-5.0, 5.0)
                if generator.random() < 0.18:
                    if not self._is_reserved(center_x - 4.0, center_z - 4.0, center_x + 4.0, center_z + 4.0):
                        self.tree_positions.extend((center_x + generator.uniform(-6.0, 6.0),
                                                    center_z + generator.uniform(-6.0, 6.0)) for _ in range(4))
                else:
                    self._add_grid_block(center_x, center_z)
                z += spacing
            x += spacing

    def _add_grid_block(self, center_x, center_z):
        generator = self.generator
        if generator.random() < 0.2:
            half_width, half_depth, height = generator.uniform(11.0, 18.0), generator.uniform(5.0, 6.5), \
                generator.uniform(13.0, 18.0)
        else:
            half_width, half_depth, height = generator.uniform(4.5, 9.0), generator.uniform(4.0, 7.0), \
                generator.uniform(7.0, 15.0)
        if generator.random() < 0.5:
            half_width, half_depth = half_depth, half_width
        footprint = Footprint(center_x - half_width, center_z - half_depth, center_x + half_width,
                              center_z + half_depth)
        if not self._is_reserved(footprint.x0, footprint.z0, footprint.x1, footprint.z1):
            self.blocks.append(self._house(footprint, height))

    def _populate_street_row(self):
        generator = self.generator
        z = -280.0
        while z < 6.0:
            length = generator.uniform(10.0, 17.0)
            footprint = Footprint(-40.0, z, -26.0, min(z + length, 6.0))
            self.blocks.append(self._house(footprint, generator.uniform(10.0, 16.0)))
            z += length + generator.uniform(0.0, 1.5)
        self.blocks.append(self._house(Footprint(-46.0, 10.0, -28.0, 24.0), 13.0))
        self.tree_positions.extend((-21.0, z) for z in range(-250, -30, 14))

    def _add_landmarks(self):
        self.blocks.append(Block(Footprint(0.0, -80.0, 12.0, -56.0), 13.0, (0.90, 0.74, 0.68),
                                 self._hip_roof(Footprint(0.0, -80.0, 12.0, -56.0), 13.0, self.roofs[0])))
        self.blocks.append(Block(Footprint(72.0, -64.0, 86.0, -28.0), 17.0, (0.93, 0.92, 0.88)))
        self.blocks.append(Block(Footprint(40.0, -150.0, 70.0, -138.0), 15.0, (0.94, 0.94, 0.92)))
        for x, z, width, height in self.tower_specs:
            self.towers.append(ChurchTower(x, z, width, height, (0.90, 0.86, 0.76), (0.42, 0.56, 0.50)))
            nave = Footprint(x - 7.0, z - 34.0, x + 7.0, z - width / 2.0)
            self.blocks.append(Block(nave, 14.0, (0.88, 0.82, 0.70), self._hip_roof(nave, 14.0, self.roofs[1])))

    def draw(self, shapes):
        for block in self.blocks:
            block.draw(shapes)
        for tower in self.towers:
            tower.draw(shapes)
        self.grove.draw(shapes)
