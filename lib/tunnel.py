import math
from time import time
import random

import arcade
import pygame
from OpenGL.GL import *
from OpenGL.GLU import gluBuild2DMipmaps, gluLookAt, gluPerspective


class Dot:
    def __init__(self, screen_width, screen_height):
        self.width = screen_width
        self.height = screen_height
        self.speed = 0.0
        self.size = 1
        self.y = self.width / 2
        self.x = self.height / 2
        self.reset()

    def reset(self):
        angle = random.uniform(0, 2 * math.pi)
        radius = random.uniform(30, min(self.width, self.height))
        self.x = self.width / 2 + math.cos(angle) * radius
        self.y = self.height / 2 + math.sin(angle) * radius
        self.size = 1
        self.speed = 0.0

    def update(self):
        dx = (self.width / 2) - self.x
        dy = (self.height / 2) - self.y
        distance = math.hypot(dx, dy)
        if distance != 0:
            dx /= distance
            dy /= distance
        acceleration = 0.1
        self.speed += acceleration
        self.x += dx * self.speed
        self.y += dy * self.speed
        if distance < 10:
            self.reset()


class TunnelEffect:
    def __init__(self, enlarge_delay: int, screen_width:int, screen_height:int, color:arcade.color):
        self.color = color
        self.width = screen_width
        self.height = screen_height
        NUM_DOTS = 400
        self.max_dots = NUM_DOTS
        self.dots = [Dot(screen_width, screen_height) for _ in range(NUM_DOTS)]
        self.dot_size = 1
        self.enlarge_time = time() + enlarge_delay

    def draw(self):
        for dot in self.dots:
            arcade.draw_circle_filled(dot.x, dot.y, self.dot_size, self.color)

    def update(self):
        #print(self.enlarge_time, time())
        if self.enlarge_time < time() and self.dot_size < 0.12*self.width:
            self.dot_size += 0.05 + 0.01*self.dot_size**1.75

        for dot in self.dots:
            dot.update()

    def new_dot(self, speed):
        dot = Dot(self.width, self.height)
        dot.speed = speed
        self.dots.append(dot)
        # Keep the dot pool bounded. Dots already recycle themselves in
        # update() (reset() when they reach the centre), so appending on every
        # frame without a cap just makes each frame heavier to draw -- which is
        # what made the animation gradually slow down toward the end.
        if len(self.dots) > self.max_dots:
            del self.dots[0]


class SurfaceTunnelEffect(TunnelEffect):
    def __init__(self, enlarge_delay, surface_width, surface_height, color):
        super().__init__(enlarge_delay, surface_width, surface_height, color)
        self.dot_scale = surface_width / 800
        self.largest_dot_share = 0.12

    @property
    def is_filled(self):
        return self.dot_size >= self.largest_dot_share * self.width

    def draw_on(self, surface, brightness):
        shaded_color = tuple(round(channel * brightness) for channel in self.color[:3])
        radius = max(1, round(self.dot_size * self.dot_scale))
        for dot in self.dots:
            pygame.draw.circle(surface, shaded_color, (round(dot.x), round(self.height - dot.y)), radius)


class IsometricSineTunnel:
    def __init__(self, color: arcade.color.Color, angle_deg=66):
        self.angle_deg = angle_deg
        self.phase = 0
        self.color = color

    def update(self, delta_time, speed=2):
        self.phase += speed * delta_time

    def draw(self, surface_width, surface_height, amplitude, frequency, horizon_x, min_y):
        points = []
        angle_rad = math.radians(self.angle_deg)

        for y in range(0, surface_height, 2):
            sine_value = amplitude * math.sin(frequency * (y + self.phase))
            # Convert to isometric projection with x as the sine value
            iso_x, iso_y = self.iso_transform(sine_value + horizon_x, y, angle_rad, surface_width, surface_height)
            if iso_y > min_y:
                points.append((iso_x, iso_y))

        arcade.draw_lines(points, self.color, 1)

    def iso_transform(self, x, y, angle_rad, surface_width, surface_height):
        iso_x = x - y * math.cos(angle_rad)
        iso_y = y * math.sin(angle_rad)

        iso_x += surface_width / 4
        iso_y += surface_height / 4
        return iso_x, iso_y


