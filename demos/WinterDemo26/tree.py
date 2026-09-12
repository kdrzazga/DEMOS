import random
from OpenGL.GL import *
from OpenGL.GLU import *


class Tree:
    def __init__(self, x, z, ground_height, snow_top=False, seed=0):
        self.x = x
        self.z = z
        self.ground_height = ground_height
        self.snow_top = snow_top
        self.random_generator = random.Random(seed)
        self.trunk_color = (0.36, 0.22, 0.11)
        self.foliage_color = (0.11, 0.44, 0.20)
        self.snow_color = (0.96, 0.98, 1.0)
        self.trunk_radius = 0.17 * self.random_generator.uniform(0.85, 1.2)
        self.trunk_height = 0.9 * self.random_generator.uniform(0.8, 1.2)
        self.tier_count = self.random_generator.randint(3, 4)
        self.base_radius = 1.15 * self.random_generator.uniform(0.85, 1.25)
        self.total_foliage_height = 3.4 * self.random_generator.uniform(0.85, 1.25)
        self.quadric = gluNewQuadric()
        gluQuadricNormals(self.quadric, GLU_SMOOTH)
        self.display_list = self._compile()

    def _compile(self):
        display_list = glGenLists(1)
        glNewList(display_list, GL_COMPILE)
        glPushMatrix()
        glRotatef(-90.0, 1.0, 0.0, 0.0)

        glColor3f(*self.trunk_color)
        gluCylinder(self.quadric, self.trunk_radius, self.trunk_radius * 0.8, self.trunk_height, 12, 2)

        tier_height = self.total_foliage_height / self.tier_count
        step_up = tier_height * 0.62
        cone_height = tier_height * 1.5
        bottom = self.trunk_height * 0.9
        summit = bottom
        for tier_index in range(self.tier_count):
            radius = self.base_radius * (1.0 - tier_index / (self.tier_count + 0.6))
            glPushMatrix()
            glTranslatef(0.0, 0.0, bottom)
            glColor3f(*self.foliage_color)
            gluCylinder(self.quadric, radius, 0.0, cone_height, 18, 3)
            if self.snow_top:
                cap_fraction = 0.45
                glTranslatef(0.0, 0.0, cone_height * (1.0 - cap_fraction))
                glColor3f(*self.snow_color)
                gluCylinder(self.quadric, radius * cap_fraction + 0.04, 0.0, cone_height * cap_fraction, 18, 2)
            glPopMatrix()
            summit = bottom + cone_height
            bottom += step_up

        if self.snow_top:
            glColor3f(*self.snow_color)
            glPushMatrix()
            glTranslatef(0.0, 0.0, summit - 0.05)
            gluSphere(self.quadric, self.base_radius * 0.10 + 0.05, 12, 12)
            glPopMatrix()

        glPopMatrix()
        glEndList()
        return display_list

    def draw(self):
        glPushMatrix()
        glTranslatef(self.x, self.ground_height, self.z)
        glCallList(self.display_list)
        glPopMatrix()
