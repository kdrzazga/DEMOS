import random

from lib.urban.glass import GlassStreet
from lib.urban.neon.neon_street import BlockPlanner, NeonStreetScene
from lib.vector3 import Vector3


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

    def build(self):
        super().build()
        self.street.far = self.street_far
        self.street.prepare()

    def draw_street_reflections(self):
        self._draw_wet_reflections()

    def draw_street(self):
        self.street.draw()

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
