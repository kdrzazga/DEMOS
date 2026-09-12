from OpenGL.GL import *


class Town:
    def __init__(self, x, y, z, quarters=(), roads=()):
        self.x = x
        self.y = y
        self.z = z
        self.quarters = tuple(quarters)
        self.roads = tuple(roads)
        self.width, self.depth = self._footprint()

    def _footprint(self):
        if not self.quarters:
            return 0.0, 0.0
        left = min(quarter.x - quarter.width / 2.0 for quarter in self.quarters)
        right = max(quarter.x + quarter.width / 2.0 for quarter in self.quarters)
        near = min(quarter.z - quarter.depth / 2.0 for quarter in self.quarters)
        far = max(quarter.z + quarter.depth / 2.0 for quarter in self.quarters)
        return right - left, far - near

    def tallest(self):
        return max((quarter.tallest() for quarter in self.quarters), default=0.0)

    def house_count(self):
        return sum(len(quarter.houses) for quarter in self.quarters)

    def draw(self):
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        for road in self.roads:
            road.draw()
        for quarter in self.quarters:
            quarter.draw()
        glPopMatrix()
