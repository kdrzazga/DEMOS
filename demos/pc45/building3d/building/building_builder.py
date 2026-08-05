from .illumination_scheme import WindowIlluminationScheme
from .ring_building import RingBuilding


class BuildingBuilder:
    def __init__(self):
        self.pillar_availability = False
        self.pillar_placement_angle = 0.9
        self.logo_segment_x = 2
        self.logo_segment_y = 2
        self.lit_window_probability = 0.42
        self.illumination_random_seed = 7

    def with_pillar(self, placement_angle=0.9):
        self.pillar_availability = True
        self.pillar_placement_angle = placement_angle
        return self

    def with_logo(self, segment_x=2, segment_y=2):
        self.logo_segment_x = segment_x
        self.logo_segment_y = segment_y
        return self

    def build(self):
        illumination_scheme = WindowIlluminationScheme(
            lit_probability=self.lit_window_probability,
            random_seed=self.illumination_random_seed)
        return RingBuilding(
            pillar_availability=self.pillar_availability,
            pillar_placement_angle=self.pillar_placement_angle,
            signage_column_offset_from_corner=self.logo_segment_x,
            signage_top_floor_from_top=self.logo_segment_y,
            illumination_scheme=illumination_scheme)
