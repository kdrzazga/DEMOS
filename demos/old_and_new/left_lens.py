import math
import os
import random

import pygame
from OpenGL.GL import *

os.environ["PATH"] += os.pathsep
from lib.tunnel import OpenGlTunnel, SurfaceTunnelEffect
from demos.old_and_new.actors import BorderColoredLens
from demos.old_and_new.stages import Stage


class FillingBlackBars:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.random = random.Random(11)
        thickness_scale = height / 208
        self.thickness_range = (round(2 * thickness_scale), round(9 * thickness_scale))
        self.bar_color = (0, 0, 0, 255)
        self.covered_rows = [False] * height
        self.covered_count = 0
        self.bars = []

    def fill_to(self, share):
        target_count = round(self.height * share)
        while self.covered_count < target_count:
            self.add_bar()

    def add_bar(self):
        uncovered_rows = [row for row, covered in enumerate(self.covered_rows) if not covered]
        top = self.random.choice(uncovered_rows)
        thickness = self.random.randint(*self.thickness_range)
        for row in range(top, min(top + thickness, self.height)):
            if not self.covered_rows[row]:
                self.covered_rows[row] = True
                self.covered_count += 1
        self.bars.append((top, thickness))

    def draw(self, surface):
        for top, thickness in self.bars:
            surface.fill(self.bar_color, (0, top, self.width, thickness))


class TunnelSnapshot:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.tunnel = OpenGlTunnel()
        self.texture_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.texture_id)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, width, height, 0, GL_RGB, GL_UNSIGNED_BYTE, None)
        glBindTexture(GL_TEXTURE_2D, 0)

    def update(self, seconds):
        self.tunnel.update(seconds)

    def capture(self):
        glViewport(0, 0, self.width, self.height)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        self.tunnel.draw(self.width, self.height)
        glBindTexture(GL_TEXTURE_2D, self.texture_id)
        glCopyTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0, 0, 0, self.width, self.height)
        glBindTexture(GL_TEXTURE_2D, 0)


class LensPicture:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.surface = pygame.Surface((width, height), pygame.SRCALPHA)
        self.bars = FillingBlackBars(width, height)
        self.tunnel = None
        self.tunnel_color = (255, 255, 255)
        self.tunnel_enlarge_delay = 6.0
        self.tunnel_brightness = 0.0
        self.tunnel_snapshot = TunnelSnapshot(1024, 416)
        self.snapshot_running = False
        self.visible = False
        self.texture_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.texture_id)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, None)
        glBindTexture(GL_TEXTURE_2D, 0)

    def start_tunnel(self):
        self.tunnel = SurfaceTunnelEffect(self.tunnel_enlarge_delay, self.width, self.height, self.tunnel_color)

    def update_tunnel(self, seconds):
        if self.snapshot_running:
            self.tunnel_snapshot.update(seconds)
            return
        if self.tunnel is None:
            self.start_tunnel()
        self.tunnel.update()
        self.snapshot_running = self.tunnel.is_filled

    @property
    def shown_texture_id(self):
        return self.tunnel_snapshot.texture_id if self.snapshot_running else self.texture_id

    def capture(self):
        if self.snapshot_running:
            self.tunnel_snapshot.capture()

    def refresh(self):
        if self.snapshot_running:
            return
        self.surface.fill((0, 0, 0, 0))
        self.bars.draw(self.surface)
        if self.tunnel is not None and self.tunnel_brightness > 0.0:
            self.tunnel.draw_on(self.surface, self.tunnel_brightness)
        pixels = pygame.image.tobytes(self.surface, "RGBA", False)
        glBindTexture(GL_TEXTURE_2D, self.texture_id)
        glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
        glTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0, self.width, self.height, GL_RGBA, GL_UNSIGNED_BYTE, pixels)
        glBindTexture(GL_TEXTURE_2D, 0)


