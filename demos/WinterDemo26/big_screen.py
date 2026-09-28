import math
from OpenGL.GL import *


class BigScreen:
    """Party projection screen on two stands: a dark frame around an unlit, animated plasma picture.

    Local frame: centred on x, standing on y=0, the picture faces +z.
    """

    def __init__(self, x, y, z, width=12.0, height=6.75, lift=1.6, columns=32, rows=18):
        self.x = x
        self.y = y
        self.z = z
        self.width = width
        self.height = height
        self.lift = lift
        self.columns = columns
        self.rows = rows
        self.frame_border = 0.25
        self.frame_depth = 0.2
        self.stand_width = 0.18
        self.stand_inset = 0.18
        self.frame_color = (0.06, 0.06, 0.07)
        self.plasma_speed = 0.8
        self.time = 0.0
        self.display_list = self._compile()

    def _box(self, min_corner, max_corner):
        x0, y0, z0 = min_corner
        x1, y1, z1 = max_corner
        faces = (
            ((0.0, 1.0, 0.0), ((x0, y1, z0), (x0, y1, z1), (x1, y1, z1), (x1, y1, z0))),
            ((0.0, -1.0, 0.0), ((x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1))),
            ((0.0, 0.0, 1.0), ((x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1))),
            ((0.0, 0.0, -1.0), ((x1, y0, z0), (x0, y0, z0), (x0, y1, z0), (x1, y1, z0))),
            ((1.0, 0.0, 0.0), ((x1, y0, z1), (x1, y0, z0), (x1, y1, z0), (x1, y1, z1))),
            ((-1.0, 0.0, 0.0), ((x0, y0, z0), (x0, y0, z1), (x0, y1, z1), (x0, y1, z0))),
        )
        glBegin(GL_QUADS)
        for normal, corners in faces:
            glNormal3f(*normal)
            for corner in corners:
                glVertex3f(*corner)
        glEnd()

    def _compile(self):
        half_width = self.width / 2.0 + self.frame_border
        bottom = self.lift - self.frame_border
        top = self.lift + self.height + self.frame_border
        half_depth = self.frame_depth / 2.0
        display_list = glGenLists(1)
        glNewList(display_list, GL_COMPILE)
        glColor3f(*self.frame_color)
        self._box((-half_width, bottom, -half_depth), (half_width, top, half_depth))
        for side in (-1.0, 1.0):
            stand_x = side * (half_width - self.stand_inset)
            self._box((stand_x - self.stand_width / 2.0, 0.0, -half_depth * 1.5),
                      (stand_x + self.stand_width / 2.0, bottom, half_depth * 1.5))
        glEndList()
        return display_list

    def update(self, delta_seconds):
        self.time += delta_seconds

    def _plasma_color(self, u, v, brightness):
        moment = self.time * self.plasma_speed
        wave = (math.sin(u * 7.0 + moment)
                + math.sin(v * 5.0 - moment * 1.3)
                + math.sin((u + v) * 6.0 + moment * 0.7)
                + math.sin(math.hypot(u - 0.5, v - 0.5) * 12.0 - moment * 1.7)) / 4.0
        red = 0.5 + 0.5 * math.sin(math.pi * wave)
        green = 0.5 + 0.5 * math.sin(math.pi * wave + 2.1)
        blue = 0.5 + 0.5 * math.sin(math.pi * wave + 4.2)
        return red * brightness, green * brightness, blue * brightness

    def _draw_picture(self, brightness):
        left = -self.width / 2.0
        front = self.frame_depth / 2.0 + 0.005
        glDisable(GL_LIGHTING)
        for row in range(self.rows):
            v_low = row / self.rows
            v_high = (row + 1) / self.rows
            glBegin(GL_QUAD_STRIP)
            for column in range(self.columns + 1):
                u = column / self.columns
                picture_x = left + u * self.width
                glColor3f(*self._plasma_color(u, v_low, brightness))
                glVertex3f(picture_x, self.lift + v_low * self.height, front)
                glColor3f(*self._plasma_color(u, v_high, brightness))
                glVertex3f(picture_x, self.lift + v_high * self.height, front)
            glEnd()
        glEnable(GL_LIGHTING)

    def draw(self, brightness=1.0):
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        glCallList(self.display_list)
        self._draw_picture(brightness)
        glPopMatrix()
