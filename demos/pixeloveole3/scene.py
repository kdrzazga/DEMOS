import math

from OpenGL.GL import *
from OpenGL.GLU import *

from demos.pixeloveole3.city import DistantCity
from demos.pixeloveole3.library import Library
from lib.urban.residential import BuildingStyle, Footprint, PlainBuilding, Tenement
from lib.urban.shapes import Shapes
from demos.pixeloveole3.sky import Sky
from demos.pixeloveole3.streets import RoadPath, StreetScape
from lib.urban.textures import TextureFactory
from demos.pixeloveole3.vegetation import Grove


class OrbitCamera:
    def __init__(self, target, radius, height, heading, sway, sway_speed):
        self.target = target
        self.radius = radius
        self.height = height
        self.heading = heading
        self.sway = sway
        self.sway_speed = sway_speed

    def view(self, elapsed):
        angle = self.heading + self.sway * math.sin(elapsed * self.sway_speed)
        eye = (self.target[0] + self.radius * math.sin(angle),
               self.height + 2.0 * math.sin(elapsed * self.sway_speed * 0.7),
               self.target[2] + self.radius * math.cos(angle))
        return eye, self.target


class LibraryScene:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.zenith = (0.33, 0.56, 0.86)
        self.horizon = (0.80, 0.86, 0.93)
        self.sun_direction = (-0.35, 0.9, 0.55, 0.0)
        self._init_gl()
        self.shapes = Shapes()
        factory = TextureFactory()
        roof_texture = factory.upload(factory.roof_tiles())
        paving_texture = factory.upload(factory.paving())
        self.library = Library(roof_texture, factory)
        self.office = self._create_office(roof_texture)
        self.tenement = self._create_tenement(roof_texture)
        self.street = StreetScape(RoadPath(), paving_texture)
        self.city = DistantCity(roof_texture)
        self.grove = Grove(((20.0, -36.0), (27.0, -44.0), (18.0, -50.0), (36.0, -28.0), (45.0, -33.0),
                            (53.0, -27.0), (61.0, -38.0), (66.0, -24.0), (90.0, -40.0), (94.0, -18.0),
                            (92.0, 4.0), (-60.0, -20.0), (-62.0, -45.0), (-58.0, -75.0)), seed=21)
        self.sky = Sky(self.zenith, self.horizon)
        self.sky.build(self.shapes)
        self.camera = OrbitCamera((15.0, 4.0, -6.0), 62.0, 34.0, -0.2, 0.35, 0.12)
        self.world = self._compile()

    def _init_gl(self):
        glViewport(0, 0, self.width, self.height)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glEnable(GL_COLOR_MATERIAL)
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
        glShadeModel(GL_SMOOTH)
        glEnable(GL_NORMALIZE)
        glHint(GL_PERSPECTIVE_CORRECTION_HINT, GL_NICEST)
        glLightfv(GL_LIGHT0, GL_DIFFUSE, (0.72, 0.70, 0.64, 1.0))
        glLightfv(GL_LIGHT0, GL_AMBIENT, (0.0, 0.0, 0.0, 1.0))
        glLightModelfv(GL_LIGHT_MODEL_AMBIENT, (0.46, 0.48, 0.53, 1.0))
        glEnable(GL_FOG)
        glFogi(GL_FOG_MODE, GL_LINEAR)
        glFogfv(GL_FOG_COLOR, (*self.horizon, 1.0))
        glFogf(GL_FOG_START, 180.0)
        glFogf(GL_FOG_END, 720.0)
        glClearColor(*self.horizon, 1.0)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(50.0, self.width / self.height, 1.0, 1600.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

    def _create_office(self, roof_texture):
        style = BuildingStyle(wall=(0.80, 0.79, 0.60), roof=(0.88, 0.48, 0.34), ridge=(0.70, 0.34, 0.25),
                              trim=(0.62, 0.62, 0.52), plinth=(0.55, 0.56, 0.52), frame=(0.96, 0.96, 0.94),
                              glass=(0.16, 0.20, 0.25), sill=(0.36, 0.42, 0.48))
        rows = ((1.7, 2.0, 1.3), (5.4, 2.0, 1.3), (9.0, 2.0, 1.3), (12.8, 1.4, 1.1))
        return PlainBuilding(style, Footprint(31.0, -20.0, 56.0, 0.0), 15.8, 5.5, rows,
                             {"front": 7, "east": 5, "back": 7}, roof_texture)

    def _create_tenement(self, roof_texture):
        style = BuildingStyle(wall=(0.86, 0.78, 0.62), roof=(0.50, 0.52, 0.55), ridge=(0.40, 0.42, 0.45),
                              trim=(0.74, 0.67, 0.53), plinth=(0.62, 0.58, 0.52), frame=(0.95, 0.94, 0.90),
                              glass=(0.18, 0.21, 0.25), sill=(0.70, 0.66, 0.58))
        rows = ((1.5, 1.9, 1.2), (5.0, 1.9, 1.2), (8.4, 1.9, 1.2), (11.6, 1.6, 1.1))
        return Tenement(style, Footprint(0.0, -54.0, 11.0, -24.0), 14.0, 5.0, rows,
                        {"west": 8, "east": 6, "back": 3}, roof_texture, balcony_columns=(1, 2, 5, 6),
                        dormer_positions=(-46.0, -41.0, -36.0, -31.0), railing_color=(0.36, 0.30, 0.25))

    def _compile(self):
        display_list = glGenLists(1)
        glNewList(display_list, GL_COMPILE)
        for part in (self.street, self.library, self.office, self.tenement, self.city, self.grove):
            part.draw(self.shapes)
        glEndList()
        return display_list

    def render(self, elapsed, view=None):
        """`view` = (eye, target) overrides the orbiting camera."""
        glClearColor(*self.horizon, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        eye, target = view or self.camera.view(elapsed)
        gluLookAt(eye[0], eye[1], eye[2], target[0], target[1], target[2], 0.0, 1.0, 0.0)
        self.sky.draw(eye)
        glLightfv(GL_LIGHT0, GL_POSITION, self.sun_direction)
        glCallList(self.world)
        self.library.draw_animated(elapsed)

    def render_blank(self):
        glClearColor(0.0, 0.0, 0.0, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
