import math

from OpenGL.GL import *


class Ball:
    def __init__(self, radius, color):
        self.radius = radius
        self.color = color
        self.slices = 32
        self.stacks = 16
        self.light_position = (3.0, 4.0, 5.0, 0.0)
        self.ambient_light = (0.25, 0.25, 0.3, 1.0)
        self.display_list = None

    def direction(self, slice_index, stack_index):
        longitude = 2.0 * math.pi * slice_index / self.slices
        latitude = math.pi * (stack_index / self.stacks - 0.5)
        return (-math.cos(latitude) * math.sin(longitude),
                math.sin(latitude),
                -math.cos(latitude) * math.cos(longitude))

    def emit_vertex(self, slice_index, stack_index):
        normal = self.direction(slice_index, stack_index)
        glNormal3f(*normal)
        glVertex3f(*(axis * self.radius for axis in normal))

    def draw_strip(self, stack_index):
        glBegin(GL_TRIANGLE_STRIP)
        for slice_index in range(self.slices + 1):
            self.emit_vertex(slice_index, stack_index + 1)
            self.emit_vertex(slice_index, stack_index)
        glEnd()

    def compile(self):
        self.display_list = glGenLists(1)
        glNewList(self.display_list, GL_COMPILE)
        glColor3f(*self.color)
        for stack_index in range(self.stacks):
            self.draw_strip(stack_index)
        glEndList()

    def enable_lighting(self):
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glEnable(GL_COLOR_MATERIAL)
        glLightfv(GL_LIGHT0, GL_POSITION, self.light_position)
        glLightfv(GL_LIGHT0, GL_AMBIENT, self.ambient_light)

    def disable_lighting(self):
        glDisable(GL_LIGHTING)

    def draw(self):
        if self.display_list is None:
            self.compile()
        self.enable_lighting()
        glCallList(self.display_list)
        self.disable_lighting()


class BallScene:
    def __init__(self):
        self.ball = Ball(1.1, (0.95, 0.45, 0.3))

    def draw(self):
        self.ball.draw()

