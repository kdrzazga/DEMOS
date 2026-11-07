import os
import sys

from OpenGL.GL import *

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                                "lib", "root_effect"))

from pulse_show import PulseShow, PulsingPalette, smooth_step
from sine_roots3d import RootTile, circular_fade, create_alpha_texture
from sine_roots3d_connected import ConnectedSineRoots3D


class PulseShowWithoutOpening(PulseShow):
    def __init__(self, roots):
        super().__init__(roots)
        self.settled_lean_degrees = roots.highest_tilt_degrees

    def lean_degrees(self):
        settling = smooth_step((self.elapsed_seconds - self.lean_settles_at_seconds) / self.settle_duration_seconds)
        swinging_lean = super().lean_degrees()
        return swinging_lean + (self.settled_lean_degrees - self.default_lean_degrees) * settling

    def start(self):
        self.elapsed_seconds = 0.0
        self.palette = PulsingPalette()
        self.opening = None
        self.roots.start_show(self)


class BakedRootTile(RootTile):
    def __init__(self, pixel_size, edge_fade, random):
        super().__init__(pixel_size, edge_fade, random)
        self.frame_count = 32
        self.baking_step_seconds = 0.5
        self.frames = self.bake()
        self.growth_seconds = 0.0
        self.real_seconds = 0.0
        self.is_growing = True
        self.playback_direction = 1.0
        self.texture = self.frames[0]

    def bake(self):
        growth = self.growth
        while growth.is_still_growing:
            growth.keep_growing(self.baking_step_seconds)
        glDeleteTextures([self.texture])
        frames = []
        for index in range(self.frame_count):
            growth.elapsed_seconds = growth.turnaround_seconds * index / (self.frame_count - 1)
            growth.repaint()
            self.texture = create_alpha_texture()
            self.upload()
            frames.append(self.texture)
        return frames

    def restart(self, random):
        self.start_delay_seconds = random.uniform(0.0, 3.0)
        self.growth_seconds = 0.0
        self.real_seconds = 0.0
        self.is_growing = True
        self.playback_direction = 1.0
        self.texture = self.frames[0]

    def update(self, delta_seconds):
        if self.start_delay_seconds > 0.0:
            self.start_delay_seconds -= delta_seconds
            return
        self.advance_growth_clock(delta_seconds)
        progress = self.growth_seconds / self.growth.turnaround_seconds
        self.texture = self.frames[round(progress * (self.frame_count - 1))]

    def advance_growth_clock(self, delta_seconds):
        growth = self.growth
        self.real_seconds += delta_seconds
        growth_delta = delta_seconds * growth.time_scale
        if self.real_seconds > growth.fast_forward_after_seconds:
            growth_delta *= growth.fast_forward_factor
        turnaround = growth.turnaround_seconds
        if self.is_growing:
            self.growth_seconds = min(self.growth_seconds + growth_delta, turnaround)
            if self.growth_seconds >= turnaround:
                self.is_growing = False
                self.playback_direction = -1.0
            return
        lowest = turnaround * growth.bounce_lowest_progress
        self.growth_seconds += growth_delta * self.playback_direction
        if self.growth_seconds <= lowest:
            self.growth_seconds = lowest
            self.playback_direction = 1.0
        elif self.growth_seconds >= turnaround:
            self.growth_seconds = turnaround
            self.playback_direction = -1.0


class BakedConnectedSineRoots3D(ConnectedSineRoots3D):
    def __init__(self):
        super().__init__()
        glDeleteTextures([tile.texture for tile in self.tiles])
        edge_fade = circular_fade(self.tile_pixel_size, self.solid_radius_fraction)
        self.tiles = [BakedRootTile(self.tile_pixel_size, edge_fade, self.random)
                      for _ in range(self.distinct_tile_count)]


class PulseBackdrop:
    def __init__(self, screen_width, screen_height):
        self.roots = BakedConnectedSineRoots3D()
        self.roots.aspect_ratio = screen_width / screen_height
        self.pulse_show = PulseShowWithoutOpening(self.roots)
        self.running = False

    def start(self):
        self.pulse_show.start()
        self.running = True

    def stop(self):
        self.running = False

    def update(self, real_seconds):
        if self.running:
            self.roots.update(real_seconds)

    def clear_screen(self):
        if self.running:
            glClearColor(*self.roots.background_color, 1.0)
        else:
            glClearColor(0.0, 0.0, 0.0, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    def draw(self):
        if self.running:
            self.roots.draw()
