import math


class HipRoof:
    def __init__(self, x0, z0, x1, z1, base, rise, color, texture=None, ridge_color=None,
                 tile_width=0.5, tile_height=0.42):
        self.x0 = x0
        self.z0 = z0
        self.x1 = x1
        self.z1 = z1
        self.base = base
        self.rise = rise
        self.color = color
        self.texture = texture
        self.ridge_color = ridge_color
        self.tile_width = tile_width
        self.tile_height = tile_height
        self.half = min(x1 - x0, z1 - z0) / 2.0
        self.pitch = rise / self.half
        self.top = base + rise

    def height_at(self, x, z):
        inset = min(x - self.x0, self.x1 - x, z - self.z0, self.z1 - z)
        return self.base + min(self.rise, max(0.0, inset) * self.pitch)

    def ridge(self):
        if self.x1 - self.x0 >= self.z1 - self.z0:
            middle = (self.z0 + self.z1) / 2.0
            return (self.x0 + self.half, self.top, middle), (self.x1 - self.half, self.top, middle)
        middle = (self.x0 + self.x1) / 2.0
        return (middle, self.top, self.z0 + self.half), (middle, self.top, self.z1 - self.half)

    def faces(self):
        back_west = (self.x0, self.base, self.z0)
        back_east = (self.x1, self.base, self.z0)
        front_east = (self.x1, self.base, self.z1)
        front_west = (self.x0, self.base, self.z1)
        first, second = self.ridge()
        if self.x1 - self.x0 >= self.z1 - self.z0:
            return ((front_west, front_east, second, first),
                    (back_east, back_west, first, second),
                    (back_west, front_west, first),
                    (front_east, back_east, second))
        return ((front_east, back_east, first, second),
                (back_west, front_west, second, first),
                (front_west, front_east, second),
                (back_east, back_west, first))

    def draw(self, shapes):
        sine = self.rise / math.hypot(self.rise, self.half)
        with shapes.textured(self.texture):
            for face in self.faces():
                start, end = face[0], face[1]
                along_x, along_z = end[0] - start[0], end[2] - start[2]
                length = math.hypot(along_x, along_z)
                along_x, along_z = along_x / length, along_z / length
                uvs = [(((point[0] - start[0]) * along_x + (point[2] - start[2]) * along_z) / self.tile_width,
                        (point[1] - self.base) / sine / self.tile_height) for point in face]
                shapes.polygon(face, self.color, shapes.upward_normal(face), uvs)
        if self.ridge_color:
            self._draw_ridges(shapes)

    def _draw_ridges(self, shapes):
        first, second = self.ridge()
        shapes.beam(first, second, 0.3, self.ridge_color)
        lift = 0.06
        corners = (((self.x0, self.base + lift, self.z0), first), ((self.x0, self.base + lift, self.z1), first),
                   ((self.x1, self.base + lift, self.z0), second), ((self.x1, self.base + lift, self.z1), second))
        if self.x1 - self.x0 < self.z1 - self.z0:
            corners = (((self.x0, self.base + lift, self.z0), first), ((self.x1, self.base + lift, self.z0), first),
                       ((self.x0, self.base + lift, self.z1), second), ((self.x1, self.base + lift, self.z1), second))
        for corner, ridge_end in corners:
            shapes.beam(corner, ridge_end, 0.22, self.ridge_color)
