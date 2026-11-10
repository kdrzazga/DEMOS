import math

from OpenGL.GL import *
from OpenGL.GLU import gluLookAt, gluPerspective

from lib.three_mirrors.mirror_renderer import ReflectorSet
from lib.urban.glass.glass_style import GlassStyle
from lib.urban.glass.night_lights import DisplayList
from lib.urban.shapes import Shapes
from lib.vector3 import Vector3


class NightGround:

    def __init__(self, half_extent):
        self.half_extent = half_extent
        self.cell_size = 3.0
        self.color = (0.06, 0.065, 0.075)
        self.surface = None

    def prepare(self):
        if self.surface is None:
            self.surface = DisplayList(self._emit)

    def draw(self):
        self.surface.call()

    def _emit(self):
        cells = int(2.0 * self.half_extent / self.cell_size)
        glColor3f(*self.color)
        glNormal3f(0.0, 1.0, 0.0)
        glBegin(GL_QUADS)
        for row in range(cells):
            for column in range(cells):
                near_x = -self.half_extent + column * self.cell_size
                near_z = -self.half_extent + row * self.cell_size
                far_x = near_x + self.cell_size
                far_z = near_z + self.cell_size
                glVertex3f(near_x, 0.0, far_z)
                glVertex3f(far_x, 0.0, far_z)
                glVertex3f(far_x, 0.0, near_z)
                glVertex3f(near_x, 0.0, near_z)
        glEnd()


class OrbitCamera:

    def __init__(self, target, distance, lowest_height, highest_height):
        self.target = target
        self.distance = distance
        self.lowest_height = lowest_height
        self.highest_height = highest_height
        self.orbit_speed = 0.07
        self.rise_speed = 0.13
        self.elapsed = 0.0
        self.paused = False

    def toggle_pause(self):
        self.paused = not self.paused

    def update(self, seconds):
        if not self.paused:
            self.elapsed += seconds

    def eye(self):
        angle = self.elapsed * self.orbit_speed
        middle = (self.lowest_height + self.highest_height) / 2.0
        swing = (self.highest_height - self.lowest_height) / 2.0
        height = middle - swing * math.cos(self.elapsed * self.rise_speed)
        return Vector3(self.target.x + self.distance * math.sin(angle), height,
                       self.target.z + self.distance * math.cos(angle))

    def look(self):
        gluLookAt(*self.eye(), *self.target, 0.0, 1.0, 0.0)


class GlassPalette:

    def standard(self):
        return GlassStyle()

    def greener(self):
        style = GlassStyle()
        style.pane_tint = (0.48, 0.8, 0.95)
        style.column_width = 1.1
        return style

    def darker(self):
        style = GlassStyle()
        style.pane_tint = (0.42, 0.62, 0.9)
        style.lit_pane_chance = 0.08
        style.floor_height = 0.95
        return style

    def all_styles(self):
        return (self.standard(), self.greener(), self.darker())


class NightScene:

    def __init__(self, name, streets, ground, camera, fog_density):
        self.name = name
        self.streets = streets
        self.ground = ground
        self.camera = camera
        self.fog_density = fog_density
        self.night = (0.008, 0.01, 0.02, 1.0)
        self.field_of_view = 50.0
        self.near_plane = 0.5
        self.far_plane = 500.0
        self.ambient = (0.02, 0.025, 0.04, 1.0)
        self.flood_distance = 11.0
        self.flood_height = 0.6
        self.light_slots = (GL_LIGHT0, GL_LIGHT1, GL_LIGHT2, GL_LIGHT3, GL_LIGHT4, GL_LIGHT5, GL_LIGHT6, GL_LIGHT7)
        self.slots_taken = 0
        self.orbs = []
        self.flood_lights = []
        self.shapes = None
        self.reflector_set = ReflectorSet([facade for street in streets for facade in street.reflectors()])

    def _take_slot(self):
        if self.slots_taken == len(self.light_slots):
            return None
        slot = self.light_slots[self.slots_taken]
        self.slots_taken += 1
        return slot

    def add_orb(self, orb):
        orb.slot = self._take_slot()
        self.orbs.append(orb)

    def flood_frontages(self, frontages, flood_light_type):
        for frontage in frontages:
            slot = self._take_slot()
            if slot is not None:
                self.flood_lights.append(flood_light_type(slot, self._flood_position(frontage), frontage.center))

    def _flood_position(self, frontage):
        ahead = frontage.center + frontage.facing * self.flood_distance
        return Vector3(ahead.x, self.flood_height, ahead.z)

    def every_light(self):
        return self.orbs + self.flood_lights

    def prepare(self):
        self.shapes = Shapes()
        self.ground.prepare()
        for street in self.streets:
            street.prepare()

    def activate(self, window_size):
        self._init_gl(window_size)
        self._configure()

    def _init_gl(self, window_size):
        width, height = window_size
        glViewport(0, 0, width, height)
        glEnable(GL_DEPTH_TEST)
        glDepthFunc(GL_LEQUAL)
        glDisable(GL_CULL_FACE)
        glEnable(GL_NORMALIZE)
        glShadeModel(GL_SMOOTH)
        glEnable(GL_COLOR_MATERIAL)
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
        glClearColor(*self.night)
        glClearStencil(0)
        glEnable(GL_FOG)
        glFogi(GL_FOG_MODE, GL_EXP2)
        glHint(GL_FOG_HINT, GL_FASTEST)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(self.field_of_view, width / height, self.near_plane, self.far_plane)
        glMatrixMode(GL_MODELVIEW)

    def _configure(self):
        glFogf(GL_FOG_DENSITY, self.fog_density)
        glFogfv(GL_FOG_COLOR, self.night)
        glLightModelfv(GL_LIGHT_MODEL_AMBIENT, self.ambient)
        glLightModeli(GL_LIGHT_MODEL_LOCAL_VIEWER, GL_TRUE)
        for slot in self.light_slots:
            glDisable(slot)
        for light in self.every_light():
            light.configure(self.shapes)

    def change_blur(self, step):
        blur = self.blur + step
        for street in self.streets:
            street.set_blur(blur)

    @property
    def blur(self):
        return self.streets[0].blur

    @property
    def flood_lights_on(self):
        return self.flood_lights[0].switched_on

    def toggle_flood_lights(self):
        switched_on = not self.flood_lights_on
        for flood_light in self.flood_lights:
            flood_light.switch(switched_on)

    def update(self, seconds):
        for street in self.streets:
            street.update(seconds)
        for orb in self.orbs:
            orb.update(seconds)
        self.camera.update(seconds)

    def status(self):
        return "blur: {:.2f}, flood lights: {}".format(self.blur, "on" if self.flood_lights_on else "off")

    def render(self, renderer):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT | GL_STENCIL_BUFFER_BIT)
        glLoadIdentity()
        self.camera.look()
        renderer.render(self.reflector_set, self, self.camera.eye())

    def illuminate(self):
        glEnable(GL_LIGHTING)
        for light in self.every_light():
            light.illuminate()

    def draw(self):
        self.ground.draw()
        for street in self.streets:
            street.draw()
        for light in self.every_light():
            light.draw()