class SurfaceSineTunnel(IsometricSineTunnel):
    def draw_on(self, surface, brightness, amplitude, frequency, horizon_x, min_y):
        width, height = surface.get_size()
        tunnel_width = 2 * width
        tunnel_height = 2 * height
        angle_rad = math.radians(self.angle_deg)
        points = []
        for y in range(0, tunnel_height, 2):
            sine_value = amplitude * math.sin(frequency * (y + self.phase))
            iso_x, iso_y = self.iso_transform(sine_value + horizon_x, y, angle_rad, tunnel_width, tunnel_height)
            if iso_y > min_y:
                points.append((iso_x, height - iso_y))
        if len(points) > 1:
            shaded_color = tuple(round(channel * brightness) for channel in self.color)
            pygame.draw.aalines(surface, shaded_color, False, points)


class BlueTunnel:
    def __init__(self, width):
        pixel_scale = width / 512
        self.curve_count = 96
        self.speed = 400.0 * pixel_scale
        self.amplitude = 0.02 * width
        self.frequency = 0.05 / pixel_scale
        self.horizon_x = 0.01 * width
        self.min_y = 0.0
        self.curves = [SurfaceSineTunnel(self.blue_shade(index), angle_deg=int(370 * index / self.curve_count))
                       for index in range(self.curve_count)]

    def blue_shade(self, index):
        red = round(40 * index / self.curve_count)
        green = round(170 * abs(math.sin(index / 12)))
        blue = 140 + round(115 * abs(math.cos(index / 20)))
        return red, green, blue

    def update(self, seconds):
        for curve in self.curves:
            curve.update(seconds, self.speed)

    def draw(self, surface, brightness):
        for curve in self.curves:
            curve.draw_on(surface, brightness, self.amplitude, self.frequency, self.horizon_x, self.min_y)


