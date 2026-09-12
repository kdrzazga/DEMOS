import random
from OpenGL.GL import *

from lib.urban.house import House

WALL_PALETTE = ((0.46, 0.44, 0.42), (0.52, 0.40, 0.34), (0.38, 0.42, 0.48),
                (0.50, 0.47, 0.36), (0.44, 0.34, 0.36))


class Quarter:
    def __init__(self, x, y, z, rows=2, columns=3, floor_range=(1, 4), windows_range=(2, 4),
                 palette=WALL_PALETTE, spacing=(1.6, 2.6), density=1.0, facing=0.0, seed=0):
        self.x = x
        self.y = y
        self.z = z
        self.rows = max(1, rows)
        self.columns = max(1, columns)
        self.floor_range = floor_range
        self.windows_range = windows_range
        self.palette = palette
        self.spacing = spacing
        self.density = max(0.0, min(1.0, density))
        self.facing = facing
        self.seed = seed

        self.random_generator = random.Random(seed)
        self.grid = self._create_grid()
        self.width = 0.0
        self.depth = 0.0
        self._arrange()
        self.houses = self._occupied_plots()

    def _create_grid(self):
        generator = self.random_generator
        grid = []
        for row in range(self.rows):
            line = []
            for _ in range(self.columns):
                floor_count = generator.randint(*self.floor_range)
                windows_per_floor = generator.randint(*self.windows_range)
                color = self.palette[generator.randrange(len(self.palette))]
                street_side = 180.0 if row < self.rows / 2.0 else 0.0
                line.append(House(0.0, 0.0, 0.0, floor_count, windows_per_floor=windows_per_floor,
                                  color=color, facing=street_side))
            grid.append(line)
        return grid

    def _column_widths(self):
        return tuple(max(self.grid[row][column].width for row in range(self.rows))
                     for column in range(self.columns))

    def _row_depths(self):
        return tuple(max(house.depth for house in line) for line in self.grid)

    def _arrange(self):
        gap_across, gap_along = self.spacing
        column_widths = self._column_widths()
        row_depths = self._row_depths()
        self.width = sum(column_widths) + gap_across * (self.columns - 1)
        self.depth = sum(row_depths) + gap_along * (self.rows - 1)
        cursor_z = -self.depth / 2.0
        for row in range(self.rows):
            cursor_x = -self.width / 2.0
            for column in range(self.columns):
                house = self.grid[row][column]
                house.x = cursor_x + column_widths[column] / 2.0
                house.z = cursor_z + row_depths[row] / 2.0
                cursor_x += column_widths[column] + gap_across
            cursor_z += row_depths[row] + gap_along

    def _occupied_plots(self):
        plots = tuple(house for line in self.grid for house in line)
        kept = max(0, min(len(plots), round(self.density * len(plots))))
        chosen = set(self.random_generator.sample(range(len(plots)), kept))
        for index, house in enumerate(plots):
            if index not in chosen:
                house.release()
        return tuple(house for index, house in enumerate(plots) if index in chosen)

    def plot_count(self):
        return self.rows * self.columns

    def tallest(self):
        return max((house.total_height for house in self.houses), default=0.0)

    def draw(self):
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        glRotatef(self.facing, 0.0, 1.0, 0.0)
        for house in self.houses:
            house.draw()
        glPopMatrix()
