from OpenGL.GL import *


class Road:
    def __init__(self, x, y, z, length, width, facing=0.0, color=(0.16, 0.17, 0.19),
                 kerb_color=(0.62, 0.65, 0.70), marking_color=(0.66, 0.64, 0.56), marking=True,
                 library=None):
        self.x = x
        self.y = y
        self.z = z
        self.length = length
        self.width = width
        self.facing = facing
        self.color = color
        self.kerb_color = kerb_color
        self.marking_color = marking_color
        self.marking = marking

        self.surface_lift = 0.25
        self.kerb_width = 0.45
        self.marking_width = 0.20
        self.dash_length = 2.2
        self.dash_gap = 2.0

        self.display_list = self.compile_shape() if library is None else library.shape_for(self)

    def _draw_strip(self, left, right, near, far, height, color):
        glColor3f(*color)
        glNormal3f(0.0, 1.0, 0.0)
        glBegin(GL_QUADS)
        glVertex3f(left, height, near)
        glVertex3f(right, height, near)
        glVertex3f(right, height, far)
        glVertex3f(left, height, far)
        glEnd()

    def _draw_surface(self):
        half_width = self.width / 2.0
        half_length = self.length / 2.0
        self._draw_strip(-half_width, half_width, -half_length, half_length,
                         self.surface_lift, self.color)
        for side in (1.0, -1.0):
            outer = side * half_width
            inner = side * (half_width - self.kerb_width)
            self._draw_strip(min(outer, inner), max(outer, inner), -half_length, half_length,
                             self.surface_lift * 1.4, self.kerb_color)

    def _draw_markings(self):
        half_width = self.marking_width / 2.0
        half_length = self.length / 2.0
        step = self.dash_length + self.dash_gap
        near = -half_length + self.dash_gap / 2.0
        while near + self.dash_length <= half_length:
            self._draw_strip(-half_width, half_width, near, near + self.dash_length,
                             self.surface_lift * 1.6, self.marking_color)
            near += step

    def shape_key(self):
        return (round(self.length, 4), round(self.width, 4), self.marking, self.color,
                self.kerb_color, self.marking_color, self.surface_lift, self.kerb_width,
                self.marking_width, self.dash_length, self.dash_gap)

    def compile_shape(self):
        display_list = glGenLists(1)
        glNewList(display_list, GL_COMPILE)
        self._draw_surface()
        if self.marking:
            self._draw_markings()
        glEndList()
        return display_list

    def draw(self):
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        glRotatef(self.facing, 0.0, 1.0, 0.0)
        glCallList(self.display_list)
        glPopMatrix()


class RoadLibrary:
    def __init__(self):
        self.shapes = {}

    def shape_for(self, road):
        key = road.shape_key()
        shape = self.shapes.get(key)
        if shape is None:
            shape = road.compile_shape()
            self.shapes[key] = shape
        return shape

    def shape_count(self):
        return len(self.shapes)
