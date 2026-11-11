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
    glPushAttrib,
    glVertex3f,
)

from lib.urban.glass import GlassStreet
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

    def _dress_blocks(self, dresser):
        super()._dress_blocks(dresser)
        for block, toward_road in self.road_side_blocks:
            for facade in block.reflectors():
                face = FacadeFace.of_glass_facade(facade)
                if face.normal.dot(toward_road) > 0.9:
                    dresser.dress(face, self.signs, self.road_sign_density)

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
        self.street.far = self.street_far
        self.street.prepare()
        self.centre_line = CentreLine(sum(self.avenue) / 2.0, self.centre_line_near, self.centre_line_far)
        self.centre_line.prepare()

    def draw_street_reflections(self):
        self._draw_wet_reflections()

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
