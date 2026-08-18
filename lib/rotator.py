import math
from collections import namedtuple
from enum import Enum, auto


Point = namedtuple("Point", ["x", "y", "z"])
Corners = namedtuple("Corners", ["top_left", "top_right", "bottom_right", "bottom_left"])


class Edge(Enum):
    LEFT = auto()
    RIGHT = auto()
    TOP = auto()
    BOTTOM = auto()


class Rotation:

    def __init__(self, surface, total_duration, fps, half_width=1.0):
        self.surface = surface
        self.total_duration = total_duration
        self.fps = fps
        self.half_width = half_width
        self.half_height = half_width * surface.get_height() / surface.get_width()
        self.elapsed_frames = 0

    def get_surface_vertices(self):
        return Corners(
            top_left=Point(-self.half_width, self.half_height, 0.0),
            top_right=Point(self.half_width, self.half_height, 0.0),
            bottom_right=Point(self.half_width, -self.half_height, 0.0),
            bottom_left=Point(-self.half_width, -self.half_height, 0.0),
        )

    def rotate(self):
        self.elapsed_frames += 1
        return self.current_vertices()

    def current_vertices(self):
        raise NotImplementedError

    def reset(self):
        self.elapsed_frames = 0

    @property
    def finished(self):
        return self.progress >= 1.0

    @property
    def progress(self):
        return min(1.0, self.elapsed_frames / (self.fps * self.total_duration))


class Rotator(Rotation):

    def __init__(self, surface, destination_top_left, destination_top_right,
                 destination_bottom_left, destination_bottom_right,
                 total_duration, fps, half_width=1.0):
        super().__init__(surface, total_duration, fps, half_width)
        self.destination = Corners(
            top_left=Point(*destination_top_left),
            top_right=Point(*destination_top_right),
            bottom_right=Point(*destination_bottom_right),
            bottom_left=Point(*destination_bottom_left),
        )

    def current_vertices(self):
        progress = self.progress
        return Corners(*[
            self._interpolate_point(start, end, progress)
            for start, end in zip(self.get_surface_vertices(), self.destination)
        ])

    def _interpolate_point(self, start, end, progress):
        return Point(
            start.x + (end.x - start.x) * progress,
            start.y + (end.y - start.y) * progress,
            start.z + (end.z - start.z) * progress,
        )


class AngleRotator(Rotation):

    def __init__(self, surface, still_edge, total_angle, total_duration, fps, half_width=1.0):
        super().__init__(surface, total_duration, fps, half_width)
        self.still_edge = still_edge
        self.total_angle = total_angle

    def current_vertices(self):
        angle = math.radians(self.total_angle * self.progress)
        return Corners(*[
            self._rotate_point(vertex, angle)
            for vertex in self.get_surface_vertices()
        ])

    def _rotate_point(self, vertex, angle):
        if self.still_edge in (Edge.LEFT, Edge.RIGHT):
            return self._rotate_about_vertical_edge(vertex, angle)
        return self._rotate_about_horizontal_edge(vertex, angle)

    def _rotate_about_vertical_edge(self, vertex, angle):
        if self.still_edge is Edge.LEFT:
            distance_from_edge = vertex.x + self.half_width
            rotated_x = -self.half_width + distance_from_edge * math.cos(angle)
        else:
            distance_from_edge = self.half_width - vertex.x
            rotated_x = self.half_width - distance_from_edge * math.cos(angle)
        return Point(rotated_x, vertex.y, -distance_from_edge * math.sin(angle))

    def _rotate_about_horizontal_edge(self, vertex, angle):
        if self.still_edge is Edge.TOP:
            distance_from_edge = self.half_height - vertex.y
            rotated_y = self.half_height - distance_from_edge * math.cos(angle)
        else:
            distance_from_edge = vertex.y + self.half_height
            rotated_y = -self.half_height + distance_from_edge * math.cos(angle)
        return Point(vertex.x, rotated_y, -distance_from_edge * math.sin(angle))
