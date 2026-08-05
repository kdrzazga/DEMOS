import math

from OpenGL.GL import GL_MODELVIEW, glLoadIdentity, glMatrixMode
from OpenGL.GLU import gluLookAt

from .linear_algebra import Vector3, clamp_value


class OrbitCamera:
    def __init__(self, target_point, distance, azimuth=0.7, elevation=0.28,
                 minimum_distance=14.0, maximum_distance=170.0,
                 minimum_elevation=-0.15, maximum_elevation=1.35,
                 automatic_rotation_speed=0.25):
        self.target_point = target_point
        self.distance = distance
        self.azimuth = azimuth
        self.elevation = elevation
        self.minimum_distance = minimum_distance
        self.maximum_distance = maximum_distance
        self.minimum_elevation = minimum_elevation
        self.maximum_elevation = maximum_elevation
        self.automatic_rotation_speed = automatic_rotation_speed

    def orbit_by(self, azimuth_delta, elevation_delta):
        self.azimuth += azimuth_delta
        self.elevation = clamp_value(
            self.elevation + elevation_delta, self.minimum_elevation, self.maximum_elevation)

    def zoom_by(self, distance_delta):
        self.distance = clamp_value(
            self.distance + distance_delta, self.minimum_distance, self.maximum_distance)

    def advance_automatic_rotation(self, elapsed_seconds):
        self.azimuth += self.automatic_rotation_speed * elapsed_seconds

    def compute_eye_position(self):
        horizontal_radius = self.distance * math.cos(self.elevation)
        return Vector3(
            self.target_point.x + horizontal_radius * math.sin(self.azimuth),
            self.target_point.y + self.distance * math.sin(self.elevation),
            self.target_point.z + horizontal_radius * math.cos(self.azimuth))

    def apply_view_transform(self):
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        eye = self.compute_eye_position()
        gluLookAt(eye.x, eye.y, eye.z,
                  self.target_point.x, self.target_point.y, self.target_point.z,
                  0.0, 1.0, 0.0)
