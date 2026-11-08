from lib.urban.glass.glass_tower import GlassSkyscraper
from lib.vector3 import Vector3


class TowerPlan:

    def __init__(self, tiers, style, seed):
        self.tiers = tiers
        self.style = style
        self.seed = seed

    @property
    def width(self):
        return self.tiers[0].width

    @property
    def depth(self):
        return self.tiers[0].depth

    @property
    def height(self):
        return sum(tier.height for tier in self.tiers)


class GlassStreet:

    def __init__(self, plans, gap, front_line):
        self.plans = plans
        self.gap = gap
        self.front_line = front_line
        self.towers = []
        self.front_centers = []
        self._line_up()

    def _line_up(self):
        cursor = -self.length / 2.0
        for plan in self.plans:
            center_x = cursor + plan.width / 2.0
            center_z = self.front_line - plan.depth / 2.0
            self.towers.append(GlassSkyscraper(center_x, center_z, plan.tiers, plan.style, plan.seed))
            self.front_centers.append(Vector3(center_x, plan.height / 2.0, self.front_line))
            cursor += plan.width + self.gap

    @property
    def length(self):
        return sum(plan.width for plan in self.plans) + self.gap * (len(self.plans) - 1)

    @property
    def tallest(self):
        return max(plan.height for plan in self.plans)

    def reflectors(self):
        return [facade for tower in self.towers for facade in tower.reflectors()]

    def set_blur(self, blur):
        for tower in self.towers:
            tower.set_blur(blur)

    @property
    def blur(self):
        return self.towers[0].blur

    def update(self, seconds):
        for tower in self.towers:
            tower.update(seconds)

    def draw(self):
        for tower in self.towers:
            tower.draw()
