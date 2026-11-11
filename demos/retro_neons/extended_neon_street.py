import random

from OpenGL.GL import (
    GL_BLEND,
    GL_COLOR_BUFFER_BIT,
    GL_ENABLE_BIT,
    GL_LIGHTING,
    GL_ONE_MINUS_SRC_ALPHA,
    GL_QUADS,
    GL_SRC_ALPHA,
    glBegin,
    glBlendFunc,
    glColor4f,
    glDisable,
    glEnable,
    glEnd,
    glPopAttrib,
    glPopMatrix,
    glPushAttrib,
    glPushMatrix,
    glScalef,
    glVertex3f,
)

from demos.retro_neons.brand_signs import (BrandedSignField, BrandRule, CaptionArtShelf, CaptionStyle,
                                           VerticalCaptionPainter)
from demos.retro_neons.butterfly_screen import ButterflyWallScreen
from demos.retro_neons.c64_wall_screen import C64WallScreen
from demos.retro_neons.newspaper_woman import NewspaperWoman
from lib.urban.glass import GlassStreet
from demos.retro_neons.matte_caption_screen import MatteCaptionScreen
from lib.urban.neon.neon_street import BlockPlanner, NeonStreetScene
from lib.urban.neon.signs import FacadeFace
from lib.urban.neon.street import Car, CompiledShape, Lane, RouteLane, Traffic
from lib.vector3 import Vector3


class CentreLine:

    def __init__(self, centre_x, near, far):
        self.centre_x = centre_x
        self.near = near
        self.far = far
        self.dash_length = 3.0
        self.dash_gap = 4.0
        self.dash_width = 0.22
        self.lift = 0.02
        self.color = (0.8, 0.82, 0.75, 0.5)
        self.shape = None

    def prepare(self):
        self.shape = CompiledShape(self._emit)

    def draw(self):
        glPushAttrib(GL_ENABLE_BIT | GL_COLOR_BUFFER_BIT)
        glDisable(GL_LIGHTING)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        self.shape.call()
        glPopAttrib()

    def _emit(self):
        half_width = self.dash_width / 2.0
        left = self.centre_x - half_width
        right = self.centre_x + half_width
        glColor4f(*self.color)
        glBegin(GL_QUADS)
        dash_start = self.near
        while dash_start - self.dash_length > self.far:
            dash_end = dash_start - self.dash_length
            glVertex3f(left, self.lift, dash_start)
            glVertex3f(right, self.lift, dash_start)
            glVertex3f(right, self.lift, dash_end)
            glVertex3f(left, self.lift, dash_end)
            dash_start = dash_end - self.dash_gap
        glEnd()


