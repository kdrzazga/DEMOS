import math

import numpy as np
import pygame
from OpenGL.GL import *


def hsl_to_rgb(hue_degrees, saturation, lightness):
    hue = np.mod(hue_degrees, 360.0) / 360.0
    chroma_scale = saturation * np.minimum(lightness, 1.0 - lightness)
    channels = []
    for offset in (0.0, 8.0, 4.0):
        sector = np.mod(offset + hue * 12.0, 12.0)
        channels.append(lightness - chroma_scale * np.clip(np.minimum(sector - 3.0, 9.0 - sector), -1.0, 1.0))
    return np.stack(np.broadcast_arrays(*channels), axis=-1) * 255.0


def distance_to_segment(x, y, start, end):
    segment_x, segment_y = end[0] - start[0], end[1] - start[1]
    along = ((x - start[0]) * segment_x + (y - start[1]) * segment_y) / (segment_x ** 2 + segment_y ** 2)
    along = np.clip(along, 0.0, 1.0)
    return np.hypot(x - start[0] - along * segment_x, y - start[1] - along * segment_y)


def vector_add(first, second):
    return tuple(a + b for a, b in zip(first, second))


def vector_scale(vector, factor):
    return tuple(component * factor for component in vector)


def vector_dot(first, second):
    return sum(a * b for a, b in zip(first, second))


def vector_cross(first, second):
    return (first[1] * second[2] - first[2] * second[1],
            first[2] * second[0] - first[0] * second[2],
            first[0] * second[1] - first[1] * second[0])


def vector_normalize(vector):
    length = math.sqrt(vector_dot(vector, vector)) or 1.0
    return vector_scale(vector, 1.0 / length)


class EllipseRegion:
    def __init__(self, center, angle_degrees, semi_axes):
        self.center = center
        self.angle = math.radians(angle_degrees)
        self.semi_axes = semi_axes

    def local_coordinates(self, x, y):
        offset_x, offset_y = x - self.center[0], y - self.center[1]
        cosine, sine = math.cos(self.angle), math.sin(self.angle)
        u = (offset_x * cosine + offset_y * sine) / self.semi_axes[0]
        v = (-offset_x * sine + offset_y * cosine) / self.semi_axes[1]
        return u, v


class WingPattern:
    def __init__(self):
        self.hue = 25.0
        self.hindwing_hue_shift = 20.0
        self.show_bands = True
        self.show_veins = True
        self.show_eyespots = True
        self.show_edge_dots = True
        self.flat_saturation = 0.8
        self.flat_lightness = 0.55
        self.band_count = 4
        self.band_hue_step = 18.0
        self.band_saturation = 0.85
        self.band_lightness = 0.62
        self.band_darkening = 0.08
        self.vein_color = (40, 30, 25)
        self.vein_width = 0.05
        self.forewing_vein_count = 7
        self.hindwing_vein_count = 5
        self.forewing_eyespot_center = (0.5, 0.15)
        self.hindwing_eyespot_center = (0.35, -0.1)
        self.eyespot_outline_radius = 0.29
        self.eyespot_iris_radius = 0.24
        self.eyespot_white_radius = 0.16
        self.eyespot_pupil_radius = 0.09
        self.eyespot_outline_color = (25, 20, 20)
        self.eyespot_white_color = (240, 240, 250)
        self.eyespot_pupil_color = (20, 20, 30)
        self.eyespot_iris_hue_shift = 200.0
        self.border_level = 0.86
        self.border_color = (30, 24, 20)
        self.edge_dot_inner_level = 0.9
        self.edge_dot_outer_level = 0.975
        self.edge_dot_half_width = 0.2
        self.forewing_edge_dot_count = 14
        self.hindwing_edge_dot_count = 10
        self.edge_dot_color = (245, 240, 225)

    def colorize(self, u, v, level, is_forewing):
        angle = np.arctan2(v, u)
        hue = self.hue + (0.0 if is_forewing else self.hindwing_hue_shift)
        rgb = self.base_colors(level, hue)
        if self.show_veins:
            self.paint_veins(rgb, angle, level, is_forewing)
        if self.show_eyespots:
            self.paint_eyespot(rgb, u, v, hue, is_forewing)
        rgb[level > self.border_level] = self.border_color
        if self.show_edge_dots:
            self.paint_edge_dots(rgb, angle, level, is_forewing)
        return rgb

    def base_colors(self, level, hue):
        if self.show_bands:
            band = np.floor(level * self.band_count)
            return hsl_to_rgb(hue + band * self.band_hue_step, self.band_saturation,
                              self.band_lightness - band * self.band_darkening)
        flat_color = hsl_to_rgb(hue, self.flat_saturation, self.flat_lightness)
        return np.broadcast_to(flat_color, level.shape + (3,)).copy()

    def paint_veins(self, rgb, angle, level, is_forewing):
        vein_count = self.forewing_vein_count if is_forewing else self.hindwing_vein_count
        tolerance = self.vein_width + 0.04 * (1.0 - level)
        rgb[(level > 0.08) & (np.abs(np.sin(angle * vein_count)) < tolerance)] = self.vein_color

    def paint_eyespot(self, rgb, u, v, hue, is_forewing):
        center = self.forewing_eyespot_center if is_forewing else self.hindwing_eyespot_center
        distance = np.hypot(u - center[0], v - center[1])
        iris_color = hsl_to_rgb(hue + self.eyespot_iris_hue_shift, 0.7, 0.45)
        rings = ((self.eyespot_outline_radius, self.eyespot_outline_color),
                 (self.eyespot_iris_radius, iris_color),
                 (self.eyespot_white_radius, self.eyespot_white_color),
                 (self.eyespot_pupil_radius, self.eyespot_pupil_color))
        for radius, color in rings:
            rgb[distance < radius] = color

    def paint_edge_dots(self, rgb, angle, level, is_forewing):
        dot_count = self.forewing_edge_dot_count if is_forewing else self.hindwing_edge_dot_count
        dot_position = angle * dot_count / (2.0 * math.pi)
        on_dot = np.abs(dot_position - np.round(dot_position)) < self.edge_dot_half_width
        in_rim = (level > self.edge_dot_inner_level) & (level < self.edge_dot_outer_level)
        rgb[on_dot & in_rim] = self.edge_dot_color


