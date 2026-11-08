import math
import random

from OpenGL.GL import (
    GL_AMBIENT,
    GL_DIFFUSE,
    GL_LIGHT0,
    GL_LIGHT1,
    GL_LIGHT2,
    GL_LIGHT_MODEL_AMBIENT,
    GL_LIGHTING,
    GL_POSITION,
    GL_SPECULAR,
    glEnable,
    glLightModelfv,
    glLightfv,
    glPopMatrix,
    glPushMatrix,
    glScalef,
)
from OpenGL.GLU import gluLookAt

from lib.three_mirrors.mirror_renderer import ReflectorSet
from lib.urban.glass import GlassStreet, GlassStyle, TowerPlan, TowerTier
from lib.urban.neon.balcony import Balcony, StreetCorner
from lib.urban.neon.caption_screen import CaptionScreen
from lib.urban.neon.palette import NeonPalette
from lib.urban.neon.signs import FacadeFace, GlowSprites, SignArtLibrary, SignDresser, SignField
from lib.urban.neon.street import Crowd, CrowdArea, Lane, Rain, StreetLamps, Traffic, WetStreet
from lib.urban.neon.textures import ClothPainter, GlTexture, SignPainter, SpritePainter, TextureAtlas
from lib.urban.neon.woman import Woman
from lib.urban.shapes import Shapes
from lib.vector3 import Vector3


class BalconyCamera:

    def __init__(self, eye, target):
        self.base_eye = eye
        self.base_target = target
        self.sway = Vector3(0.25, 0.12, 0.18)
        self.sway_speeds = (0.11, 0.17, 0.08)
        self.pan_reach = 3.5
        self.pan_speed = 0.05
        self.elapsed = 0.0
        self.paused = False

    def toggle_pause(self):
        self.paused = not self.paused

    def update(self, seconds):
        if not self.paused:
            self.elapsed += seconds

    def eye(self):
        time = self.elapsed
        return self.base_eye + Vector3(self.sway.x * math.sin(time * self.sway_speeds[0]),
                                       self.sway.y * math.sin(time * self.sway_speeds[1]),
                                       self.sway.z * math.sin(time * self.sway_speeds[2]))

    def target(self):
        return self.base_target + Vector3(self.pan_reach * math.sin(self.elapsed * self.pan_speed), 0.0, 0.0)

    def forward(self):
        return (self.target() - self.eye()).normalized()

    def right(self):
        return self.forward().cross(Vector3(0.0, 1.0, 0.0)).normalized()

    def up(self):
        return self.right().cross(self.forward()).normalized()

    def look(self):
        gluLookAt(*self.eye(), *self.target(), 0.0, 1.0, 0.0)


class NeonGlassStyles:

    def __init__(self):
        self.variants = [self._variant((0.18, 0.26, 0.27), 0.16), self._variant((0.22, 0.24, 0.2), 0.12),
                         self._variant((0.14, 0.2, 0.26), 0.2)]

    def _variant(self, tint, lit_chance):
        style = GlassStyle()
        style.pane_tint = tint
        style.pane_opacity = 0.55
        style.lit_pane_chance = lit_chance
        style.lit_pane_tint = (1.0, 0.85, 0.55)
        style.lit_pane_glow = (0.42, 0.34, 0.2, 1.0)
        style.floor_height = 2.2
        style.column_width = 2.4
        style.mullion_gap = 0.14
        style.blur = 0.3
        return style

    def pick(self, randomness):
        return randomness.choice(self.variants)


class BlockPlanner:

    def __init__(self, styles, randomness):
        self.styles = styles
        self.randomness = randomness
        self.width_range = (9.0, 16.0)
        self.depth_range = (12.0, 18.0)
        self.setback_shrink = 0.75
        self.setback_height_range = (6.0, 14.0)
        self.planned = 0

    def plans(self, count, height_range):
        return [self.plan(height_range) for _ in range(count)]

    def plans_within(self, length, gap, height_range):
        chosen = []
        while True:
            candidate = self.plan(height_range)
            if GlassStreet.length_of(chosen + [candidate], gap) > length:
                return chosen
            chosen.append(candidate)

    def plan(self, height_range):
        width = round(self.randomness.uniform(*self.width_range))
        depth = round(self.randomness.uniform(*self.depth_range))
        tiers = [TowerTier(width, depth, round(self.randomness.uniform(*height_range)))]
        if self.randomness.random() < 0.45:
            tiers.append(TowerTier(width * self.setback_shrink, depth * self.setback_shrink,
                                   round(self.randomness.uniform(*self.setback_height_range))))
        self.planned += 1
        return TowerPlan(tiers, self.styles.pick(self.randomness), seed=self.planned)


