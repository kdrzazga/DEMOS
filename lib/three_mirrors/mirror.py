from OpenGL.GL import (
    GL_BLEND,
    GL_LINE_LOOP,
    GL_ONE_MINUS_SRC_ALPHA,
    GL_QUADS,
    GL_SRC_ALPHA,
    glBegin,
    glBlendFunc,
    glColor3f,
    glColor4f,
    glDisable,
    glEnable,
    glEnd,
    glLineWidth,
    glNormal3f,
    glVertex3f,
)

from lib.vector3 import Vector3


class Mirror:

    def __init__(self, corner, first_edge, second_edge):
        self.corner = corner
        self.first_edge = first_edge
        self.second_edge = second_edge
        self.normal = first_edge.cross(second_edge).normalized()
        self.distance_from_origin = self.normal.dot(corner)
        self.shades = {
            "clear": (0.55, 0.68, 0.85, 0.22),
            "cyan": (0.0, 0.85, 0.9, 0.3),
            "yellow": (0.95, 0.85, 0.1, 0.3),
            "red": (0.9, 0.1, 0.1, 0.3),
            "pink": (1.0, 0.5, 0.75, 0.3),
            "light blue": (0.5, 0.75, 1.0, 0.3),
            "purple": (0.55, 0.15, 0.8, 0.3),
            "light green": (0.55, 0.95, 0.5, 0.3),
        }
        self.glass_tint = self.shades["clear"]
        self.blur = 0.0
        self.sharpest_blur = 0.0
        self.strongest_blur = 1.0
        self.strongest_blur_pixels = 14.0
        self.frame_color = (0.75, 0.8, 0.9)
        self.frame_width = 2.0
        self.clip_tolerance = 0.002

    def shade_names(self):
        return tuple(self.shades)

    def apply_shade(self, name):
        self.glass_tint = self.shades[name]

    def apply_custom_shade(self, red, green, blue, opacity):
        self.glass_tint = (red, green, blue, opacity)

    def set_blur(self, blur):
        self.blur = round(min(max(blur, self.sharpest_blur), self.strongest_blur), 2)

    def is_blurred(self):
        return self.blur > self.sharpest_blur

    def blur_radius_pixels(self):
        return self.blur * self.strongest_blur_pixels

    def corners(self):
        return (self.corner,
                self.corner + self.first_edge,
                self.corner + self.first_edge + self.second_edge,
                self.corner + self.second_edge)

    def signed_distance(self, point):
        return self.normal.dot(point) - self.distance_from_origin

    def faces(self, point):
        return self.signed_distance(point) > 0.0

    def reflect_point(self, point):
        return point - self.normal * (2.0 * self.signed_distance(point))

    def reflection_matrix(self):
        nx, ny, nz = self.normal
        shift = 2.0 * self.distance_from_origin
        return (1.0 - 2.0 * nx * nx, -2.0 * ny * nx, -2.0 * nz * nx, 0.0,
                -2.0 * nx * ny, 1.0 - 2.0 * ny * ny, -2.0 * nz * ny, 0.0,
                -2.0 * nx * nz, -2.0 * ny * nz, 1.0 - 2.0 * nz * nz, 0.0,
                shift * nx, shift * ny, shift * nz, 1.0)

    def behind_clip_plane(self):
        nx, ny, nz = self.normal
        return -nx, -ny, -nz, self.distance_from_origin + self.clip_tolerance

    def draw_shape(self):
        glBegin(GL_QUADS)
        glNormal3f(*self.normal)
        for point in self.corners():
            glVertex3f(*point)
        glEnd()

    def draw_glass(self):
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glColor4f(*self.glass_tint)
        self.draw_shape()
        glDisable(GL_BLEND)

    def draw_frame(self):
        glLineWidth(self.frame_width)
        glColor3f(*self.frame_color)
        glBegin(GL_LINE_LOOP)
        for point in self.corners():
            glVertex3f(*point)
        glEnd()

    @staticmethod
    def spanning(corner, first_edge, second_edge):
        return Mirror(Vector3(*corner), Vector3(*first_edge), Vector3(*second_edge))
