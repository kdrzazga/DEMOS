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


class Frontage:

    def __init__(self, center, facing):
        self.center = center
        self.facing = facing

    @property
    def height(self):
        return self.center.y


class GlassStreet:

    def __init__(self, plans, gap, front_start, along, facing):
        self.plans = plans
        self.gap = gap
        self.front_start = front_start
        self.along = along
        self.facing = facing
        self.runs_along_depth = abs(along.z) > abs(along.x)
        self.towers = []
        self.frontages = []
        self._line_up()

    @staticmethod
    def length_of(plans, gap):
        return sum(plan.width for plan in plans) + gap * (len(plans) - 1)

    @staticmethod
    def centered(plans, gap, front_line):
        start = Vector3(-GlassStreet.length_of(plans, gap) / 2.0, 0.0, front_line)
        return GlassStreet(plans, gap, start, Vector3(1.0, 0.0, 0.0), Vector3(0.0, 0.0, 1.0))

    def _line_up(self):
        cursor = 0.0
        for plan in self.plans:
            front_center = self.front_start + self.along * (cursor + plan.width / 2.0)
            center = front_center - self.facing * (plan.depth / 2.0)
            tiers = [tier.turned() for tier in plan.tiers] if self.runs_along_depth else plan.tiers
            self.towers.append(GlassSkyscraper(center.x, center.z, tiers, plan.style, plan.seed))
            self.frontages.append(Frontage(Vector3(front_center.x, plan.height / 2.0, front_center.z), self.facing))
            cursor += plan.width + self.gap

    @property
    def length(self):
        return GlassStreet.length_of(self.plans, self.gap)

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

    def prepare(self):
        for tower in self.towers:
            tower.prepare()

    def draw(self):
        for tower in self.towers:
            tower.draw()
