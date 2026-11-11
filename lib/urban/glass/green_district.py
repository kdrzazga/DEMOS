import math

from lib.urban.glass.glass_street import GlassStreet, TowerPlan
from lib.urban.glass.glass_tower import TowerTier
from lib.urban.glass.night_lights import GreenFloodLight, GreenLight
from lib.urban.glass.night_scene import GlassPalette, NightGround, NightScene, OrbitCamera
from lib.vector3 import Vector3


class GreenGlassPalette(GlassPalette):

    def __init__(self):
        self.standard_tint = (0.45, 0.95, 0.6)
        self.greener_tint = (0.38, 1.0, 0.48)
        self.darker_tint = (0.32, 0.78, 0.48)
        self.lit_pane_tint = (0.62, 0.95, 0.72)
        self.lit_pane_glow = (0.25, 0.55, 0.32, 1.0)
        self.slab_color = (0.2, 0.42, 0.26)
        self.spire_color = (0.3, 0.6, 0.36)

    def standard(self):
        return self._greened(super().standard(), self.standard_tint)

    def greener(self):
        return self._greened(super().greener(), self.greener_tint)

    def darker(self):
        return self._greened(super().darker(), self.darker_tint)

    def _greened(self, style, pane_tint):
        style.pane_tint = pane_tint
        style.lit_pane_tint = self.lit_pane_tint
        style.lit_pane_glow = self.lit_pane_glow
        style.slab_color = self.slab_color
        style.spire_color = self.spire_color
        return style


class GreenDistrict:

    def __init__(self):
        self.palette = GreenGlassPalette()
        self.origin = Vector3(0.0, 0.0, 0.0)
        self.facing = Vector3(0.0, 0.0, 1.0)
        self.ground_half_extent = 120.0
        self.tower_gap = 1.2

    def _place(self, across, height, ahead):
        right = Vector3(0.0, 1.0, 0.0).cross(self.facing)
        return self.origin + right * across + Vector3(0.0, height, 0.0) + self.facing * ahead

    def build(self):
        plans = [
            TowerPlan([TowerTier(7.0, 9.0, 20.0)], self.palette.standard(), seed=3),
            TowerPlan([TowerTier(9.0, 10.0, 28.0), TowerTier(6.5, 7.0, 8.0)], self.palette.greener(), seed=8),
            TowerPlan([TowerTier(6.0, 8.0, 16.0)], self.palette.darker(), seed=11),
            TowerPlan([TowerTier(10.0, 11.0, 34.0), TowerTier(7.0, 8.0, 10.0), TowerTier(4.0, 4.0, 5.0)],
                      self.palette.standard(), seed=5),
            TowerPlan([TowerTier(8.0, 9.0, 24.0)], self.palette.greener(), seed=13),
            TowerPlan([TowerTier(7.5, 9.0, 30.0), TowerTier(5.0, 6.0, 6.0)], self.palette.darker(), seed=21),
        ]
        right = Vector3(0.0, 1.0, 0.0).cross(self.facing)
        front_start = self._place(-GlassStreet.length_of(plans, self.tower_gap) / 2.0, 0.0, 0.0)
        street = GlassStreet(plans, self.tower_gap, front_start, right, self.facing)
        camera = OrbitCamera(self._place(0.0, 18.0, -4.0), 64.0, 4.0, 30.0)
        ground = NightGround(self.ground_half_extent)
        ground.center = self.origin
        scene = NightScene("Green District", [street], ground, camera, fog_density=0.009)
        scene.flood_frontages(street.frontages, GreenFloodLight)
        scene.add_orb(GreenLight(self._place(0.0, 5.0, -4.0), 34.0, 0.3, 0.0, 2.0, 0.6))
        scene.add_orb(GreenLight(self._place(0.0, 20.0, -4.0), 31.0, -0.22, math.pi, 10.0, 0.25))
        return scene
