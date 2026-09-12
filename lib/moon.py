from OpenGL.GL import *
from OpenGL.GLU import *


class Moon:
    def __init__(self, name, radius, orbit_radius, angular_speed, inclination=0.0,
                 color=(0.74, 0.74, 0.72), phase=0.0, slices=18, stacks=14):
        self.name = name
        self.radius = radius
        self.orbit_radius = orbit_radius
        self.angular_speed = angular_speed
        self.inclination = inclination
        self.color = color
        self.angle = phase
        self.slices = slices
        self.stacks = stacks
        self.quadric = gluNewQuadric()
        gluQuadricNormals(self.quadric, GLU_SMOOTH)

    def update(self, dt):
        self.angle += self.angular_speed * dt

    def draw(self):
        glPushMatrix()
        glRotatef(self.inclination, 0.0, 0.0, 1.0)
        glRotatef(self.angle, 0.0, 1.0, 0.0)
        glTranslatef(self.orbit_radius, 0.0, 0.0)
        glColor3f(*self.color)
        gluSphere(self.quadric, self.radius, self.slices, self.stacks)
        glPopMatrix()
