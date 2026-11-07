import math
import random as random_module

import numpy as np
import pygame
from OpenGL.GL import *
from OpenGL.GLU import gluLookAt, gluPerspective

from sine_roots import SineRootGrowth


class RootTile:
    def __init__(self, pixel_size, random):
        self.pixel_size = pixel_size
        self.solid_radius_fraction = 0.7
        self.growth = SineRootGrowth(pixel_size, pixel_size, random.randrange(1 << 30))
        self.growth.maximum_root_count = 300
        self.growth.growth_speed *= pixel_size / 720
        self.growth.time_scale *= random.uniform(0.7, 1.3)
        self.growth.restart()
        self.start_delay_seconds = random.uniform(0.0, 3.0)
        self.edge_fade = self.build_edge_fade()
        self.texture = self.create_texture()
        self.upload()

    def build_edge_fade(self):
        coordinates = (np.arange(self.pixel_size) + 0.5) / self.pixel_size * 2.0 - 1.0
        distance_from_center = np.hypot(coordinates[None, :], coordinates[:, None])
        fade = (1.0 - distance_from_center) / (1.0 - self.solid_radius_fraction)
        return (np.clip(fade, 0.0, 1.0) * 255).astype(np.uint8)

    def create_texture(self):
        texture = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, texture)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_GENERATE_MIPMAP, GL_TRUE)
        return texture

    def upload(self):
        rgb = np.frombuffer(pygame.image.tobytes(self.growth.canvas, "RGB"), np.uint8)
        rgba = np.dstack((rgb.reshape(self.pixel_size, self.pixel_size, 3), self.edge_fade))
        glBindTexture(GL_TEXTURE_2D, self.texture)
        glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, self.pixel_size, self.pixel_size, 0,
                     GL_RGBA, GL_UNSIGNED_BYTE, np.ascontiguousarray(rgba))

    def restart(self, random):
        self.growth.restart()
        self.start_delay_seconds = random.uniform(0.0, 3.0)
        self.upload()

    def update(self, delta_seconds):
        if self.start_delay_seconds > 0.0:
            self.start_delay_seconds -= delta_seconds
            return
        self.growth.update(delta_seconds)
        self.upload()


class RootPatch:
    def __init__(self, x, z, size):
        self.x = x
        self.z = z
        self.size = size
        self.tile_index = 0
        self.angle_degrees = 0.0


