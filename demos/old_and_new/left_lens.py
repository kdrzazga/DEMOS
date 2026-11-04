import math
import os
import random

import pygame
from OpenGL.GL import *
from OpenGL.GLU import gluLookAt

os.environ["PATH"] += os.pathsep
from lib import Globals
from lib.amiga.amiga_ball import AmigaBall
from lib.amiga.amos import Amos
from lib.tunnel import OpenGlTunnel, SurfaceTunnelEffect
from demos.old_and_new.actors import BorderColoredLens
from demos.old_and_new.stages import Stage, smooth


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
        self.cruise_speed = self.speed
        self.boot_screen_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
            os.path.abspath(__file__)))), "lib", "resources", "amiga-500-bootscreen.jpg")
        self.boot_screen_texture = None
        self.boot_screen_aspect = 1.0
        self.boot_screen_half_height = 0.6
        self.boot_screen_start = 0.0
        self.boot_screen_approach_duration = 1.5
        self.boot_screen_zoom_duration = 1.5
        self.boot_screen_spin_duration = 1.5
        self.boot_screen_exit_duration = 1.0
        self.boot_screen_duration = (self.boot_screen_approach_duration + self.boot_screen_zoom_duration
                                     + self.boot_screen_spin_duration + self.boot_screen_exit_duration)
        self.boot_screen_far_depth = -30.0
        self.boot_screen_hover_depth = -5.0
        self.boot_screen_behind_camera_depth = 1.0
        self.boot_screen_zoom_amount = 0.5
        self.amos = None
        self.amos_texture = None
        self.amos_arrival = math.inf
        self.amos_brake_duration = 1.5
        self.amos_stop_depth = -5.0
        self.amos_close_depth = -3.1
        self.amos_sway_settle_duration = 2.5
        self.amos_wall_fade_duration = 2.5
        self.amos_zoom_duration = 2.0
        self.amos_typing_pause = 1.0
        self.amos_code_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
            os.path.abspath(__file__)))), "lib", "resources", "amos-code.txt")
        self.amos_typing = False
        self.amos_typed_announced = False
        self.amos_mouse_route = ["Run Other", "Edit Other", "Insert", "Fold/Unfold", "Line Insert",
                                 "Search Menu", "Blocks Menu", "Indent", "Test"]

    def update(self, seconds):
        self.speed = self.cruise_speed * min(max((self.amos_arrival - self.time) / self.amos_brake_duration, 0.0), 1.0)
        super().update(seconds)
        self.ball.update(seconds)
        self.direct_amos()
        if self.amos is not None:
            self.amos.update(seconds)

    def since_amos_arrival(self):
        return self.time - self.amos_arrival

    def amos_typing_start(self):
        return self.amos_sway_settle_duration + self.amos_zoom_duration + self.amos_typing_pause

    def direct_amos(self):
        if self.amos is None or self.since_amos_arrival() < self.amos_typing_start():
            return
        if not self.amos_typing:
            self.amos_typing = True
            self.amos.type_code(self.amos_code_path)
        if not self.amos.is_typing() and not self.amos_typed_announced:
            self.amos_typed_announced = True
            print('AMOS program typed in ' + str(Globals.get_duration()))
        mouse_cursor = self.amos.mouse_cursor
        if self.amos_mouse_route and not mouse_cursor.is_moving():
            button = self.amos_menu_button(self.amos_mouse_route.pop(0))
            mouse_cursor.move_to(*button.rect.center)

    def amos_menu_button(self, label):
        return next(button for button in self.amos.screen.top_menu.buttons if button.label == label)

    def wall_brightness(self):
        fade_out = smooth(self.share_of(self.since_amos_arrival(), 0.0, self.amos_wall_fade_duration))
        return super().wall_brightness() * (1.0 - fade_out)

    def sway_share(self):
        return 1.0 - smooth(self.share_of(self.since_amos_arrival(), 0.0, self.amos_sway_settle_duration))

    def amos_zoom_share(self):
        return smooth(self.share_of(self.since_amos_arrival(), self.amos_sway_settle_duration,
                                    self.amos_zoom_duration))

    def look(self):
        sway = self.sway_share()
        camera_x = 0.35 * math.sin(self.time * 0.9) * sway
        camera_y = 0.2 * math.sin(self.time * 1.3) * sway
        camera_z = (self.amos_stop_depth - self.amos_close_depth) * self.amos_zoom_share()
        up_x = 0.12 * math.sin(self.time * 0.7) * sway
        up_length = math.hypot(up_x, 1.0)
        gluLookAt(camera_x, camera_y, camera_z, camera_x, camera_y, camera_z - 1.0,
                  up_x / up_length, 1.0 / up_length, 0.0)

    def ball_height_share(self):
        ball_depth = -self.ball_position[2]
        return self.ball.radius / (ball_depth * math.tan(math.radians(self.field_of_view / 2.0)))

    def draw_inside(self):
        self.draw_ball()
        glMatrixMode(GL_TEXTURE)
        glPushMatrix()
        glLoadIdentity()
        glMatrixMode(GL_MODELVIEW)
        glDisable(GL_DEPTH_TEST)
        self.draw_amos()
        self.draw_boot_screen()
        glMatrixMode(GL_TEXTURE)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)

    def draw_boot_screen(self):
        elapsed = self.time - self.boot_screen_start
        if elapsed < 0.0 or elapsed > self.boot_screen_duration:
            return
        if self.boot_screen_texture is None:
            boot_screen = pygame.image.load(self.boot_screen_path)
            self.boot_screen_aspect = boot_screen.get_width() / boot_screen.get_height()
            self.boot_screen_texture = self.picture_texture(boot_screen)
        zoom_start = self.boot_screen_approach_duration
        spin_start = zoom_start + self.boot_screen_zoom_duration
        exit_start = spin_start + self.boot_screen_spin_duration
        approach = smooth(self.share_of(elapsed, 0.0, self.boot_screen_approach_duration))
        zoom = self.share_of(elapsed, zoom_start, self.boot_screen_zoom_duration)
        spin = smooth(self.share_of(elapsed, spin_start, self.boot_screen_spin_duration))
        leaving = self.share_of(elapsed, exit_start, self.boot_screen_exit_duration)
        depth = (self.boot_screen_far_depth
                 + (self.boot_screen_hover_depth - self.boot_screen_far_depth) * approach
                 + (self.boot_screen_behind_camera_depth - self.boot_screen_hover_depth) * leaving * leaving)
        scale = 1.0 + self.boot_screen_zoom_amount * math.sin(2.0 * math.pi * zoom)
        half_height = self.boot_screen_half_height * scale
        glPushMatrix()
        glTranslatef(0.0, 0.0, depth)
        glRotatef(360.0 * spin, 0.0, 0.0, 1.0)
        self.draw_picture(self.boot_screen_texture, half_height * self.boot_screen_aspect, half_height)
        glPopMatrix()

    def draw_amos(self):
        remaining = self.amos_remaining_distance()
        if remaining > self.length + self.amos_stop_depth:
            return
        if self.amos is None:
            self.amos = Amos()
            self.amos_texture = self.picture_texture(self.amos.surface)
        self.upload_picture(self.amos_texture, self.amos.surface)
        glPushMatrix()
        glTranslatef(0.0, 0.0, self.amos_stop_depth - remaining)
        self.draw_picture(self.amos_texture, self.half_width, self.half_height)
        glPopMatrix()

    def amos_remaining_distance(self):
        until_arrival = max(self.amos_arrival - self.time, 0.0)
        if until_arrival <= self.amos_brake_duration:
            return self.cruise_speed * until_arrival * until_arrival / (2.0 * self.amos_brake_duration)
        return self.cruise_speed * (until_arrival - self.amos_brake_duration / 2.0)

    def share_of(self, elapsed, start, duration):
        return min(max((elapsed - start) / duration, 0.0), 1.0)

    def picture_texture(self, surface):
        texture = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, texture)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
        width, height = surface.get_size()
        glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE,
                     pygame.image.tobytes(surface, "RGBA", False))
        glBindTexture(GL_TEXTURE_2D, 0)
        return texture

    def upload_picture(self, texture, surface):
        width, height = surface.get_size()
        glBindTexture(GL_TEXTURE_2D, texture)
        glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
        glTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0, width, height, GL_RGBA, GL_UNSIGNED_BYTE,
                        pygame.image.tobytes(surface, "RGBA", False))
        glBindTexture(GL_TEXTURE_2D, 0)

    def draw_picture(self, texture, half_width, half_height):
        glEnable(GL_TEXTURE_2D)
        glColor4f(1.0, 1.0, 1.0, 1.0)
        glBindTexture(GL_TEXTURE_2D, texture)
        glBegin(GL_QUADS)
        glTexCoord2f(0.0, 1.0)
        glVertex3f(-half_width, -half_height, 0.0)
        glTexCoord2f(1.0, 1.0)
        glVertex3f(half_width, -half_height, 0.0)
        glTexCoord2f(1.0, 0.0)
        glVertex3f(half_width, half_height, 0.0)
        glTexCoord2f(0.0, 0.0)
        glVertex3f(-half_width, half_height, 0.0)
        glEnd()
        glBindTexture(GL_TEXTURE_2D, 0)

    def draw_ball(self):
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
        self.boot_screen_delay = 3.0
        self.travel_to_amos = 4.0
        self.amos_hold = 12.0
        self.tunnel_end = 0.0
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
        tunnel = lens.picture.opengl_tunnel
        tunnel.boot_screen_start = self.dive_start + self.boot_screen_delay
        tunnel.amos_arrival = tunnel.boot_screen_start + tunnel.boot_screen_duration + self.travel_to_amos
        self.tunnel_end = tunnel.amos_arrival + self.amos_hold

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
