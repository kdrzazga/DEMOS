import math

from OpenGL.GL import (
    GL_COMPILE,
    GL_QUADS,
    GL_TEXTURE_2D,
    glBegin,
    glCallList,
    glColor3f,
    glDisable,
    glEnable,
    glEnd,
    glEndList,
    glGenLists,
    glNewList,
    glPopMatrix,
    glPushMatrix,
    glRotatef,
    glScalef,
    glVertex3f,
)

STACKS = 8           # horizontal layers of polygons
SLICES = 16          # segments around the ball
RED = (0.95, 0.05, 0.05)
WHITE = (1.0, 1.0, 1.0)


class AmigaBall:
    """Low-poly checkered ball in the style of the Amiga Boing demo."""
    DEFAULT_SPIN_SPEED = 60.0  # degrees per second
    DEFAULT_TILT = 17.0  # classic Boing Ball lean

    def __init__(self, radius=1.0, clockwise=True):
        self.radius = radius
        self.clockwise = clockwise
        self.angle = 0.0
        self.display_list = None
        self.spin_speed = AmigaBall.DEFAULT_SPIN_SPEED
        self.tilt = AmigaBall.DEFAULT_TILT

    def update(self, dt):
        step = self.spin_speed * dt
        if self.clockwise:
            step = -step
        self.angle = (self.angle + step) % 360.0

    def render(self):
        if self.display_list is None:
            self.display_list = self._compile()

        glDisable(GL_TEXTURE_2D)
        glPushMatrix()
        glRotatef(AmigaBall.DEFAULT_TILT, 0.0, 0.0, 1.0)
        glRotatef(self.angle, 0.0, 1.0, 0.0)
        glScalef(self.radius, self.radius, self.radius)
        glCallList(self.display_list)
        glPopMatrix()
        glEnable(GL_TEXTURE_2D)

    def _compile(self):
        list_id = glGenLists(1)
        glNewList(list_id, GL_COMPILE)
        glBegin(GL_QUADS)
        for stack in range(STACKS):
            for segment in range(SLICES):
                glColor3f(*(RED if (stack + segment) % 2 else WHITE))
                for vertex in self._quad(stack, segment):
                    glVertex3f(*vertex)
        glEnd()
        glEndList()
        return list_id

    def _quad(self, stack, segment):
        return (self._vertex(stack, segment),
                self._vertex(stack + 1, segment),
                self._vertex(stack + 1, segment + 1),
                self._vertex(stack, segment + 1))

    def _vertex(self, stack, segment):
        """Unit-sphere point; render() scales it to self.radius."""
        latitude = math.pi * stack / STACKS
        longitude = 2.0 * math.pi * segment / SLICES
        ring = math.sin(latitude)
        return ring * math.cos(longitude), math.cos(latitude), ring * math.sin(longitude)
