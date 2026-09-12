import random
from OpenGL.GL import *
from OpenGL.GLU import *


class Cloud:
    def __init__(self, x, y, z, size=5.0, puff_count=11, seed=0):
        self.x = x
        self.y = y
        self.z = z
        self.size = size
        self.puff_count = puff_count
        self.random_generator = random.Random(seed)
        self.base_color = (0.80, 0.82, 0.86)
        self.quadric = gluNewQuadric()
        gluQuadricNormals(self.quadric, GLU_SMOOTH)
        self.puffs = self._build_puffs()
        self.display_list = self._compile()

    def _build_puffs(self):
        puffs = []
        for _ in range(self.puff_count):
            offset_x = self.random_generator.uniform(-1.0, 1.0)
            offset_z = self.random_generator.uniform(-0.55, 0.55)
            offset_y = self.random_generator.uniform(-0.10, 0.20) - abs(offset_x) * 0.12
            radius = self.random_generator.uniform(0.34, 0.58) * (1.0 - abs(offset_x) * 0.35)
            shade = self.random_generator.uniform(0.88, 1.06)
            puffs.append((offset_x, offset_y, offset_z, radius, shade))
        return puffs

    def _compile(self):
        display_list = glGenLists(1)
        glNewList(display_list, GL_COMPILE)
        for offset_x, offset_y, offset_z, radius, shade in self.puffs:
            glColor3f(min(1.0, self.base_color[0] * shade),
                      min(1.0, self.base_color[1] * shade),
                      min(1.0, self.base_color[2] * shade))
            glPushMatrix()
            glTranslatef(offset_x * self.size, offset_y * self.size, offset_z * self.size)
            glScalef(1.0, 0.68, 1.0)
            gluSphere(self.quadric, radius * self.size, 14, 12)
            glPopMatrix()
        glEndList()
        return display_list

    def draw(self):
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        glCallList(self.display_list)
        glPopMatrix()
