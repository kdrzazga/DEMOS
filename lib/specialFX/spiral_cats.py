from lib.specialFX.cats import CatAnim
from lib.specialFX.spiral import Spiral, SpiralAnim
from lib.specialFX.travelling_surface import TravellingSurface


class SpiralCatsAnim:

    def __init__(self, camera_distance, field_of_view_degrees, aspect_ratio):
        self.cats_start_at_spiral_travel_share = 0.5
        self.cat_size = 1.0
        self.time = 0.0
        spiral = Spiral(center=(0.0, 0.0, 0.0), turn_spacing=1.0, turns=5)
        self.spiral_surface = SpiralAnim(spiral, camera_distance, field_of_view_degrees, aspect_ratio)
        cats_half_size = self.spiral_surface.content_half_size
        cats = CatAnim(area_center=(0.0, 0.0, 0.0), area_width=2.0 * cats_half_size,
                       area_height=2.0 * cats_half_size, cat_size=self.cat_size)
        self.cats_surface = TravellingSurface(cats, cats.area_center, cats_half_size, camera_distance,
                                              field_of_view_degrees, aspect_ratio)
        self.cats_surface.surface_margin = self.spiral_surface.surface_margin
        self.cats_delay = self.cats_start_at_spiral_travel_share * self.spiral_surface.travel_seconds
        self.surfaces = (self.spiral_surface, self.cats_surface)

    def restart(self):
        self.time = 0.0
        for surface in self.surfaces:
            surface.restart()
        self._sync_surfaces()

    def update(self, delta_seconds):
        self.time += delta_seconds
        self._sync_surfaces()

    def is_finished(self):
        return all(surface.is_finished() for surface in self.surfaces)

    def draw(self):
        for surface in sorted(self.surfaces, key=lambda surface: surface.depth()):
            surface.draw()

    def _sync_surfaces(self):
        self.spiral_surface.set_time(self.time)
        self.cats_surface.set_time(self.time - self.cats_delay)
