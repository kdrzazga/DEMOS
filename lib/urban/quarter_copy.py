from OpenGL.GL import *


class QuarterCopy:
    def __init__(self, prototype, x=0.0, y=0.0, z=0.0, facing=0.0):
        self.prototype = prototype
        self.x = x
        self.y = y
        self.z = z
        self.facing = facing
        self.width = prototype.width
        self.depth = prototype.depth
        self.density = prototype.density
        self.houses = prototype.houses

    def plot_count(self):
        return self.prototype.plot_count()

    def tallest(self):
        return self.prototype.tallest()

    def draw(self):
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        glRotatef(self.facing, 0.0, 1.0, 0.0)
        for house in self.houses:
            house.draw()
        glPopMatrix()
