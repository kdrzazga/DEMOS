import math
import random

from lib.urban.city import City
from lib.urban.quarter import Quarter, WALL_PALETTE
from lib.urban.quarter_library import QuarterLibrary
from lib.urban.road import RoadLibrary
from lib.urban.town_builder import TownBuilder


class CityFactory:
    def __init__(self, quarter_rows=2, quarter_columns=3, road_width=6.0, town_spacing=0.0,
                 floor_range=(1, 4), windows_range=(2, 4), palette=WALL_PALETTE,
                 house_spacing=(1.6, 2.6), matrix_size=7, quarter_variants=43,
                 library=None, seed=0):
        self.quarter_rows = quarter_rows
        self.quarter_columns = quarter_columns
        self.road_width = road_width
        self.town_spacing = town_spacing
        self.floor_range = floor_range
        self.windows_range = windows_range
        self.palette = palette
        self.house_spacing = house_spacing
        self.matrix_size = matrix_size
        self.quarter_variants = quarter_variants
        self.library = library
        self.seed = seed

        self.ring_densities = (1.0, 0.7, 0.5)
        self.outer_density_range = (0.1, 0.4)
        self.center_quarters = (2, 1)
        self.ring_quarters = (2, 1)
        self.outer_quarters = (2, 2)
        self.triple_factor = 3
        self.big_matrix_size = 11
        self.road_library = RoadLibrary()
        self.quarter_size = None

    def _measure_quarter(self):
        if self.quarter_size is None:
            probe = Quarter(0.0, 0.0, 0.0, rows=self.quarter_rows, columns=self.quarter_columns,
                            floor_range=self.floor_range, windows_range=self.windows_range,
                            palette=self.palette, spacing=self.house_spacing, density=0.0, seed=0)
            self.quarter_size = (probe.width, probe.depth)
        return self.quarter_size

    def _town_size(self, blocks_across, blocks_deep):
        quarter_width, quarter_depth = self._measure_quarter()
        return (quarter_width * blocks_across + self.road_width * (blocks_across - 1),
                quarter_depth * blocks_deep + self.road_width * (blocks_deep - 1))

    def _enlarged(self, quarter_layout, factor):
        blocks_across, blocks_deep = quarter_layout
        if factor <= 1:
            return quarter_layout
        total = blocks_across * blocks_deep * factor
        squarest = None
        for across in range(1, total + 1):
            if total % across:
                continue
            width, depth = self._town_size(across, total // across)
            skew = abs(math.log(width / depth))
            if squarest is None or skew < squarest[0]:
                squarest = (skew, (across, total // across))
        return squarest[1]

    def _ring_density(self, distance, generator):
        if distance < len(self.ring_densities):
            return self.ring_densities[distance]
        return generator.uniform(*self.outer_density_range)

    def _ring_quarters(self, distance):
        if distance == 0:
            return self.center_quarters
        if distance < len(self.ring_densities):
            return self.ring_quarters
        return self.outer_quarters

    def _create_town(self, quarter_layout, density, generator, library):
        blocks_across, blocks_deep = quarter_layout
        builder = TownBuilder(blocks_across=blocks_across, blocks_deep=blocks_deep,
                              quarter_rows=self.quarter_rows, quarter_columns=self.quarter_columns,
                              road_width=self.road_width, floor_range=self.floor_range,
                              windows_range=self.windows_range, palette=self.palette,
                              house_spacing=self.house_spacing, density=density, library=library,
                              road_library=self.road_library, seed=generator.randrange(1000000))
        return builder.build()

    def _build_rings(self, x, y, z, factor, matrix_size, library):
        generator = random.Random(self.seed)
        center = matrix_size // 2
        grid = []
        for row in range(matrix_size):
            line = []
            for column in range(matrix_size):
                distance = max(abs(row - center), abs(column - center))
                density = self._ring_density(distance, generator)
                layout = self._enlarged(self._ring_quarters(distance), factor)
                line.append(self._create_town(layout, density, generator, library))
            grid.append(line)
        return City(x, y, z, grid, spacing=self.town_spacing)

    def build_library(self):
        if self.library is None:
            self.library = QuarterLibrary(size=self.quarter_variants, rows=self.quarter_rows,
                                          columns=self.quarter_columns,
                                          floor_range=self.floor_range,
                                          windows_range=self.windows_range, palette=self.palette,
                                          spacing=self.house_spacing, seed=self.seed)
        return self.library

    def create_with_dense_center(self, x=0.0, y=0.0, z=0.0):
        return self._build_rings(x, y, z, 1, self.matrix_size, self.library)

    def create_with_dense_center_triple(self, x=0.0, y=0.0, z=0.0):
        return self._build_rings(x, y, z, self.triple_factor, self.matrix_size, self.library)

    def create_big_city(self, x=0.0, y=0.0, z=0.0, matrix_size=None):
        span = self.big_matrix_size if matrix_size is None else matrix_size
        return self._build_rings(x, y, z, 1, span, self.build_library())
