import math
import random
from OpenGL.GL import *


class Stars:
    def __init__(self, count=450, radius=170.0, seed=0):
        self.radius = radius
        self.random_generator = random.Random(seed)
        self.color = (1.0, 0.98, 0.92)
        self.bright_stars, self.faint_stars = self._build(count)

    def _build(self, count):
        bright = []
        faint = []
        for _ in range(count):
            height = self.random_generator.uniform(-1.0, 1.0)
            angle = self.random_generator.uniform(0.0, math.tau)
            ring = math.sqrt(max(0.0, 1.0 - height * height))
            point = (math.cos(angle) * ring * self.radius,
                     height * self.radius,
                     math.sin(angle) * ring * self.radius)
            twinkle = self.random_generator.uniform(0.45, 1.0)
            if self.random_generator.random() < 0.22:
                bright.append((point, twinkle))
            else:
                faint.append((point, twinkle * 0.7))
        return bright, faint

    def _draw_group(self, group, point_size, brightness):
        glPointSize(point_size)
        glBegin(GL_POINTS)
        for point, twinkle in group:
            glColor4f(self.color[0], self.color[1], self.color[2], brightness * twinkle)
            glVertex3f(*point)
        glEnd()

    def draw(self, brightness, eye):
        if brightness <= 0.01:
            return
        glDisable(GL_LIGHTING)
        glDisable(GL_FOG)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glDepthMask(GL_FALSE)
        glPushMatrix()
        glTranslatef(eye[0], eye[1], eye[2])
        self._draw_group(self.faint_stars, 1.7, brightness)
        self._draw_group(self.bright_stars, 2.8, brightness)
        glPopMatrix()
        glDepthMask(GL_TRUE)
        glDisable(GL_BLEND)
        glEnable(GL_FOG)
        glEnable(GL_LIGHTING)
