from OpenGL.GL import *


class LogoPart:
    """One separately movable element of the 3D logo.

    Subclasses emit their geometry in local coordinates (around their own
    pivot) from `build()`; it is compiled into a display list on first draw,
    so instances may be created before the GL context exists. Position,
    rotation (degrees), scale and visibility can be animated freely; `home`
    remembers where the part sits in the assembled logo.
    """

    def __init__(self, name, x=0.0, y=0.0, z=0.0):
        self.name = name
        self.x, self.y, self.z = x, y, z
        self.home = (x, y, z)
        self.yaw = 0.0
        self.pitch = 0.0
        self.roll = 0.0
        self.scale = 1.0
        self.visible = True
        self.display_list = 0

    def build(self):
        raise NotImplementedError

    def go_home(self):
        self.x, self.y, self.z = self.home
        self.yaw = self.pitch = self.roll = 0.0
        self.scale = 1.0

    def compile(self):
        self.display_list = glGenLists(1)
        glNewList(self.display_list, GL_COMPILE)
        self.build()
        glEndList()

    def release(self):
        if self.display_list:
            glDeleteLists(self.display_list, 1)
            self.display_list = 0

    def draw(self):
        if not self.visible:
            return
        if not self.display_list:
            self.compile()
        glPushAttrib(GL_ENABLE_BIT | GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT | GL_LINE_BIT | GL_CURRENT_BIT)
        glDisable(GL_LIGHTING)
        glDisable(GL_TEXTURE_2D)
        glDisable(GL_CULL_FACE)
        glEnable(GL_DEPTH_TEST)
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        glRotatef(self.yaw, 0.0, 1.0, 0.0)
        glRotatef(self.pitch, 1.0, 0.0, 0.0)
        glRotatef(self.roll, 0.0, 0.0, 1.0)
        glScalef(self.scale, self.scale, self.scale)
        glCallList(self.display_list)
        glPopMatrix()
        glPopAttrib()