class NeonStreetScene:

    def __init__(self, seed):
        self.randomness = random.Random(seed)
        self.palette = NeonPalette()
        self.balcony_height = 14.0
        self.rail_z = -2.0
        self.left_wall_x = -9.0
        self.avenue = (-10.0, 6.0)
        self.tower_gap = 0.6
        self.right_row_length = 44.0
        self.reflection_stretch = 1.35
        self.camera = BalconyCamera(Vector3(0.8, 16.2, 3.0), Vector3(8.0, 7.0, -45.0))
        self.ambient = (0.12, 0.15, 0.14, 1.0)
        self.lights = (
            (GL_LIGHT0, (0.3, -0.25, -1.0, 0.0), (1.0, 0.8, 0.45, 1.0)),
            (GL_LIGHT1, (-0.6, 0.5, 0.8, 0.0), (0.2, 0.55, 0.5, 1.0)),
            (GL_LIGHT2, (1.0, 0.2, -0.2, 0.0), (0.65, 0.2, 0.45, 1.0)),
        )
        self.caption_text = "Komoda & Amiga + is a paper magazine dedicated to Commodore computers"
        self.caption_color = (60, 240, 230)
        self.caption_rise = 3.6
        self.caption_height = 1.7
        self.caption_margin = 1.0
        self.blocks = []
        self.reflector_set = None

    def build(self):
        shapes = Shapes()
        atlas = TextureAtlas(2048)
        library = SignArtLibrary(SignPainter(self.palette, self.randomness), SpritePainter(), atlas)
        self.atlas_texture = atlas.upload()
        shirt = GlTexture(ClothPainter(self.palette, self.randomness).graffiti_shirt(), repeating=True)
        self.blocks = self._lay_out_blocks(BlockPlanner(NeonGlassStyles(), self.randomness))
        for block in self.blocks:
            block.prepare()
        self.reflector_set = ReflectorSet([facade for block in self.blocks for facade in block.reflectors()])
        self.signs = SignField(self.randomness)
        self._dress_blocks(SignDresser(library, self.randomness))
        self.signs.seal(library.glow_region)
        self.caption = self._hang_caption()
        self.caption.prepare()
        self.street = WetStreet(self.palette, -140.0, 160.0, 40.0, -200.0)
        self.street.add_crossing(-2.0, -20.0, 12.0, along_x=True)
        self.street.add_crossing(20.0, -58.0, 8.0, along_x=False)
        self.street.prepare()
        self.lamps = self._place_lamps()
        self.lamps.prepare(shapes)
        self.traffic = self._route_traffic()
        self.traffic.prepare(shapes)
        self.crowd = Crowd([CrowdArea(7.0, 44.0, -14.0, -53.0), CrowdArea(-8.5, -7.0, -6.0, -50.0)], 380,
                           library.walker_regions, self.randomness)
        self.rain = Rain(2600, Vector3(-30.0, 0.0, -75.0), Vector3(50.0, 40.0, 6.0), self.randomness)
        self.balcony = Balcony(self.palette, self.left_wall_x, 10.0, self.rail_z, self.balcony_height)
        self.balcony.prepare(shapes)
        self.corner = StreetCorner(self.palette, self.left_wall_x, self.balcony_height, self.rail_z)
        self.corner.prepare(shapes)
        self.woman = Woman(Vector3(-1.4, self.balcony_height, self.rail_z + 0.55), self.palette, shirt)
        self.woman.prepare()
        self.glows = GlowSprites(library.glow_region)
        self._refresh_glows()

    def _lay_out_blocks(self, planner):
        along_x = Vector3(1.0, 0.0, 0.0)
        toward_camera = Vector3(0.0, 0.0, 1.0)
        blocks = []
        for front_z, count, heights in ((-64.0, 4, (30.0, 55.0)), (-90.0, 5, (50.0, 85.0)), (-118.0, 5, (70.0, 110.0))):
            left_plans = planner.plans(count, heights)
            right_plans = planner.plans(count, heights)
            left_start = Vector3(self.avenue[0] - GlassStreet.length_of(left_plans, self.tower_gap), 0.0, front_z)
            blocks.append(GlassStreet(left_plans, self.tower_gap, left_start, along_x, toward_camera))
            blocks.append(GlassStreet(right_plans, self.tower_gap, Vector3(self.avenue[1], 0.0, front_z),
                                      along_x, toward_camera))
        right_plans = planner.plans_within(self.right_row_length, self.tower_gap, (25.0, 45.0))
        blocks.append(GlassStreet(right_plans, self.tower_gap, Vector3(46.0, 0.0, -10.0),
                                  Vector3(0.0, 0.0, -1.0), Vector3(-1.0, 0.0, 0.0)))
        neighbour = TowerPlan([TowerTier(58.0, 17.0, 48.0)], planner.styles.pick(self.randomness), seed=99)
        blocks.append(GlassStreet([neighbour], 0.0, Vector3(self.left_wall_x, 0.0, 10.0),
                                  Vector3(0.0, 0.0, -1.0), Vector3(1.0, 0.0, 0.0)))
        return blocks

    def _dress_blocks(self, dresser):
        eye = self.camera.base_eye
        for block in self.blocks:
            for facade in block.reflectors():
                face = FacadeFace.of_glass_facade(facade)
                center = face.point(face.width / 2.0, face.height / 2.0, 0.0)
                toward_eye = (eye - center).normalized()
                if face.normal.dot(toward_eye) > 0.1:
                    distance = (eye - center).length()
                    dresser.dress(face, self.signs, 1.0 if distance < 110.0 else 0.5)

    def _hang_caption(self):
        tower_across_street = self.blocks[1].towers[0]
        face = FacadeFace.of_glass_facade(tower_across_street.reflectors()[0])
        width = face.width - 2.0 * self.caption_margin
        return CaptionScreen(face, self.caption_margin, self.caption_rise, width, self.caption_height,
                             self.caption_text, self.caption_color)

    def _place_lamps(self):
        lamps = StreetLamps(self.palette)
        for lamp_z in (-6.0, -22.0, -38.0, -54.0):
            lamps.add(Vector3(4.6, 0.0, lamp_z), Vector3(-1.0, 0.0, 0.0))
        for lamp_x in (10.0, 30.0, 40.0):
            lamps.add(Vector3(lamp_x, 0.0, -54.5), Vector3(0.0, 0.0, -1.0))
        return lamps

    def _route_traffic(self):
        traffic = Traffic(self.palette, self.randomness)
        traffic.add_lane(Lane(Vector3(-5.0, 0.0, -170.0), Vector3(-5.0, 0.0, 30.0)), 9)
        traffic.add_lane(Lane(Vector3(1.0, 0.0, 30.0), Vector3(1.0, 0.0, -170.0)), 9)
        traffic.add_lane(Lane(Vector3(-140.0, 0.0, -56.5), Vector3(160.0, 0.0, -56.5)), 8)
        traffic.add_lane(Lane(Vector3(160.0, 0.0, -60.5), Vector3(-140.0, 0.0, -60.5)), 8)
        return traffic

    def _refresh_glows(self):
        centers, sizes, tints = [], [], []
        for source in (self.lamps.glow_arrays(), self.corner.glow_arrays(), self.traffic.glow_arrays()):
            centers.extend(source[0])
            sizes.extend(source[1])
            tints.extend(source[2])
        self.glows.set(centers, sizes, tints)

    def configure(self):
        glLightModelfv(GL_LIGHT_MODEL_AMBIENT, self.ambient)
        for slot, _, color in self.lights:
            glEnable(slot)
            glLightfv(slot, GL_DIFFUSE, color)
            glLightfv(slot, GL_SPECULAR, color)
            glLightfv(slot, GL_AMBIENT, (0.0, 0.0, 0.0, 1.0))

    def set_blur(self, blur):
        for block in self.blocks:
            block.set_blur(blur)

    @property
    def blur(self):
        return self.blocks[0].blur

    def update(self, seconds):
        self.camera.update(seconds)
        self.signs.update(seconds)
        self.caption.update(seconds)
        self.traffic.update(seconds)
        self.crowd.update(seconds)
        self.rain.update(seconds)
        self.woman.update(seconds)
        for block in self.blocks:
            block.update(seconds)
        self._refresh_glows()

    def illuminate(self):
        glEnable(GL_LIGHTING)
        for slot, direction, _ in self.lights:
            glLightfv(slot, GL_POSITION, direction)

    def draw(self):
        self._draw_wet_reflections()
        self.street.draw()
        for block in self.blocks:
            block.draw()
        self.lamps.draw()
        self.traffic.draw()
        self.corner.draw()
        self.balcony.draw()
        self.woman.draw()
        self.signs.draw_signs(self.atlas_texture)
        self.signs.draw_glows(self.atlas_texture)
        self.caption.draw()
        self.glows.draw(self.atlas_texture, self.camera.right(), self.camera.up())
        self.crowd.draw(self.atlas_texture, self.camera.right())
        self.rain.draw()

    def _draw_wet_reflections(self):
        glPushMatrix()
        glScalef(1.0, -self.reflection_stretch, 1.0)
        self.signs.draw_signs(self.atlas_texture)
        self.signs.draw_glows(self.atlas_texture)
        self.caption.draw()
        self.glows.draw(self.atlas_texture, self.camera.right(), self.camera.up())
        glPopMatrix()
