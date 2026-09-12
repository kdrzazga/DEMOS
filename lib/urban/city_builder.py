import random

from lib.urban.city import City
from lib.urban.quarter import Quarter, WALL_PALETTE
from lib.urban.road import Road


class CityBuilder:
    def __init__(self, blocks_across=3, blocks_deep=2, quarter_rows=2, quarter_columns=3,
                 road_width=7.0, floor_range=(1, 4), windows_range=(2, 4),
                 palette=WALL_PALETTE, house_spacing=(1.6, 2.6), density=1.0,
                 road_marking=True, seed=0):
        self.blocks_across = max(1, blocks_across)
        self.blocks_deep = max(1, blocks_deep)
        self.quarter_rows = quarter_rows
        self.quarter_columns = quarter_columns
        self.road_width = road_width
        self.floor_range = floor_range
        self.windows_range = windows_range
        self.palette = palette
        self.house_spacing = house_spacing
        self.density = max(0.0, min(1.0, density))
        self.road_marking = road_marking
        self.seed = seed

    def _create_blocks(self):
        generator = random.Random(self.seed)
        blocks = []
        for _ in range(self.blocks_deep):
            line = []
            for _ in range(self.blocks_across):
                line.append(Quarter(0.0, 0.0, 0.0, rows=self.quarter_rows,
                                    columns=self.quarter_columns, floor_range=self.floor_range,
                                    windows_range=self.windows_range, palette=self.palette,
                                    spacing=self.house_spacing, density=self.density,
                                    seed=generator.randrange(1000000)))
            blocks.append(line)
        return blocks

    def _place_blocks(self, blocks):
        column_widths = tuple(max(blocks[row][column].width for row in range(self.blocks_deep))
                              for column in range(self.blocks_across))
        row_depths = tuple(max(quarter.depth for quarter in line) for line in blocks)
        width = sum(column_widths) + self.road_width * (self.blocks_across - 1)
        depth = sum(row_depths) + self.road_width * (self.blocks_deep - 1)
        cursor_z = -depth / 2.0
        for row in range(self.blocks_deep):
            cursor_x = -width / 2.0
            for column in range(self.blocks_across):
                quarter = blocks[row][column]
                quarter.x = cursor_x + column_widths[column] / 2.0
                quarter.z = cursor_z + row_depths[row] / 2.0
                cursor_x += column_widths[column] + self.road_width
            cursor_z += row_depths[row] + self.road_width
        return column_widths, row_depths, width, depth

    def _create_roads(self, column_widths, row_depths, width, depth):
        roads = []
        cursor_x = -width / 2.0
        for column in range(self.blocks_across - 1):
            cursor_x += column_widths[column]
            roads.append(Road(cursor_x + self.road_width / 2.0, 0.0, 0.0, depth, self.road_width,
                              facing=0.0, marking=self.road_marking))
            cursor_x += self.road_width
        cursor_z = -depth / 2.0
        for row in range(self.blocks_deep - 1):
            cursor_z += row_depths[row]
            roads.append(Road(0.0, 0.0, cursor_z + self.road_width / 2.0, width, self.road_width,
                              facing=90.0, marking=self.road_marking))
            cursor_z += self.road_width
        return roads

    def build(self, x=0.0, y=0.0, z=0.0):
        blocks = self._create_blocks()
        column_widths, row_depths, width, depth = self._place_blocks(blocks)
        roads = self._create_roads(column_widths, row_depths, width, depth)
        quarters = tuple(quarter for line in blocks for quarter in line)
        return City(x, y, z, quarters, roads)
