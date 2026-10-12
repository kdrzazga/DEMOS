import random


class Tree:
    def __init__(self, x, z, generator, scale=1.0, ground=0.0):
        self.x = x
        self.z = z
        self.ground = ground
        self.trunk_color = (0.36, 0.28, 0.20)
        self.trunk_height = generator.uniform(2.6, 4.0) * scale
        self.trunk_radius = 0.22 * scale
        crown_base = self.ground + self.trunk_height
        self.puffs = []
        for _ in range(generator.randint(3, 6)):
            radius = generator.uniform(1.8, 3.2) * scale
            shade = generator.uniform(0.75, 1.15)
            color = (0.20 * shade, 0.42 * shade, 0.16 * shade)
            self.puffs.append((x + generator.uniform(-1.6, 1.6) * scale,
                               crown_base + generator.uniform(1.2, 3.6) * scale,
                               z + generator.uniform(-1.6, 1.6) * scale,
                               radius, color))

    def draw(self, shapes):
        shapes.cylinder(self.x, self.ground, self.z, self.trunk_radius, self.trunk_radius * 0.7,
                        self.trunk_height + 1.5, self.trunk_color, 8)
        for x, y, z, radius, color in self.puffs:
            shapes.sphere(x, y, z, radius, color, (1.0, 0.85, 1.0), 9, 7)


class Grove:
    def __init__(self, positions, seed=0, scale_range=(0.8, 1.3), ground=0.0):
        generator = random.Random(seed)
        self.trees = tuple(Tree(x, z, generator, generator.uniform(*scale_range), ground) for x, z in positions)

    def draw(self, shapes):
        for tree in self.trees:
            tree.draw(shapes)
