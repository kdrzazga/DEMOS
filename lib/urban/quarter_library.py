import random

from lib.urban.quarter import Quarter, WALL_PALETTE
from lib.urban.quarter_copy import QuarterCopy


class QuarterLibrary:
    def __init__(self, size=43, rows=2, columns=3, floor_range=(1, 4), windows_range=(2, 4),
                 palette=WALL_PALETTE, spacing=(1.6, 2.6),
                 densities=(1.0, 0.7, 0.5, 0.4, 0.3, 0.2, 0.1), seed=0):
        self.size = max(1, size)
        self.rows = rows
        self.columns = columns
        self.floor_range = floor_range
        self.windows_range = windows_range
        self.palette = palette
        self.spacing = spacing
        self.densities = densities
        self.seed = seed
        self.prototypes = self._create_prototypes()

    def _create_prototypes(self):
        generator = random.Random(self.seed)
        prototypes = []
        for index in range(self.size):
            prototypes.append(Quarter(0.0, 0.0, 0.0, rows=self.rows, columns=self.columns,
                                      floor_range=self.floor_range,
                                      windows_range=self.windows_range, palette=self.palette,
                                      spacing=self.spacing,
                                      density=self.densities[index % len(self.densities)],
                                      seed=generator.randrange(1000000)))
        return tuple(prototypes)

    def nearest_density(self, density):
        return min(self.densities, key=lambda value: abs(value - density))

    def matching(self, density):
        wanted = self.nearest_density(density)
        return tuple(prototype for prototype in self.prototypes if prototype.density == wanted)

    def copy(self, density, generator):
        return QuarterCopy(generator.choice(self.matching(density)))

    def house_count(self):
        return sum(len(prototype.houses) for prototype in self.prototypes)

    def plot_count(self):
        return sum(prototype.plot_count() for prototype in self.prototypes)
