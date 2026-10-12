from OpenGL.GL import *

from lib.pixelove_ole.geometry import mix, shade
from lib.pixelove_ole.part import LogoPart


class NeonFloor(LogoPart):
    """Synthwave checkerboard plane the logo stands on, with neon grid lines
    that fade towards the far edge.

    `opacity` fades the whole floor without recompiling: the display list
    blends with the GL constant alpha, which draw() sets from `opacity`.
    `fade_to()` + `update()` animate it."""

    def __init__(self, x=0.0, y=-2.6, z=0.8, half_width=6.0, near_depth=4.0, far_depth=3.2, tile_size=0.5):
        super().__init__("floor", x, y, z)
        self.half_width = half_width
        self.near_depth = near_depth
        self.far_depth = far_depth
        self.tile_size = tile_size
        self.dark_tile = (0.03, 0.0, 0.07)
        self.light_tile = (0.1, 0.02, 0.18)
        self.near_line = (1.0, 0.2, 0.85)
        self.far_line = (0.35, 0.15, 0.9)
        self.opacity = 1.0
        self.target_opacity = 1.0
        self.fade_speed = 1.0

    def fade_to(self, opacity, duration=1.5):
        self.target_opacity = opacity
        self.fade_speed = abs(opacity - self.opacity) / duration if duration > 0 else float("inf")
        if opacity > 0.0:
            self.visible = True

    def update(self, delta_seconds):
        step = self.fade_speed * delta_seconds
        if self.opacity < self.target_opacity:
            self.opacity = min(self.target_opacity, self.opacity + step)
        else:
            self.opacity = max(self.target_opacity, self.opacity - step)
        self.visible = self.opacity > 0.0

    def line_color(self, z):
        distance = (self.near_depth - z) / (self.near_depth + self.far_depth)
        return shade(mix(self.near_line, self.far_line, distance), 1.0 - 0.6 * distance)

    def tile_edges(self, start, end):
        edges = []
        value = start
        while value <= end + 1e-6:
            edges.append(value)
            value += self.tile_size
        return edges

    def build(self):
        xs = self.tile_edges(-self.half_width, self.half_width)
        zs = self.tile_edges(-self.far_depth, self.near_depth)

        glEnable(GL_BLEND)
        glDepthMask(GL_FALSE)
        glBlendFunc(GL_CONSTANT_ALPHA, GL_ONE_MINUS_CONSTANT_ALPHA)
        glBegin(GL_QUADS)
        for column, (x0, x1) in enumerate(zip(xs, xs[1:])):
            for row, (z0, z1) in enumerate(zip(zs, zs[1:])):
                glColor3f(*(self.light_tile if (column + row) % 2 else self.dark_tile))
                glVertex3f(x0, 0.0, z1)
                glVertex3f(x1, 0.0, z1)
                glVertex3f(x1, 0.0, z0)
                glVertex3f(x0, 0.0, z0)
        glEnd()

        # Additive lines scaled by the constant alpha; the far-edge fade is
        # premultiplied into the colour since vertex alpha is not used here.
        glBlendFunc(GL_CONSTANT_ALPHA, GL_ONE)
        lift = 0.004
        for width, strength in ((2.0, 1.0), (7.0, 0.25)):
            glLineWidth(width)
            glBegin(GL_LINES)
            for x in xs:
                glColor3f(0.0, 0.0, 0.0)
                glVertex3f(x, lift, zs[0])
                glColor3f(*shade(self.line_color(zs[-1]), strength))
                glVertex3f(x, lift, zs[-1])
            for z in zs:
                fade = strength * (z - zs[0]) / (zs[-1] - zs[0]) if zs[-1] != zs[0] else strength
                glColor3f(*shade(self.line_color(z), fade))
                glVertex3f(xs[0], lift, z)
                glVertex3f(xs[-1], lift, z)
            glEnd()
        glDepthMask(GL_TRUE)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glDisable(GL_BLEND)

    def draw(self):
        glBlendColor(0.0, 0.0, 0.0, self.opacity)
        super().draw()
        glBlendColor(0.0, 0.0, 0.0, 0.0)