class ButterflyShape:
    def __init__(self):
        self.body = EllipseRegion((0.0, 0.05), 0.0, (0.13, 0.95))
        self.forewing = EllipseRegion((0.82, 0.55), 35.0, (0.95, 0.52))
        self.hindwing = EllipseRegion((0.62, -0.45), -40.0, (0.72, 0.44))
        self.antenna_base = (0.05, 0.85)
        self.antenna_tip = (0.55, 1.65)
        self.antenna_width = 0.022
        self.antenna_tip_radius = 0.075
        self.body_color = (55, 42, 34)
        self.body_ring_color = (85, 65, 50)
        self.body_ring_frequency = 28.0
        self.body_ring_threshold = 0.55
        self.antenna_color = (35, 28, 24)
        self.pattern = WingPattern()
        self.extent = (-1.75, 1.75, -1.1, 1.8)

    def is_body_ring(self, y):
        return (y < 0.0) & (np.sin(y * self.body_ring_frequency) > self.body_ring_threshold)

    def wing_rgba(self, x, y):
        rgba = np.zeros(x.shape + (4,), np.uint8)
        mirrored_x = np.abs(x)
        self.paint_wing(rgba, self.hindwing, mirrored_x, y, False)
        self.paint_wing(rgba, self.forewing, mirrored_x, y, True)
        return rgba

    def paint_wing(self, rgba, region, x, y, is_forewing):
        u, v = region.local_coordinates(x, y)
        level = u * u + v * v
        inside = level <= 1.0
        if not inside.any():
            return
        rgb = self.pattern.colorize(u[inside], v[inside], level[inside], is_forewing)
        rgba[inside, :3] = np.clip(rgb, 0, 255).astype(np.uint8)
        rgba[inside, 3] = 255

    def full_rgba(self, x, y):
        rgba = self.wing_rgba(x, y)
        u, v = self.body.local_coordinates(x, y)
        inside_body = u * u + v * v <= 1.0
        rgba[inside_body] = (*self.body_color, 255)
        rgba[inside_body & self.is_body_ring(y)] = (*self.body_ring_color, 255)
        mirrored_x = np.abs(x)
        on_antenna = distance_to_segment(mirrored_x, y, self.antenna_base, self.antenna_tip) < self.antenna_width
        on_antenna |= np.hypot(mirrored_x - self.antenna_tip[0], y - self.antenna_tip[1]) < self.antenna_tip_radius
        rgba[on_antenna] = (*self.antenna_color, 255)
        return rgba


