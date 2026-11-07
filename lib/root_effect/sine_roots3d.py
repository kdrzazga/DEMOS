import math
import random as random_module

import numpy as np
import pygame
from OpenGL.GL import *
from OpenGL.GLU import gluLookAt, gluPerspective

from sine_roots import SineRootGrowth


def to_unit_color(color):
    return tuple(channel / 255 for channel in color)


def mix_colors(first, second, amount):
    return tuple(a + (b - a) * amount for a, b in zip(first, second))


def create_alpha_texture():
    texture = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, texture)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
    glTexParameteri(GL_TEXTURE_2D, GL_GENERATE_MIPMAP, GL_TRUE)
    return texture


def upload_alpha_texture(texture, alpha):
    size = alpha.shape[0]
    glBindTexture(GL_TEXTURE_2D, texture)
    glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_ALPHA, size, size, 0, GL_ALPHA, GL_UNSIGNED_BYTE,
                 np.ascontiguousarray(alpha))


def circular_fade(pixel_size, solid_radius_fraction):
    coordinates = (np.arange(pixel_size) + 0.5) / pixel_size * 2.0 - 1.0
    distance_from_center = np.hypot(coordinates[None, :], coordinates[:, None])
    fade = (1.0 - distance_from_center) / (1.0 - solid_radius_fraction)
    return (np.clip(fade, 0.0, 1.0) * 255).astype(np.uint8)