class OpenGlTunnel:
    def __init__(self):
        self.half_width = 2.0
        self.half_height = 1.5
        self.length = 80.0
        self.tile_size = 2.0
        self.speed = 8.0
        self.fog_distance = 36.0
        self.field_of_view = 60.0
        self.near = 0.1
        self.fade_in_duration = 0.5
        self.segment_count = 40
        self.time = 0.0
        self.travelled = 0.0
        self.wall_texture = None
        self.floor_texture = None
        self.walls_list = None
        self.floor_list = None

    def restart(self):
        self.time = 0.0
        self.travelled = 0.0

    def update(self, seconds):
        self.time += seconds
        self.travelled += seconds * self.speed

    def draw(self, viewport_width, viewport_height):
        if self.walls_list is None:
            self.prepare()
        glPushAttrib(GL_ALL_ATTRIB_BITS)
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        gluPerspective(self.field_of_view, viewport_width / viewport_height, self.near, self.length)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        self.look()
        glMatrixMode(GL_TEXTURE)
        glPushMatrix()
        glLoadIdentity()
        glTranslatef(0.0, self.travelled / self.tile_size, 0.0)
        glMatrixMode(GL_MODELVIEW)

        glDisable(GL_DEPTH_TEST)
        glDisable(GL_CULL_FACE)
        glDisable(GL_BLEND)
        glDisable(GL_LIGHTING)
        glEnable(GL_TEXTURE_2D)
        glTexEnvi(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_MODULATE)
        self.enable_fog()
        brightness = self.wall_brightness()
        glColor4f(brightness, brightness, brightness, 1.0)
        glBindTexture(GL_TEXTURE_2D, self.wall_texture)
        glCallList(self.walls_list)
        glBindTexture(GL_TEXTURE_2D, self.floor_texture)
        glCallList(self.floor_list)
        glBindTexture(GL_TEXTURE_2D, 0)
        self.draw_inside()

        glMatrixMode(GL_TEXTURE)
        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glPopMatrix()
        glPopAttrib()

    def wall_brightness(self):
        return min(1.0, self.time / self.fade_in_duration)

    def draw_inside(self):
        pass

    def look(self):
        camera_x = 0.35 * math.sin(self.time * 0.9)
        camera_y = 0.2 * math.sin(self.time * 1.3)
        up_x = 0.12 * math.sin(self.time * 0.7)
        up_length = math.hypot(up_x, 1.0)
        gluLookAt(camera_x, camera_y, 0.0, camera_x, camera_y, -1.0, up_x / up_length, 1.0 / up_length, 0.0)

    def enable_fog(self):
        glEnable(GL_FOG)
        glFogi(GL_FOG_MODE, GL_LINEAR)
        glFogf(GL_FOG_START, 0.0)
        glFogf(GL_FOG_END, self.fog_distance)
        glFogfv(GL_FOG_COLOR, (0.0, 0.0, 0.0, 1.0))
        glHint(GL_FOG_HINT, GL_NICEST)

    def prepare(self):
        self.wall_texture = self.repeating_texture(self.grid_surface())
        self.floor_texture = self.repeating_texture(self.checker_surface())
        half_width = self.half_width
        half_height = self.half_height
        self.walls_list = self.compile_surfaces([(-half_width, -half_height, -half_width, half_height),
                                                 (half_width, -half_height, half_width, half_height),
                                                 (-half_width, half_height, half_width, half_height)])
        self.floor_list = self.compile_surfaces([(-half_width, -half_height, half_width, -half_height)])

    def compile_surfaces(self, edges):
        display_list = glGenLists(1)
        glNewList(display_list, GL_COMPILE)
        for edge in edges:
            self.emit_surface(*edge)
        glEndList()
        return display_list

    def emit_surface(self, first_x, first_y, second_x, second_y):
        across = math.hypot(second_x - first_x, second_y - first_y) / self.tile_size
        segment_length = self.length / self.segment_count
        glBegin(GL_QUAD_STRIP)
        for segment in range(self.segment_count + 1):
            depth = segment * segment_length
            along = depth / self.tile_size
            glTexCoord2f(0.0, along)
            glVertex3f(first_x, first_y, -depth)
            glTexCoord2f(across, along)
            glVertex3f(second_x, second_y, -depth)
        glEnd()

    def grid_surface(self):
        surface = pygame.Surface((128, 128), pygame.SRCALPHA)
        surface.fill(self.color_of(0.03, 0.06, 0.16))
        line_color = self.color_of(0.08, 0.2, 0.45)
        surface.fill(line_color, (0, 62, 128, 4))
        surface.fill(line_color, (62, 0, 4, 128))
        edge_color = self.color_of(0.15, 0.45, 0.95)
        surface.fill(edge_color, (0, 0, 128, 6))
        surface.fill(edge_color, (0, 0, 6, 128))
        return surface

    def checker_surface(self):
        surface = pygame.Surface((128, 128), pygame.SRCALPHA)
        surface.fill(self.color_of(0.12, 0.12, 0.16))
        light_color = self.color_of(0.7, 0.72, 0.78)
        surface.fill(light_color, (0, 0, 64, 64))
        surface.fill(light_color, (64, 64, 64, 64))
        return surface

    def color_of(self, red, green, blue):
        return round(red * 255), round(green * 255), round(blue * 255), 255

    def repeating_texture(self, surface):
        width, height = surface.get_size()
        texture = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, texture)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
        glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
        gluBuild2DMipmaps(GL_TEXTURE_2D, GL_RGBA, width, height, GL_RGBA, GL_UNSIGNED_BYTE,
                          pygame.image.tobytes(surface, "RGBA", False))
        glBindTexture(GL_TEXTURE_2D, 0)
        return texture
