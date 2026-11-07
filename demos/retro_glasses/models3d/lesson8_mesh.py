from OpenGL.GL import *


class MeshSurface:
    def __init__(self, size, divisions):
        self.size = size
        self.divisions = divisions
        self.base_height = -0.3
        self.line_color = (0.55, 0.75, 1.0)
        self.fill_color = (0.2, 0.45, 1.0)
        self.fill_alpha = 0.15

    def height(self, x, z):
        return self.base_height

    def line_color_at(self, position):
        return self.line_color

    def fill_color_at(self, position):
        return (*self.fill_color, self.fill_alpha)

    def grid_positions(self):
        step = self.size / self.divisions
        start = -self.size / 2.0
        positions = []
        for row in range(self.divisions + 1):
            z = start + row * step
            row_positions = []
            for column in range(self.divisions + 1):
                x = start + column * step
                row_positions.append((x, self.height(x, z), z))
            positions.append(row_positions)
        return positions

    def draw_line_strip(self, line_positions):
        glBegin(GL_LINE_STRIP)
        for position in line_positions:
            glColor3f(*self.line_color_at(position))
            glVertex3f(*position)
        glEnd()

    def draw_rows(self, positions, row_indices):
        for row in row_indices:
            self.draw_line_strip(positions[row])

    def draw_columns(self, positions, column_indices):
        for column in column_indices:
            column_positions = [line[column] for line in positions]
            self.draw_line_strip(column_positions)

    def draw_fill(self, positions):
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glDepthMask(GL_FALSE)
        for row in range(self.divisions):
            glBegin(GL_TRIANGLE_STRIP)
            for column in range(self.divisions + 1):
                for strip_row in (row + 1, row):
                    position = positions[strip_row][column]
                    glColor4f(*self.fill_color_at(position))
                    glVertex3f(*position)
            glEnd()
        glDepthMask(GL_TRUE)
        glDisable(GL_BLEND)

    def draw(self):
        positions = self.grid_positions()
        every_line = range(self.divisions + 1)
        glLineWidth(1.0)
        self.draw_rows(positions, every_line)
        self.draw_columns(positions, every_line)
        self.draw_fill(positions)


class MeshScene:
    def __init__(self):
        self.mesh = MeshSurface(4.0, 20)

    def draw(self):
        self.mesh.draw()