class Butterfly2D:
    def __init__(self, width_pixels):
        self.shape = ButterflyShape()
        self.width_pixels = width_pixels
        self.supersampling = 2
        self.image = None
        self.render()

    def render(self):
        left, right, bottom, top = self.shape.extent
        sampled_width = self.width_pixels * self.supersampling
        units_per_pixel = (right - left) / sampled_width
        sampled_height = round((top - bottom) / units_per_pixel)
        xs = left + (np.arange(sampled_width) + 0.5) * units_per_pixel
        ys = top - (np.arange(sampled_height) + 0.5) * units_per_pixel
        x, y = np.meshgrid(xs, ys, indexing="ij")
        rgba = self.shape.full_rgba(x, y)
        sampled = pygame.Surface((sampled_width, sampled_height), pygame.SRCALPHA)
        color_pixels = pygame.surfarray.pixels3d(sampled)
        color_pixels[...] = rgba[..., :3]
        del color_pixels
        alpha_pixels = pygame.surfarray.pixels_alpha(sampled)
        alpha_pixels[...] = rgba[..., 3]
        del alpha_pixels
        final_size = (self.width_pixels, max(1, round(sampled_height / self.supersampling)))
        self.image = pygame.transform.smoothscale(sampled, final_size)

    def draw(self, surface, center, wing_opening=1.0):
        image = self.image
        if wing_opening != 1.0:
            opened_width = max(1, round(image.get_width() * wing_opening))
            image = pygame.transform.smoothscale(image, (opened_width, image.get_height()))
        surface.blit(image, image.get_rect(center=center))


