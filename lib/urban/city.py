from OpenGL.GL import *


class City:
    def __init__(self, x, y, z, grid=(), spacing=0.0):
        self.x = x
        self.y = y
        self.z = z
        self.grid = tuple(tuple(line) for line in grid)
        self.spacing = spacing
        self.towns = tuple(town for line in self.grid for town in line if town is not None)
        self.rows = len(self.grid)
        self.columns = max((len(line) for line in self.grid), default=0)
        self.width = 0.0
        self.depth = 0.0
        self._arrange()

    def _column_widths(self):
        return tuple(max((line[column].width for line in self.grid
                          if column < len(line) and line[column] is not None), default=0.0)
                     for column in range(self.columns))

    def _row_depths(self):
        return tuple(max((town.depth for town in line if town is not None), default=0.0)
                     for line in self.grid)

    def _arrange(self):
        if not self.towns:
            return
        column_widths = self._column_widths()
        row_depths = self._row_depths()
        self.width = sum(column_widths) + self.spacing * (self.columns - 1)
        self.depth = sum(row_depths) + self.spacing * (self.rows - 1)
        cursor_z = -self.depth / 2.0
        for row, line in enumerate(self.grid):
            cursor_x = -self.width / 2.0
            for column in range(self.columns):
                town = line[column] if column < len(line) else None
                if town is not None:
                    town.x = cursor_x + column_widths[column] / 2.0
                    town.z = cursor_z + row_depths[row] / 2.0
                cursor_x += column_widths[column] + self.spacing
            cursor_z += row_depths[row] + self.spacing

    def town_at(self, row, column):
        if 0 <= row < self.rows and 0 <= column < len(self.grid[row]):
            return self.grid[row][column]
        return None

    def town_count(self):
        return len(self.towns)

    def quarter_count(self):
        return sum(len(town.quarters) for town in self.towns)

    def house_count(self):
        return sum(town.house_count() for town in self.towns)

    def tallest(self):
        return max((town.tallest() for town in self.towns), default=0.0)

    def draw(self):
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        for town in self.towns:
            town.draw()
        glPopMatrix()