class ExtendedNeonStreet(NeonStreetScene):

    def __init__(self, seed):
        super().__init__(seed)
        self.back_row_count = 6
        self.first_back_row_z = -146.0
        self.back_row_spacing = 28.0
        self.back_towers_per_side = 5
        self.back_row_heights = (60.0, 100.0)
        self.back_randomness = random.Random(seed + 1)
        self.street_far = -200.0
        self.road_lamps_near = -66.0
        self.road_lamps_far = -200.0
        self.road_lamp_spacing = 12.0
        self.road_lamp_kerb_inset = 1.4
        self.road_buildings_near = -310.0
        self.road_buildings_far = -400.0
        self.road_building_gap = 5.0
        self.road_building_heights = (35.0, 75.0)
        self.centre_line_near = -66.0
        self.centre_line_far = -200.0
        self.centre_line = None
        self.road_side_blocks = []
        self.road_sign_density = 0.5
        self.avenue_join_z = -170.0
        self.road_cars_far = -200.0
        self.avenue_cars_per_direction = 9
        self.road_cars_per_direction = 6
        self.cross_street_cars_per_direction = 8
        self.brand_rules = (BrandRule(11, 0, "COMMODORE", (90, 160, 255)),
                            BrandRule(11, 5, "AMIGA", (255, 70, 90)),
                            BrandRule(22, 7, "ATARI", (255, 150, 40)),
                            BrandRule(22, 3, "ZX SPECTRUM", (110, 255, 140)))
        self.brand_arts = {}
        komoda_amiga = CaptionStyle("K&A+", (60, 240, 230))
        self.road_caption_cycle = (komoda_amiga, CaptionStyle("RetroSfera", (255, 110, 190)),
                                   komoda_amiga, CaptionStyle("NRG", (255, 220, 60)),
                                   komoda_amiga, CaptionStyle("C&A", (210, 255, 240)))
        self.caption_shelf = None
        self.caption_arts = {}
        self.screen_enlargement = 1.75
        self.screen_edge_clearance = 0.3
        self.sign_wall_offset = 0.25
        self.butterfly_screen = None
        self.glow_region = None
        self.square_screen_face = None
        self.square_screen = None
        self.square_screen_tower = 0
        self.ticker_tower = 1
        self.house_door_depth = 0.6

    def _side_row_faces(self):
        toward_square = Vector3(-1.0, 0.0, 0.0)
        faces = []
        for block in self.blocks:
            if block.facing.dot(toward_square) > 0.9 and block.front_start.x > self.avenue[1] + 1.0:
                faces.extend(face for face in (FacadeFace.of_glass_facade(facade) for facade in block.reflectors())
                             if face.normal.dot(toward_square) > 0.9)
        return faces

    def _sign_on_face(self, sign, face):
        bottom_left, bottom_right, _, top_left = sign.corners
        offset = (bottom_left - face.origin).dot(face.normal)
        if abs(offset - self.sign_wall_offset) > 0.05:
            return None
        across = (bottom_left - face.origin).dot(face.right)
        rise = (bottom_left - face.origin).dot(face.up)
        width = (bottom_right - bottom_left).length()
        height = (top_left - bottom_left).length()
        if across < -0.01 or rise < -0.01 or across + width > face.width + 0.01 or rise + height > face.height + 0.01:
            return None
        return across, rise, width, height

    def _enlarged_placement(self, face, across, rise, width, height):
        wide = width * self.screen_enlargement
        tall = height * self.screen_enlargement
        room_across = face.width - 2.0 * self.screen_edge_clearance
        room_up = face.height - 2.0 * self.screen_edge_clearance
        if wide > room_across or tall > room_up:
            return None
        left = min(max(across + width / 2.0 - wide / 2.0, self.screen_edge_clearance),
                   face.width - self.screen_edge_clearance - wide)
        bottom = min(max(rise + height / 2.0 - tall / 2.0, self.screen_edge_clearance),
                     face.height - self.screen_edge_clearance - tall)
        return left, bottom, wide, tall

    def _take_over_screen(self, library):
        screen_arts = library.kinds["screen"]
        best = None
        for face in self._side_row_faces():
            for sign in self.signs.signs:
                if sign.art not in screen_arts:
                    continue
                placement = self._sign_on_face(sign, face)
                enlarged = placement and self._enlarged_placement(face, *placement)
                if enlarged and (best is None or enlarged[2] * enlarged[3] > best[2][2] * best[2][3]):
                    best = (sign, face, enlarged)
        if best is None:
            return None
        sign, face, (left, bottom, wide, tall) = best
        self._remove_signs_under(face, (left, bottom, wide, tall))
        return ButterflyWallScreen(face, left, bottom, wide, tall)

    def _remove_signs_under(self, face, rectangle):
        left, bottom, wide, tall = rectangle
        covered = (left - self.screen_edge_clearance, bottom - self.screen_edge_clearance,
                   left + wide + self.screen_edge_clearance, bottom + tall + self.screen_edge_clearance)
        self.signs.signs = [sign for sign in self.signs.signs if not self._sign_overlaps(sign, face, covered)]

    def _sign_overlaps(self, sign, face, covered):
        if abs((sign.corners[0] - face.origin).dot(face.normal) - self.sign_wall_offset) > 0.05:
            return False
        across = [(corner - face.origin).dot(face.right) for corner in sign.corners]
        rise = [(corner - face.origin).dot(face.up) for corner in sign.corners]
        return (min(across) < covered[2] and covered[0] < max(across)
                and min(rise) < covered[3] and covered[1] < max(rise))

    def _add_extra_art(self, atlas):
        self.brand_arts = VerticalCaptionPainter().store_all(atlas, self.brand_rules)
        self.caption_shelf = CaptionArtShelf()
        self.caption_arts = self.caption_shelf.store(atlas, self.road_caption_cycle)

    def _dress_blocks(self, dresser):
        super()._dress_blocks(dresser)
        road_signs = BrandedSignField(self.signs, self.brand_rules, self.brand_arts, self.road_caption_cycle,
                                      self.caption_arts, self.caption_shelf)
        for block, toward_road in self.road_side_blocks:
            for facade in block.reflectors():
                face = FacadeFace.of_glass_facade(facade)
                if face.normal.dot(toward_road) > 0.9:
                    road_signs.face = face
                    dresser.dress(face, road_signs, self.road_sign_density)
        self.butterfly_screen = self._take_over_screen(dresser.library)
        self.glow_region = dresser.library.glow_region

    def _street_face_of(self, tower):
        return FacadeFace.of_glass_facade(tower.reflectors()[0])

    def _hang_caption(self):
        face = self._street_face_of(self.blocks[1].towers[self.ticker_tower])
        return MatteCaptionScreen(face, self.caption_margin, self.caption_rise, face.width - 2.0 * self.caption_margin,
                                  self.caption_height, self.caption_text, self.caption_color)

    def _hang_square_screen(self):
        self.square_screen_face = self._street_face_of(self.blocks[1].towers[self.square_screen_tower])
        return C64WallScreen(self.square_screen_face, self.caption_margin, self.caption_rise,
                             self.square_screen_face.width - 2.0 * self.caption_margin)

    def _clear_wall_behind_square_screen(self):
        self._remove_signs_under(self.square_screen_face, self.square_screen.covered_rectangle)
        self.signs.seal(self.glow_region)

    def switch_square_screen(self):
        self.square_screen.switch_on()

    def _route_traffic(self):
        traffic = Traffic(self.palette, self.randomness)
        road_length = self.avenue_join_z - self.road_cars_far
        toward_square = RouteLane.turning(Vector3(-5.0, 0.0, self.road_cars_far), Vector3(-5.0, 0.0, self.eastbound_z),
                                          Vector3(160.0, 0.0, self.eastbound_z), self.turn_radius, self.turn_steps)
        self._spread_cars(traffic, toward_square, self.road_cars_per_direction, 0.0, road_length)
        self._spread_cars(traffic, toward_square, self.avenue_cars_per_direction, road_length, toward_square.length)
        from_square = RouteLane.turning(Vector3(160.0, 0.0, self.westbound_z), Vector3(1.0, 0.0, self.westbound_z),
                                        Vector3(1.0, 0.0, self.road_cars_far), self.turn_radius, self.turn_steps)
        avenue_length = from_square.length - road_length
        self._spread_cars(traffic, from_square, self.avenue_cars_per_direction, 0.0, avenue_length)
        self._spread_cars(traffic, from_square, self.road_cars_per_direction, avenue_length, from_square.length)
        traffic.add_lane(Lane(Vector3(-140.0, 0.0, -56.5), Vector3(160.0, 0.0, -56.5)),
                         self.cross_street_cars_per_direction)
        traffic.add_lane(Lane(Vector3(160.0, 0.0, -60.5), Vector3(-140.0, 0.0, -60.5)),
                         self.cross_street_cars_per_direction)
        return traffic

    @staticmethod
    def _spread_cars(traffic, lane, count, first_distance, last_distance):
        spacing = (last_distance - first_distance) / count
        for index in range(count):
            distance = first_distance + index * spacing + traffic.randomness.uniform(0.0, spacing * 0.5)
            traffic.cars.append(Car(traffic.randomness.choice(traffic.models), lane, distance,
                                    traffic.randomness.uniform(*traffic.speed_range)))

    def _place_lamps(self):
        lamps = super()._place_lamps()
        right_kerb = Vector3(self.avenue[1] - self.road_lamp_kerb_inset, 0.0, 0.0)
        left_kerb = Vector3(self.avenue[0] + self.road_lamp_kerb_inset, 0.0, 0.0)
        toward_left = Vector3(-1.0, 0.0, 0.0)
        toward_right = Vector3(1.0, 0.0, 0.0)
        depth = self.road_lamps_near
        on_right = True
        while depth > self.road_lamps_far:
            kerb, arm = (right_kerb, toward_left) if on_right else (left_kerb, toward_right)
            lamps.add(Vector3(kerb.x, 0.0, depth), arm)
            depth -= self.road_lamp_spacing
            on_right = not on_right
        return lamps

    def build(self):
        super().build()
        self.woman = NewspaperWoman(self.woman.position, self.palette, self.woman.shirt_texture,
                                    self.home_front_z + self.house_door_depth)
        self.woman.prepare()
        self.square_screen = self._hang_square_screen()
        self.square_screen.prepare()
        self._clear_wall_behind_square_screen()
        self.street.far = self.street_far
        self.street.prepare()
        self.centre_line = CentreLine(sum(self.avenue) / 2.0, self.centre_line_near, self.centre_line_far)
        self.centre_line.prepare()
        if self.butterfly_screen is not None:
            self.butterfly_screen.prepare()

    def play_butterfly_screen(self, playing):
        if self.butterfly_screen is not None:
            self.butterfly_screen.playing = playing

    def update(self, seconds):
        super().update(seconds)
        self.square_screen.update(seconds)
        if self.butterfly_screen is not None:
            self.butterfly_screen.update(seconds)

    def draw_street_reflections(self):
        self._draw_wet_reflections()
        glPushMatrix()
        glScalef(1.0, -self.reflection_stretch, 1.0)
        self.square_screen.draw()
        if self.butterfly_screen is not None:
            self.butterfly_screen.draw()
        glPopMatrix()

    def draw_street(self):
        self.street.draw()
        self.centre_line.draw()

    def draw(self):
        for block in self.blocks + [self.home]:
            block.draw()
        self.lamps.draw()
        self.traffic.draw()
        self.corner.draw()
        self.balcony.draw()
        self.woman.draw()
        self.signs.draw_signs(self.atlas_texture)
        self.signs.draw_glows(self.atlas_texture)
        self.caption.draw()
        self.square_screen.draw()
        if self.butterfly_screen is not None:
            self.butterfly_screen.draw()
        self.glows.draw(self.atlas_texture, self.camera.right(), self.camera.up())
        self.crowd.draw(self.atlas_texture, self.camera.right())
        self.rain.draw()

    def _lay_out_blocks(self, planner):
        blocks = super()._lay_out_blocks(planner)
        back_planner = BlockPlanner(planner.styles, self.back_randomness)
        for row in range(self.back_row_count):
            front_z = self.first_back_row_z - row * self.back_row_spacing
            blocks.extend(self._avenue_row(back_planner, front_z))
        blocks.extend(self._road_sides(back_planner))
        return blocks

    def _avenue_row(self, planner, front_z):
        along_x = Vector3(1.0, 0.0, 0.0)
        toward_balcony = Vector3(0.0, 0.0, 1.0)
        left_plans = planner.plans(self.back_towers_per_side, self.back_row_heights)
        right_plans = planner.plans(self.back_towers_per_side, self.back_row_heights)
        left_start = Vector3(self.avenue[0] - GlassStreet.length_of(left_plans, self.tower_gap), 0.0, front_z)
        right_start = Vector3(self.avenue[1], 0.0, front_z)
        return [GlassStreet(left_plans, self.tower_gap, left_start, along_x, toward_balcony),
                GlassStreet(right_plans, self.tower_gap, right_start, along_x, toward_balcony)]

    def _road_sides(self, planner):
        road_length = self.road_buildings_near - self.road_buildings_far
        away_from_square = Vector3(0.0, 0.0, -1.0)
        sides = []
        for kerb_x, toward_road in ((self.avenue[0], Vector3(1.0, 0.0, 0.0)), (self.avenue[1], Vector3(-1.0, 0.0, 0.0))):
            plans = planner.plans_within(road_length, self.road_building_gap, self.road_building_heights)
            side = GlassStreet(plans, self.road_building_gap, Vector3(kerb_x, 0.0, self.road_buildings_near),
                               away_from_square, toward_road)
            self.road_side_blocks.append((side, toward_road))
            sides.append(side)
        return sides
