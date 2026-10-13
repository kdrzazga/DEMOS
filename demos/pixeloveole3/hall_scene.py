import math

from OpenGL.GL import *
from OpenGL.GLU import *

from demos.pixeloveole3.hall import Hall, HallPalette, floor_tiles_surface
from lib.urban.shapes import Shapes
from lib.urban.textures import TextureFactory


class HallScene:
    """Renders the empty entrance hall. By default it is seen from where
    models/hall.jpg was taken (just inside the street door, looking at the
    opening into the hall); `render(elapsed, view)` takes an (eye, target)
    override like LibraryScene."""

    def __init__(self, width, height, field_of_view=60.0):
        self.width = width
        self.height = height
        self.field_of_view = field_of_view
        self.background = (0.05, 0.04, 0.04)
        self.light_direction = (0.3, 1.0, 0.6, 0.0)
        self.photo_eye = (0.8, 1.7, 0.4)
        self.photo_target = (0.4, 1.5, -10.0)
        self.sway = 0.08
        self.sway_speed = 0.3
        self._init_gl()
        self.shapes = Shapes()
        palette = HallPalette()
        floor_texture = TextureFactory().upload(floor_tiles_surface(palette))
        self.hall = Hall(floor_texture, palette)
        self.display_list = self._compile()

    def _init_gl(self):
        glViewport(0, 0, self.width, self.height)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glEnable(GL_COLOR_MATERIAL)
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
        glShadeModel(GL_SMOOTH)
        glEnable(GL_NORMALIZE)
        glDisable(GL_FOG)
        glLightfv(GL_LIGHT0, GL_DIFFUSE, (0.45, 0.43, 0.40, 1.0))
        glLightfv(GL_LIGHT0, GL_AMBIENT, (0.0, 0.0, 0.0, 1.0))
        glLightModelfv(GL_LIGHT_MODEL_AMBIENT, (0.62, 0.60, 0.56, 1.0))
        glLightModeli(GL_LIGHT_MODEL_TWO_SIDE, GL_TRUE)

    def _compile(self):
        display_list = glGenLists(1)
        glNewList(display_list, GL_COMPILE)
        self.hall.draw(self.shapes)
        glEndList()
        return display_list

    def default_view(self, elapsed):
        angle = self.sway * math.sin(elapsed * self.sway_speed)
        eye_x, eye_y, eye_z = self.photo_eye
        target_x, target_y, target_z = self.photo_target
        distance = eye_z - target_z
        return self.photo_eye, (target_x + distance * math.sin(angle), target_y, eye_z - distance * math.cos(angle))

    def render(self, elapsed, view=None):
        glClearColor(*self.background, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(self.field_of_view, self.width / self.height, 0.05, 100.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        eye, target = view or self.default_view(elapsed)
        gluLookAt(*eye, *target, 0.0, 1.0, 0.0)
        glEnable(GL_LIGHTING)
        glLightfv(GL_LIGHT0, GL_POSITION, self.light_direction)
        glCallList(self.display_list)
        glPushAttrib(GL_ENABLE_BIT | GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glDisable(GL_LIGHTING)
        glDisable(GL_TEXTURE_2D)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE)
        glDepthMask(GL_FALSE)
        self.hall.draw_glow()
        glPopAttrib()
