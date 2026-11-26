import math

import numpy

from lib.animals.dragon import Sculptor, StatueMesh, mottling


class Stool:

    def __init__(self, back_center, floor, yaw, seat_height, seat_width, seat_depth):
        self.back_center = (float(back_center[0]), float(back_center[1]))
        self.floor = float(floor)
        self.yaw = yaw
        self.seat_height = seat_height
        self.seat_width = seat_width
        self.seat_depth = seat_depth
        self.slab_thickness = 0.045
        self.cushion_thickness = 0.04
        self.cushion_inset = 0.025
        self.post_size = 0.05
        self.rear_leg_depth = (0.0, self.post_size)
        self.stretcher_height = 0.09
        self.stretcher_size = 0.025
        self.wood = (0.21, 0.12, 0.07)
        self.dark_wood = (0.11, 0.065, 0.04)
        self.cushion = (0.36, 0.05, 0.07)
        self.iron = (0.17, 0.16, 0.18)
        self.right = numpy.array((math.cos(yaw), 0.0, -math.sin(yaw)))
        self.forward = numpy.array((math.sin(yaw), 0.0, math.cos(yaw)))
        self.origin = numpy.array((self.back_center[0], self.floor, self.back_center[1]))

    def placed(self, points):
        points = numpy.asarray(points, dtype=numpy.float64)
        return (self.origin + points[..., 0:1] * self.right + points[..., 1:2] * numpy.array((0.0, 1.0, 0.0))
                + points[..., 2:3] * self.forward)

    def turned(self, vectors):
        vectors = numpy.asarray(vectors, dtype=numpy.float64)
        return (vectors[..., 0:1] * self.right + vectors[..., 1:2] * numpy.array((0.0, 1.0, 0.0))
                + vectors[..., 2:3] * self.forward)

    def box(self, mesh, low, high, color):
        (left, bottom, back), (right, top, front) = low, high
        faces = (((left, bottom, front), (right, bottom, front), (right, top, front), (left, top, front), (0, 0, 1)),
                 ((right, bottom, back), (left, bottom, back), (left, top, back), (right, top, back), (0, 0, -1)),
                 ((right, bottom, front), (right, bottom, back), (right, top, back), (right, top, front), (1, 0, 0)),
                 ((left, bottom, back), (left, bottom, front), (left, top, front), (left, top, back), (-1, 0, 0)),
                 ((left, top, front), (right, top, front), (right, top, back), (left, top, back), (0, 1, 0)),
                 ((left, bottom, back), (right, bottom, back), (right, bottom, front), (left, bottom, front),
                  (0, -1, 0)))
        for *corners, normal in faces:
            corners = self.placed(corners)
            shade = numpy.asarray(color) * mottling(corners * 6.0, 0.12)[:, None]
            mesh.add_quad(corners, numpy.broadcast_to(self.turned(normal), (4, 3)), shade)

    def slab_top(self):
        return self.seat_height - self.cushion_thickness

    def slab_bottom(self):
        return self.slab_top() - self.slab_thickness

    def rear_leg_top(self):
        return self.slab_bottom()

    def rear_leg(self, mesh, side, left, right):
        back, front = self.rear_leg_depth
        self.box(mesh, (left, 0.0, back), (right, self.rear_leg_top(), front), self.wood)

    def build(self, mesh):
        half_width = self.seat_width / 2.0
        post = self.post_size
        slab_top, slab_bottom = self.slab_top(), self.slab_bottom()
        self.box(mesh, (-half_width, slab_bottom, 0.0), (half_width, slab_top, self.seat_depth), self.wood)
        inset = self.cushion_inset
        self.box(mesh, (-half_width + inset, slab_top, inset), (half_width - inset, self.seat_height,
                                                               self.seat_depth - inset), self.cushion)
        stretcher_top = self.stretcher_height + self.stretcher_size
        for side in (1.0, -1.0):
            outer = side * half_width
            inner = outer - side * post
            left, right = min(outer, inner), max(outer, inner)
            self.box(mesh, (left, 0.0, self.seat_depth - post), (right, slab_bottom, self.seat_depth), self.wood)
            self.rear_leg(mesh, side, left, right)
            self.box(mesh, (left, self.stretcher_height, self.rear_leg_depth[1]),
                     (right, stretcher_top, self.seat_depth - post), self.dark_wood)
        self.box(mesh, (-half_width + post, self.stretcher_height, self.seat_depth - post),
                 (half_width - post, stretcher_top, self.seat_depth), self.dark_wood)


class Chair(Stool):

    def __init__(self, back_center, floor, yaw, seat_height, seat_width, seat_depth):
        super().__init__(back_center, floor, yaw, seat_height, seat_width, seat_depth)
        self.rear_leg_depth = (-self.post_size, 0.0)
        self.back_height = 1.0
        self.arch_height = 0.24
        self.panel_thickness = 0.03
        self.finial_height = 0.13

    def rear_leg_top(self):
        return self.seat_height + self.back_height

    def rear_leg(self, mesh, side, left, right):
        super().rear_leg(mesh, side, left, right)
        post = self.post_size
        tip = self.placed((side * (self.seat_width / 2.0 - post / 2.0), self.rear_leg_top(), -post / 2.0))
        Sculptor(mesh).spike(tip, (0.0, 1.0, 0.0), self.finial_height, post * 0.55, self.iron)

    def back_panel(self, mesh, half_width, bottom, top):
        rows, columns = 16, 21
        across = numpy.linspace(-half_width, half_width, columns)[None, :]
        peak = top + self.arch_height * (1.0 - numpy.abs(across) / half_width) ** 0.75
        rise = numpy.linspace(0.0, 1.0, rows)[:, None]
        heights = bottom + (peak - bottom) * rise
        frame = numpy.minimum(numpy.minimum(half_width - numpy.abs(across), heights - bottom), peak - heights)
        carving = 0.55 + 0.45 * numpy.clip(frame / 0.05, 0.0, 1.0) * (
                0.8 + 0.2 * numpy.abs(numpy.sin(across * 40.0) * numpy.sin(heights * 25.0)))
        dark, light = numpy.asarray(self.dark_wood), numpy.asarray(self.wood)
        for depth, facing in ((-0.002, 1.0), (-self.panel_thickness, -1.0)):
            local = numpy.stack((numpy.broadcast_to(across, heights.shape), heights,
                                 numpy.full(heights.shape, depth)), axis=-1)
            grid = self.placed(local)
            colors = (dark + (light - dark) * carving[..., None]) * mottling(grid * 5.0, 0.1)[..., None]
            mesh.add_grid(grid, numpy.broadcast_to(self.turned((0.0, 0.0, facing)), grid.shape), colors)

    def build(self, mesh):
        super().build(mesh)
        self.back_panel(mesh, self.seat_width / 2.0 - self.post_size, self.slab_top(), self.rear_leg_top() - 0.05)


def build_chairs(chairs):
    mesh = StatueMesh()
    for chair in chairs:
        chair.build(mesh)
    return mesh.arrays()
