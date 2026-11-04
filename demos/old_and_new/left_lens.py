import math
import os
import random

import pygame
from OpenGL.GL import *

from lib import Globals

os.environ["PATH"] += os.pathsep
from lib import Globals
from lib.amiga_ball import AmigaBall
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


class AmigaBallTunnel(OpenGlTunnel):
    def __init__(self):
        super().__init__()
        self.ball = AmigaBall(radius=0.8)
        self.ball_delay = 4.0
        self.ball_position = (0.0, 0.0, -6.0)
        self.ball_travel = 10.0
        self.ball_trip_duration = 2.0
        self.ball_trips = 3
        self.ball_inside = True

    def update(self, seconds):
        super().update(seconds)
        self.ball.update(seconds)

    def ball_height_share(self):
        ball_depth = -self.ball_position[2]
        return self.ball.radius / (ball_depth * math.tan(math.radians(self.field_of_view / 2.0)))

    def draw_inside(self):
        if not self.ball_inside or self.time < self.ball_delay:
            return
        glEnable(GL_DEPTH_TEST)
        glPushMatrix()
        x, y, z = self.ball_position
        glTranslatef(x, y, z - self.ball_distance())
        self.ball.render()
        glPopMatrix()

    def ball_distance(self):
        moving_time = self.time - self.ball_delay
        if moving_time >= self.ball_trips * self.ball_trip_duration:
            return 0.0
        return self.ball_travel * (1.0 - math.cos(2.0 * math.pi * moving_time / self.ball_trip_duration)) / 2.0


class TunnelSnapshot:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.tunnel = AmigaBallTunnel()
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
        print("Tunnel in left lens " + str(Globals.get_duration()))

    def update_tunnel(self, seconds):
        if self.snapshot_running:
            self.tunnel_snapshot.update(seconds)
            return
        if self.tunnel is None:
            self.start_tunnel()
        self.tunnel.update()
        self.snapshot_running = self.tunnel.is_filled

    @property
    def opengl_tunnel(self):
        return self.tunnel_snapshot.tunnel

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
        self.ball_escaping = False
        self.escaping_ball_position = (0.0, 0.0, 0.0)
        self.escaping_ball_radius = 0.0

    def draw_escaping_ball(self):
        if not self.ball_escaping:
            return
        ball = self.picture.opengl_tunnel.ball
        scale = self.escaping_ball_radius / ball.radius
        glPushAttrib(GL_ENABLE_BIT | GL_CURRENT_BIT)
        glDisable(GL_LIGHTING)
        glEnable(GL_DEPTH_TEST)
        glPushMatrix()
        glTranslatef(*self.escaping_ball_position)
        glScalef(scale, scale, scale)
        ball.render()
        glPopMatrix()
        glPopAttrib()

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
        self.zoom_out_start = 10.0
        self.zoom_out_duration = 3.0
        self.escape_start = 12.0
        self.escape_duration = 2.0
        self.dive_start = 14.5
        self.dive_duration = 3.0
        self.final_travel = 4.0
        self.tunnel_end = self.dive_start + self.dive_duration + self.final_travel
        self.escape_miss_to_left = 0.2
        self.escape_overshoot = 1.3
        self.start_distance = 0.0
        self.close_distance = 0.0
        self.start_focus = (0.0, 0.0, 0.0)
        self.lens_focus = (0.0, 0.0, 0.0)
        self.last_time = 0.0
        self.second_entry_announced = False

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
        tunnel_time = picture.opengl_tunnel.time
        if picture.snapshot_running:
            self.duration = time + (self.tunnel_end - tunnel_time) * show.playback_speed
        zoom_in = self.eased(time, self.blackout_duration, self.zoom_duration)
        zoom_out = self.eased(tunnel_time, self.zoom_out_start, self.zoom_out_duration)
        dive = self.eased(tunnel_time, self.dive_start, self.dive_duration)
        if tunnel_time >= self.dive_start and not self.second_entry_announced:
            self.second_entry_announced = True
            print('Second entry to the tunnel ' + str(Globals.get_duration()))
        self.zoom(show.camera, zoom_in * (1.0 - zoom_out + dive))
        self.move_escaping_ball(show.left_lens, tunnel_time)

    def move_escaping_ball(self, lens, tunnel_time):
        tunnel = lens.picture.opengl_tunnel
        if tunnel_time < self.escape_start:
            return
        tunnel.ball_inside = False
        progress = self.phase(tunnel_time, self.escape_start, self.escape_duration)
        lens.ball_escaping = progress < 1.0
        radius = tunnel.ball_height_share() * lens.world_height() / 2.0
        start_x, start_y, start_z = self.lens_focus
        start = (start_x, start_y, start_z + radius)
        focus_x, focus_y, focus_z = self.start_focus
        passing_point = (focus_x - self.escape_miss_to_left * self.start_distance,
                         focus_y,
                         focus_z + self.start_distance)
        travel = self.escape_overshoot * progress
        lens.escaping_ball_radius = radius
        lens.escaping_ball_position = tuple(begin + (passing - begin) * travel
                                            for begin, passing in zip(start, passing_point))

    def zoom(self, camera, share):
        distance_ratio = self.close_distance / self.start_distance
        camera.distance = self.start_distance * distance_ratio ** share
        camera.focus_point = tuple(start + (lens - start) * share
                                   for start, lens in zip(self.start_focus, self.lens_focus))