class RootTile:
    def __init__(self, pixel_size, edge_fade, random):
        self.pixel_size = pixel_size
        self.edge_fade = edge_fade.astype(np.uint16)
        self.growth = SineRootGrowth(pixel_size, pixel_size, random.randrange(1 << 30))
        self.growth.maximum_root_count = 300
        self.growth.growth_speed *= pixel_size / 720
        self.growth.time_scale *= random.uniform(0.7, 1.3)
        self.growth.background_color = (255, 255, 255)
        self.growth.root_color = (0, 0, 0)
        self.growth.restart()
        self.start_delay_seconds = random.uniform(0.0, 3.0)
        self.texture = create_alpha_texture()
        self.upload()

    def upload(self):
        rgb = np.frombuffer(pygame.image.tobytes(self.growth.canvas, "RGB"), np.uint8)
        coverage = 255 - rgb.reshape(self.pixel_size, self.pixel_size, 3)[:, :, 0].astype(np.uint16)
        upload_alpha_texture(self.texture, (coverage * self.edge_fade // 255).astype(np.uint8))

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
        self.color_index = 0
        self.is_waiting = False


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
        self.travel_right_speed = 5.0
        self.travel_toward_camera_speed = 8.0
        self.is_releasing = True
        self.patches = self.scatter_patches()
        for patch_index, patch in enumerate(self.patches):
            patch.color_index = patch_index

    def hold_back_all(self):
        self.is_releasing = False
        for patch in self.patches:
            patch.is_waiting = True

    def release(self):
        self.is_releasing = True

    def visible_patches(self):
        return [patch for patch in self.patches if not patch.is_waiting]

    def move(self, patch, delta_seconds):
        patch.x += self.travel_right_speed * delta_seconds
        patch.z += self.travel_toward_camera_speed * delta_seconds

    def path_progress(self, patch):
        return (patch.z - self.far_edge_z) / self.region_depth

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
            self.move(patch, delta_seconds)
            wrapped = False
            if patch.x > self.right_edge_x:
                patch.x -= self.region_width
                wrapped = True
            if patch.z > self.near_edge_z:
                patch.z -= self.region_depth
                wrapped = True
            if wrapped:
                self.dress(patch)
                if self.is_releasing:
                    patch.is_waiting = False

    @staticmethod
    def draw_square(half_size):
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

    def draw_patch(self, patch, root_texture, disc_texture, surface_color, root_color):
        glPushMatrix()
        glTranslatef(patch.x, 0.0, patch.z)
        glRotatef(patch.angle_degrees, 0.0, 1.0, 0.0)
        glBindTexture(GL_TEXTURE_2D, disc_texture)
        glColor4f(*surface_color, 1.0)
        self.draw_square(patch.size / 2)
        glBindTexture(GL_TEXTURE_2D, root_texture)
        glColor4f(*root_color, 1.0)
        self.draw_square(patch.size / 2)
        glPopMatrix()

    def draw_patches(self, patches, tiles, disc_texture, surface_color, color_of_patch):
        for patch in patches:
            self.draw_patch(patch, tiles[patch.tile_index].texture, disc_texture,
                            surface_color, color_of_patch(patch))

    def draw(self, tiles, disc_texture, surface_color, color_of_patch):
        self.draw_patches(self.visible_patches(), tiles, disc_texture, surface_color, color_of_patch)


class SineRoots3D:
    def __init__(self, seed=None):
        self.random = random_module.Random(seed)
        self.field_of_view = 45.0
        self.aspect_ratio = 16.0 / 9.0
        self.tile_pixel_size = 256
        self.solid_radius_fraction = 0.7
        self.distinct_tile_count = 8
        self.eye = (0.0, 6.0, 5.0)
        self.look_at = (0.0, 0.0, -3.0)
        self.fog_start = 12.0
        self.fog_end = 24.0
        self.surface_tilt_degrees = 0.0
        self.lowest_tilt_degrees = -35.0
        self.highest_tilt_degrees = 50.0
        self.background_color = to_unit_color((226, 229, 235))
        self.root_color = to_unit_color((24, 20, 20))
        self.palette = None
        self.opening = None
        self.show = None
        edge_fade = circular_fade(self.tile_pixel_size, self.solid_radius_fraction)
        self.disc_texture = create_alpha_texture()
        upload_alpha_texture(self.disc_texture, edge_fade)
        self.tiles = [RootTile(self.tile_pixel_size, edge_fade, self.random)
                      for _ in range(self.distinct_tile_count)]
        self.field = ScatteredField(len(self.tiles), self.random)

    def restart(self):
        for tile in self.tiles:
            tile.restart(self.random)

    def set_surface_color(self, color):
        self.palette = None
        self.background_color = to_unit_color(color)

    def set_root_color(self, color):
        self.palette = None
        self.root_color = to_unit_color(color)

    def tilt_surface(self, degrees):
        self.surface_tilt_degrees = min(max(self.surface_tilt_degrees + degrees, self.lowest_tilt_degrees),
                                        self.highest_tilt_degrees)

    def start_show(self, show):
        self.show = show
        self.palette = show.palette
        self.opening = show.opening
        self.follow_palette()

    def follow_palette(self):
        self.background_color = to_unit_color(self.palette.surface_color())
        self.root_color = to_unit_color(self.palette.shifting_root_color())

    def color_of_patch(self, patch):
        if self.palette is None:
            return self.root_color
        return to_unit_color(self.palette.patch_color(patch.color_index))

    def update(self, delta_seconds):
        if self.palette is not None:
            self.palette.update(delta_seconds)
            self.follow_palette()
        if self.opening is not None:
            self.opening.update(delta_seconds)
        if self.show is not None:
            self.show.update(delta_seconds)
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
        self.field.draw(self.tiles, self.disc_texture, self.background_color, self.color_of_patch)
        if self.opening is not None:
            self.field.draw_patches(self.opening.patches, self.tiles, self.disc_texture,
                                    self.background_color, self.color_of_patch)

    def draw(self):
        glPushAttrib(GL_ENABLE_BIT | GL_FOG_BIT | GL_CURRENT_BIT | GL_COLOR_BUFFER_BIT | GL_TEXTURE_BIT)
        glDisable(GL_DEPTH_TEST)
        glDisable(GL_LIGHTING)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glEnable(GL_TEXTURE_2D)
        glTexEnvi(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_MODULATE)
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
        glTranslatef(*self.look_at)
        glRotatef(self.surface_tilt_degrees, 1.0, 0.0, 0.0)
        glTranslatef(*(-coordinate for coordinate in self.look_at))

        self.draw_scene()

        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glPopAttrib()