class Butterfly3D:
    def __init__(self):
        self.shape = ButterflyShape()
        self.position = [0.0, 0.0, 0.0]
        self.orientation_degrees = [0.0, 0.0, 0.0]
        self.scale = 1.0
        self.wing_texture_width = 256
        self.wing_thickness_texels = 3
        self.wing_span = 1.75
        self.wing_bottom = -1.1
        self.wing_top = 1.3
        self.antenna_tip_depth = 0.3
        self.antenna_sides = 8
        self.body_stacks = 64
        self.body_slices = 24
        self.antenna_tip_stacks = 8
        self.antenna_tip_slices = 10
        self.light_direction = vector_normalize((0.4, 0.6, 0.7))
        self.ambient_light = 0.35
        self.flap_frequency = 2.5
        self.flap_amplitude_degrees = 55.0
        self.flap_rest_degrees = 20.0
        self.flap_phase = 0.0
        self.flap_angle_degrees = self.flap_rest_degrees
        self.wing_texture = None
        self.wing_texture_top = self.wing_top
        self.body_display_list = None

    def flap_wings(self, delta_seconds):
        self.flap_phase = (self.flap_phase + 2.0 * math.pi * self.flap_frequency * delta_seconds) % (2.0 * math.pi)
        self.flap_angle_degrees = self.flap_rest_degrees + self.flap_amplitude_degrees * math.sin(self.flap_phase)

    def rebuild(self):
        if self.wing_texture is not None:
            glDeleteTextures([self.wing_texture])
        self.wing_texture = None

    def forget_gl_resources(self):
        self.wing_texture = None
        self.body_display_list = None

    def draw(self):
        if self.wing_texture is None:
            self.build_wing_texture()
        if self.body_display_list is None:
            self.build_body_display_list()
        glPushAttrib(GL_ENABLE_BIT | GL_TEXTURE_BIT | GL_CURRENT_BIT)
        glDisable(GL_LIGHTING)
        glDisable(GL_CULL_FACE)
        glEnable(GL_DEPTH_TEST)
        glPushMatrix()
        glTranslatef(*self.position)
        glRotatef(self.orientation_degrees[0], 1.0, 0.0, 0.0)
        glRotatef(self.orientation_degrees[1], 0.0, 1.0, 0.0)
        glRotatef(self.orientation_degrees[2], 0.0, 0.0, 1.0)
        glScalef(self.scale, self.scale, self.scale)
        glDisable(GL_TEXTURE_2D)
        glCallList(self.body_display_list)
        self.draw_wing(1.0)
        self.draw_wing(-1.0)
        glPopMatrix()
        glPopAttrib()

    def draw_wing(self, side):
        flap_radians = math.radians(self.flap_angle_degrees)
        wing_normal = (-side * math.sin(flap_radians), 0.0, math.cos(flap_radians))
        brightness = self.ambient_light + (1.0 - self.ambient_light) * abs(vector_dot(wing_normal, self.light_direction))
        texel_size = self.wing_span / self.wing_texture_width
        glPushMatrix()
        glScalef(side, 1.0, 1.0)
        glRotatef(-self.flap_angle_degrees, 0.0, 1.0, 0.0)
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, self.wing_texture)
        glTexEnvi(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_MODULATE)
        glEnable(GL_ALPHA_TEST)
        glAlphaFunc(GL_GREATER, 0.5)
        glColor3f(brightness, brightness, brightness)
        glBegin(GL_QUADS)
        for layer in range(self.wing_thickness_texels):
            depth = (layer - (self.wing_thickness_texels - 1) / 2.0) * texel_size
            glTexCoord2f(0.0, 0.0)
            glVertex3f(0.0, self.wing_bottom, depth)
            glTexCoord2f(1.0, 0.0)
            glVertex3f(self.wing_span, self.wing_bottom, depth)
            glTexCoord2f(1.0, 1.0)
            glVertex3f(self.wing_span, self.wing_texture_top, depth)
            glTexCoord2f(0.0, 1.0)
            glVertex3f(0.0, self.wing_texture_top, depth)
        glEnd()
        glPopMatrix()

    def build_wing_texture(self):
        width = self.wing_texture_width
        units_per_texel = self.wing_span / width
        height = round((self.wing_top - self.wing_bottom) / units_per_texel)
        self.wing_texture_top = self.wing_bottom + height * units_per_texel
        xs = (np.arange(width) + 0.5) * units_per_texel
        ys = self.wing_bottom + (np.arange(height) + 0.5) * units_per_texel
        x, y = np.meshgrid(xs, ys)
        rgba = np.ascontiguousarray(self.shape.wing_rgba(x, y))
        self.wing_texture = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.wing_texture)
        glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, rgba.tobytes())

    def build_body_display_list(self):
        self.body_display_list = glGenLists(1)
        glNewList(self.body_display_list, GL_COMPILE)
        body = self.shape.body
        body_center = (body.center[0], body.center[1], 0.0)
        body_semi_axes = (body.semi_axes[0], body.semi_axes[1], body.semi_axes[0])
        self.draw_spheroid(body_center, body_semi_axes, self.body_color_at, self.body_stacks, self.body_slices)
        tip_radius = self.shape.antenna_tip_radius
        for side in (-1.0, 1.0):
            base = (side * self.shape.antenna_base[0], self.shape.antenna_base[1], 0.0)
            tip = (side * self.shape.antenna_tip[0], self.shape.antenna_tip[1], self.antenna_tip_depth)
            self.draw_tube(base, tip, self.shape.antenna_width, self.shape.antenna_color)
            self.draw_spheroid(tip, (tip_radius, tip_radius, tip_radius), lambda point: self.shape.antenna_color,
                               self.antenna_tip_stacks, self.antenna_tip_slices)
        glEndList()

    def body_color_at(self, point):
        if self.shape.is_body_ring(point[1]):
            return self.shape.body_ring_color
        return self.shape.body_color

    def emit_shaded_vertex(self, point, normal, color):
        intensity = self.ambient_light + (1.0 - self.ambient_light) * max(0.0, vector_dot(normal, self.light_direction))
        glColor3f(*(channel / 255.0 * intensity for channel in color))
        glVertex3f(*point)

    def draw_spheroid(self, center, semi_axes, color_at, stacks, slices):
        for stack in range(stacks):
            glBegin(GL_QUAD_STRIP)
            for slice_index in range(slices + 1):
                azimuth = 2.0 * math.pi * slice_index / slices
                for polar_index in (stack, stack + 1):
                    polar = math.pi * polar_index / stacks
                    unit = (math.sin(polar) * math.cos(azimuth), math.cos(polar), math.sin(polar) * math.sin(azimuth))
                    point = vector_add(center, tuple(axis * component for axis, component in zip(semi_axes, unit)))
                    normal = vector_normalize(tuple(component / axis for axis, component in zip(semi_axes, unit)))
                    self.emit_shaded_vertex(point, normal, color_at(point))
            glEnd()

    def draw_tube(self, start, end, radius, color):
        axis = vector_normalize(tuple(b - a for a, b in zip(start, end)))
        helper = (0.0, 0.0, 1.0) if abs(axis[2]) < 0.9 else (1.0, 0.0, 0.0)
        first = vector_normalize(vector_cross(axis, helper))
        second = vector_cross(axis, first)
        glBegin(GL_QUAD_STRIP)
        for side_index in range(self.antenna_sides + 1):
            around = 2.0 * math.pi * side_index / self.antenna_sides
            normal = vector_add(vector_scale(first, math.cos(around)), vector_scale(second, math.sin(around)))
            offset = vector_scale(normal, radius)
            self.emit_shaded_vertex(vector_add(start, offset), normal, color)
            self.emit_shaded_vertex(vector_add(end, offset), normal, color)
        glEnd()