class LeftLens(BorderColoredLens):
    def __init__(self, head):
        lenses = head.sunglasses.lenses
        lens_index = min(range(len(lenses)), key=lambda index: lenses[index].outline.center[0])
        super().__init__(lenses[lens_index].outline, head.c64_screen)
        lenses[lens_index] = self
        self.pose = head.pose
        self.picture = LensPicture(2048, 832)
        self.picture_lift = 0.004
        self.picture_list = None

    def capture_tunnel(self):
        if self.picture.visible:
            self.picture.capture()

    def world_center(self):
        return self.pose.transform_point(self.outline.center + (0.0, self.bulge, 0.0))

    def world_height(self):
        return 2.0 * self.outline.half_length * self.pose.scale

    def emit_picture_vertex(self, ring, slice_index):
        position, _normal = self.lens_point(ring, slice_index)
        offset = position - self.outline.center
        glTexCoord2f(0.5 + offset[0] / (2.0 * self.outline.half_width),
                     0.5 + offset[2] / (2.0 * self.outline.half_length))
        glVertex3f(position[0], position[1] + self.picture_lift, position[2])

    def compile_picture(self):
        self.picture_list = glGenLists(1)
        glNewList(self.picture_list, GL_COMPILE)
        for ring in range(self.rings):
            glBegin(GL_TRIANGLE_STRIP)
            for slice_index in range(self.slices + 1):
                self.emit_picture_vertex(ring + 1, slice_index)
                self.emit_picture_vertex(ring, slice_index)
            glEnd()
        glEndList()

    def draw(self):
        super().draw()
        if not self.picture.visible:
            return
        if self.picture_list is None:
            self.compile_picture()
        self.picture.refresh()
        glDisable(GL_LIGHTING)
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, self.picture.shown_texture_id)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glColor4f(1.0, 1.0, 1.0, 1.0)
        glMatrixMode(GL_TEXTURE)
        glPushMatrix()
        if self.picture.snapshot_running:
            glTranslatef(0.0, 1.0, 0.0)
            glScalef(1.0, -1.0, 1.0)
        glMatrixMode(GL_MODELVIEW)
        glCallList(self.picture_list)
        glMatrixMode(GL_TEXTURE)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glBindTexture(GL_TEXTURE_2D, 0)
        glDisable(GL_BLEND)
        glDisable(GL_TEXTURE_2D)
        glEnable(GL_LIGHTING)


class LeftLensStage(Stage):
    def __init__(self):
        self.blackout_duration = 8.0
        self.blackout_steps = 24
        self.zoom_duration = 6.0
        self.tunnel_fade_duration = 2.0
        self.tunnel_hold = 26.0
        super().__init__(self.blackout_duration + self.zoom_duration + self.tunnel_hold)
        self.fill_share = 1.2
        self.start_distance = 0.0
        self.close_distance = 0.0
        self.start_focus = (0.0, 0.0, 0.0)
        self.lens_focus = (0.0, 0.0, 0.0)
        self.last_time = 0.0

    def enter(self, show):
        lens = show.left_lens
        lens.picture.visible = True
        camera = show.camera
        camera.target_tilt = 0.0
        self.start_distance = camera.distance
        self.start_focus = camera.focus_point
        self.lens_focus = lens.world_center()
        self.close_distance = camera.distance_to_fill(lens.world_height(), self.fill_share)

    def update(self, show, time):
        picture = show.left_lens.picture
        blackout = self.phase(time, 0.0, self.blackout_duration)
        stepped_blackout = math.floor(blackout * self.blackout_steps) / self.blackout_steps
        picture.bars.fill_to(stepped_blackout)
        picture.tunnel_brightness = self.phase(time, self.blackout_duration, self.tunnel_fade_duration)
        if time >= self.blackout_duration:
            picture.update_tunnel((time - self.last_time) / show.playback_speed)
        self.last_time = time
        self.zoom(show.camera, self.eased(time, self.blackout_duration, self.zoom_duration))

    def zoom(self, camera, share):
        distance_ratio = self.close_distance / self.start_distance
        camera.distance = self.start_distance * distance_ratio ** share
        camera.focus_point = tuple(start + (lens - start) * share
                                   for start, lens in zip(self.start_focus, self.lens_focus))
