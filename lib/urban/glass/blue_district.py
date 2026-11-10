import math
import random

from lib.urban.glass.glass_street import GlassStreet, TowerPlan
from lib.urban.glass.glass_tower import TowerTier
from lib.urban.glass.night_lights import BlueLight, FloodLight
from lib.urban.glass.night_scene import GlassPalette, NightGround, NightScene, OrbitCamera
from lib.vector3 import Vector3


class CityLine:

    def __init__(self, towers_per_side, front_line, height_range):
        self.towers_per_side = towers_per_side
        self.front_line = front_line
        self.height_range = height_range


class BlueDistrict:

    def __init__(self):
        self.palette = GlassPalette()
        self.avenue_width = 16.0
        self.side_road_width = 14.0
        self.side_line_towers = 4
        self.side_line_floods = 2
        self.line_flood_counts = (3, 1, 1)
        self.side_line_heights = (20.0, 40.0)
        self.lines = (CityLine(6, 0.0, (16.0, 34.0)),
                      CityLine(3, -30.0, (26.0, 46.0)),
                      CityLine(1, -60.0, (40.0, 60.0)))
        self.gap = 1.2
        self.width_range = (6.0, 10.0)
        self.depth_range = (8.0, 12.0)
        self.setback_height_range = (5.0, 12.0)
        self.setback_shrink = 0.72
        self.most_setbacks = 2
        self.orb_margin = 12.0
        self.camera_margin = 50.0
        self.randomness = random.Random(2026)
        self.planned = 0

    def build(self):
        streets = []
        for line in self.lines:
            streets.extend(self._split_line(line))
        streets.append(self._side_line(streets[0]))
        towers = [tower for street in streets for tower in street.towers]
        center = self._center_of(towers)
        reach = max(math.hypot(tower.x - center.x, tower.z - center.z) for tower in towers) + self.orb_margin
        camera = OrbitCamera(Vector3(center.x, 22.0, center.z), reach + self.camera_margin, 10.0, 60.0)
        camera.orbit_speed = 0.05
        scene = NightScene("Blue District", streets, NightGround(220.0), camera, fog_density=0.0045)
        scene.flood_frontages(self._lit_frontages(streets), FloodLight)
        scene.add_orb(BlueLight(Vector3(center.x, 8.0, center.z), reach, 0.18, 0.0, 4.0, 0.5))
        scene.add_orb(BlueLight(Vector3(center.x, 34.0, center.z), reach - 4.0, -0.12, math.pi, 12.0, 0.2))
        return scene

    def _lit_frontages(self, streets):
        line_streets = [streets[index:index + 2] for index in range(0, 2 * len(self.lines), 2)]
        side_street = streets[-1]
        chosen = []
        for halves, flood_count in zip(line_streets, self.line_flood_counts):
            line_frontages = [frontage for half in halves for frontage in half.frontages]
            chosen.extend(self._spread(line_frontages, flood_count, lambda frontage: frontage.center.x))
        chosen.extend(self._spread(side_street.frontages, self.side_line_floods, lambda frontage: frontage.center.z))
        return chosen

    def _spread(self, frontages, count, position_of):
        if count == 1:
            return [max(frontages, key=lambda frontage: frontage.height)]
        first = min(position_of(frontage) for frontage in frontages)
        last = max(position_of(frontage) for frontage in frontages)
        remaining = list(frontages)
        chosen = []
        for slot in range(count):
            target = first + (last - first) * (slot + 0.5) / count
            nearest = min(remaining, key=lambda frontage: abs(position_of(frontage) - target))
            remaining.remove(nearest)
            chosen.append(nearest)
        return chosen

    def _center_of(self, towers):
        xs = [tower.x for tower in towers]
        zs = [tower.z for tower in towers]
        return Vector3((min(xs) + max(xs)) / 2.0, 0.0, (min(zs) + max(zs)) / 2.0)

    def _split_line(self, line):
        along = Vector3(1.0, 0.0, 0.0)
        facing = Vector3(0.0, 0.0, 1.0)
        half_avenue = self.avenue_width / 2.0
        left_plans = self._plans(line.towers_per_side, line.height_range)
        right_plans = self._plans(line.towers_per_side, line.height_range)
        left_start = Vector3(-half_avenue - GlassStreet.length_of(left_plans, self.gap), 0.0, line.front_line)
        right_start = Vector3(half_avenue, 0.0, line.front_line)
        return [GlassStreet(left_plans, self.gap, left_start, along, facing),
                GlassStreet(right_plans, self.gap, right_start, along, facing)]

    def _side_line(self, first_line_left):
        front_x = first_line_left.front_start.x - self.side_road_width
        plans = self._plans(self.side_line_towers, self.side_line_heights)
        start = Vector3(front_x, 0.0, first_line_left.front_start.z + GlassStreet.length_of(plans, self.gap))
        return GlassStreet(plans, self.gap, start, Vector3(0.0, 0.0, -1.0), Vector3(1.0, 0.0, 0.0))

    def _plans(self, count, height_range):
        return [self._plan(height_range) for _ in range(count)]

    def _plan(self, height_range):
        width = round(self.randomness.uniform(*self.width_range) * 2.0) / 2.0
        depth = round(self.randomness.uniform(*self.depth_range) * 2.0) / 2.0
        tiers = [TowerTier(width, depth, round(self.randomness.uniform(*height_range)))]
        for _ in range(self.randomness.randint(0, self.most_setbacks)):
            previous = tiers[-1]
            tiers.append(TowerTier(previous.width * self.setback_shrink, previous.depth * self.setback_shrink,
                                   round(self.randomness.uniform(*self.setback_height_range))))
        style = self.randomness.choice(self.palette.all_styles())
        self.planned += 1
        return TowerPlan(tiers, style, seed=self.planned)