class ScatteredField:
    def __init__(self, tile_count, random):
        self.tile_count = tile_count
        self.random = random
        self.left_edge_x = -22.0
        self.right_edge_x = 22.0
        self.far_edge_z = -24.0
        self.near_edge_z = 8.0
        self.smallest_patch = 1.6
        self.largest_patch = 3.2
        self.smallest_scale = 1.0
        self.largest_scale = 2.5
        self.spacing_factor = 1.5
        self.wanted_patch_count = 45
        self.placement_attempts = 4000
        self.travel_right_speed = 2.5
        self.travel_toward_camera_speed = 4.0
        self.patches = self.scatter_patches()

    @property
    def region_width(self):
        return self.right_edge_x - self.left_edge_x

    @property
    def region_depth(self):
        return self.near_edge_z - self.far_edge_z

    def wrapped_gap(self, first, second):
        gap_x = abs(first.x - second.x) % self.region_width
        gap_z = abs(first.z - second.z) % self.region_depth
        return math.hypot(min(gap_x, self.region_width - gap_x), min(gap_z, self.region_depth - gap_z))

    def has_room_for(self, candidate, patches):
        for patch in patches:
            needed_gap = (candidate.size + patch.size) / 2 * self.spacing_factor
            if self.wrapped_gap(candidate, patch) < needed_gap:
                return False
        return True

    def dress(self, patch):
        patch.tile_index = self.random.randrange(self.tile_count)
        patch.angle_degrees = self.random.uniform(0.0, 360.0)

    def scatter_patches(self):
        patches = []
        for _ in range(self.placement_attempts):
            if len(patches) >= self.wanted_patch_count:
                break
            candidate = RootPatch(self.random.uniform(self.left_edge_x, self.right_edge_x),
                                  self.random.uniform(self.far_edge_z, self.near_edge_z),
                                  self.random.uniform(self.smallest_patch, self.largest_patch)
                                  * self.random.uniform(self.smallest_scale, self.largest_scale))
            if self.has_room_for(candidate, patches):
                self.dress(candidate)
                patches.append(candidate)
        return patches

    def update(self, delta_seconds):
        for patch in self.patches:
            patch.x += self.travel_right_speed * delta_seconds
            patch.z += self.travel_toward_camera_speed * delta_seconds
            wrapped = False
            if patch.x > self.right_edge_x:
                patch.x -= self.region_width
                wrapped = True
            if patch.z > self.near_edge_z:
                patch.z -= self.region_depth
                wrapped = True
            if wrapped:
                self.dress(patch)

    def draw_patch(self, patch, texture):
        half_size = patch.size / 2
        glBindTexture(GL_TEXTURE_2D, texture)
        glPushMatrix()
        glTranslatef(patch.x, 0.0, patch.z)
        glRotatef(patch.angle_degrees, 0.0, 1.0, 0.0)
        glBegin(GL_QUADS)
        glTexCoord2f(0.0, 0.0)
        glVertex3f(-half_size, 0.0, -half_size)
        glTexCoord2f(1.0, 0.0)
        glVertex3f(half_size, 0.0, -half_size)
        glTexCoord2f(1.0, 1.0)
        glVertex3f(half_size, 0.0, half_size)
        glTexCoord2f(0.0, 1.0)
        glVertex3f(-half_size, 0.0, half_size)
        glEnd()
        glPopMatrix()

    def draw(self, tiles):
        for patch in self.patches:
            self.draw_patch(patch, tiles[patch.tile_index].texture)


class SineRoots3D:
    def __init__(self, seed=None):
        self.random = random_module.Random(seed)
        self.field_of_view = 45.0
        self.aspect_ratio = 16.0 / 9.0
        self.tile_pixel_size = 256
        self.distinct_tile_count = 8
        self.eye = (0.0, 6.0, 5.0)
        self.look_at = (0.0, 0.0, -3.0)
        self.fog_start = 12.0
        self.fog_end = 24.0
        self.background_color = (226 / 255, 229 / 255, 235 / 255)
        self.tiles = [RootTile(self.tile_pixel_size, self.random) for _ in range(self.distinct_tile_count)]
        self.field = ScatteredField(len(self.tiles), self.random)

    def restart(self):
        for tile in self.tiles:
            tile.restart(self.random)

    def set_surface_color(self, color):
        self.background_color = tuple(channel / 255 for channel in color)
        for tile in self.tiles:
            tile.growth.background_color = color

    def set_root_color(self, color):
        for tile in self.tiles:
            tile.growth.root_color = color

    def update(self, delta_seconds):
        for tile in self.tiles:
            tile.update(delta_seconds)
        self.field.update(delta_seconds)

    def apply_fog(self):
        glEnable(GL_FOG)
        glFogi(GL_FOG_MODE, GL_LINEAR)
        glFogf(GL_FOG_START, self.fog_start)
        glFogf(GL_FOG_END, self.fog_end)
        glFogfv(GL_FOG_COLOR, (*self.background_color, 1.0))

    def draw_scene(self):
        self.field.draw(self.tiles)

    def draw(self):
        glPushAttrib(GL_ENABLE_BIT | GL_FOG_BIT | GL_CURRENT_BIT | GL_COLOR_BUFFER_BIT)
        glDisable(GL_DEPTH_TEST)
        glDisable(GL_LIGHTING)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glEnable(GL_TEXTURE_2D)
        self.apply_fog()
        glColor4f(1.0, 1.0, 1.0, 1.0)

        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        gluPerspective(self.field_of_view, self.aspect_ratio, 0.1, 100.0)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        gluLookAt(*self.eye, *self.look_at, 0.0, 1.0, 0.0)

        self.draw_scene()

        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glPopAttrib()
