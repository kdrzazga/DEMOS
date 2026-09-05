import math
import os

import pygame
from OpenGL.GL import (
    GL_BLEND,
    GL_COLOR_ATTACHMENT0,
    GL_COLOR_BUFFER_BIT,
    GL_DEPTH_TEST,
    GL_FRAMEBUFFER,
    GL_LINEAR,
    GL_MODELVIEW,
    GL_NEAREST,
    GL_ONE_MINUS_SRC_ALPHA,
    GL_PROJECTION,
    GL_QUADS,
    GL_RGBA,
    GL_SRC_ALPHA,
    GL_TEXTURE_2D,
    GL_TEXTURE_MAG_FILTER,
    GL_TEXTURE_MIN_FILTER,
    GL_UNSIGNED_BYTE,
    glBegin,
    glBindFramebuffer,
    glBindTexture,
    glBlendFunc,
    glClear,
    glClearColor,
    glColor3f,
    glDisable,
    glEnable,
    glEnd,
    glFramebufferTexture2D,
    glGenFramebuffers,
    glGenTextures,
    glGetIntegerv,
    glLoadIdentity,
    glMatrixMode,
    glOrtho,
    glTexCoord2f,
    glTexImage2D,
    glTexParameteri,
    glTranslatef,
    glVertex3f,
    glViewport,
    GL_VIEWPORT,
)
from OpenGL.GLU import gluPerspective

from lib.rotator import Rotator
from demos.petscii.files.globals import Constants
from demos.petscii.files.mesh import PetsciiMesh
from demos.petscii.files.typer import Typer


class C64BaseScreen:

    START_Z = -34 * 6
    TARGET_Z = -1.5
    ZOOM_SPEED = 1.6
    FINALE_ZOOM_SPEED = 0.04
    PULSE_FAR = -2.5
    PULSE_SPEED = 0.06
    FAR_PLANE = 300.0

    HEADER2_OFFSET = 45
    HEADER3_OFFSET = 95

    def __init__(self):
        self.z = C64BaseScreen.START_Z
        self.target_z = C64BaseScreen.TARGET_Z
        self.zoom_speed = C64BaseScreen.ZOOM_SPEED
        self.pulse = False
        self._pulsing = False
        self._pulse_phase = 0.0
        self._arrived = False
        self.receding = False
        self.recede_speed = 0.0
        self.rotator = None
        self.loading = False
        self.color = list(Constants.PALETTE[11])
        self.half_width = Constants.HALF_WIDTH
        self.half_height = Constants.HALF_WIDTH * Constants.HEIGHT / Constants.WIDTH
        self.inset_w = self.half_width * 0.8
        self.inset_h = self.half_height * 0.8

        font_size = self.font_size = Constants.WIDTH // Constants.COLUMNS
        start_x = (Constants.WIDTH - len(Constants.HEADER) * font_size) // 2
        start_x2 = (Constants.WIDTH - len(Constants.HEADER2) * font_size) // 2
        self.screen_surface = pygame.Surface((Constants.WIDTH, Constants.HEIGHT))
        self.header_typer1 = Typer(0, Constants.HEADER,
                                   self.screen_surface, start_x, font_size, font_size)
        self.header_typer2 = Typer(C64BaseScreen.HEADER2_OFFSET, Constants.HEADER2,
                                   self.screen_surface, start_x2, 3*font_size, font_size)
        self.header_typer3 = Typer(C64BaseScreen.HEADER3_OFFSET, Constants.HEADER3,
                                   self.screen_surface, Constants.WIDTH*0.006, 5*font_size, font_size)
        self.texture = glGenTextures(1)

        self.mesh = PetsciiMesh(font_size)
        self.mesh_drawn = False
        self.header_start = None

        # a Bruce Lee stage revealed from the bottom, gradually replacing the
        # screen face; set with reveal_bruce_stage(), None until then
        self.bruce_stage = None
        self.bruce_origin = (0, 0)

        # a Bruce Lee sprite that drops in from above and performs his routine
        # (fall, run, kick); set with start_falling_bruce(), None until then. The
        # sprite owns its own position and animation state.
        self.falling_bruce = None

        # a static Bruce Lee pose (a BruceLee picture) stamped onto the screen
        # face as part of the scene; set with show_bruce_pose(), None until then
        self.bruce_pose = None

        self.caption_color = (255, 255, 255)
        self.caption_texture = glGenTextures(1)
        self.mesh_texture = glGenTextures(1)
        self.fbo_texture = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.fbo_texture)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, Constants.WIDTH, Constants.HEIGHT,
                     0, GL_RGBA, GL_UNSIGNED_BYTE, None)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        self.fbo = glGenFramebuffers(1)
        glBindFramebuffer(GL_FRAMEBUFFER, self.fbo)
        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D,
                               self.fbo_texture, 0)
        glBindFramebuffer(GL_FRAMEBUFFER, 0)
        self.caption_ready = False
        self.caption_start_frame = 0
        self.caption_step = 6
        self.caption_amplitude = 2

        self.captions = ("PETSCII", "3D", "DEMO")
        self.caption_index = 0
        self.mesh_caption = self.captions[0]
        self.drawn_caption = None
        self.caption_timer = 0
        self.caption_durations = (75, 220, 75)
        # captions named here sway by a fixed number of cells; any others fall back
        # to the width-derived amplitude computed in build_caption
        self.caption_amplitude_overrides = {"PETSCII": 1}

        pygame.mixer.init()
        self.wolf = self.load_sound("wolf.mp3")
        self.wolf_background = self.load_sound("wolf-background1.mp3")
        self.music_started = False

        self.header_typers = (self.header_typer1, self.header_typer2, self.header_typer3)
        # the mesh appears once every header has finished typing
        self.mesh_start_frame = max(t.start_frame + len(t.text) * t.speed
                                    for t in self.header_typers)

    def update(self, frame):
        if self.receding:
            self.z -= self.recede_speed   # zoom straight away from the camera, off-screen
            return
        if self._pulsing:
            self._pulse_phase += C64BaseScreen.PULSE_SPEED
            center = (C64BaseScreen.TARGET_Z + C64BaseScreen.PULSE_FAR) / 2
            reach = (C64BaseScreen.TARGET_Z - C64BaseScreen.PULSE_FAR) / 2
            self.z = center + reach * math.cos(self._pulse_phase)
        elif self.z < self.target_z:
            self.z = min(self.target_z, self.z + self.zoom_speed)
            if self.z >= self.target_z:
                self._arrived = True
                if self.pulse:
                    self._pulsing = True
        if frame > 20:
            self.change_color_rgb(frame, amplitude=127.5, offset=127.5)
        self.update_caption()
        if self.rotator is not None and self.at_front() and not self.rotator.finished:
            self.rotator.rotate()

    def zoom(self, magnification, speed=None):
        eye = C64BaseScreen.TARGET_Z + Constants.CAMERA_Z
        self.target_z = eye / magnification - Constants.CAMERA_Z
        self.zoom_speed = speed if speed is not None else C64BaseScreen.FINALE_ZOOM_SPEED
        self.pulse = False
        self._pulsing = False

    def zoom_to_front(self, speed=None):
        self.target_z = 0.0
        self.zoom_speed = speed if speed is not None else C64BaseScreen.FINALE_ZOOM_SPEED
        self.pulse = False
        self._pulsing = False

    def recede(self, speed):
        """Zoom the screen straight away from the camera at `speed` world units per
        frame, overriding the normal zoom until it is far off-screen."""
        self.receding = True
        self.recede_speed = speed
        self.pulse = False
        self._pulsing = False

    def at_front(self):
        return self.z >= 0.0

    def fold_to_left_wall(self, depth, total_duration, fps):
        hw, hh = self.half_width, self.half_height
        self.rotator = Rotator(
            self.screen_surface,
            destination_top_left=(-hw, hh, 0.0),
            destination_top_right=(-hw, hh, depth),
            destination_bottom_left=(-hw, -hh, 0.0),
            destination_bottom_right=(-hw, -hh, depth),
            total_duration=total_duration, fps=fps, half_width=hw)

    def fold_to_right_wall(self, depth, total_duration, fps):
        hw, hh = self.half_width, self.half_height
        self.rotator = Rotator(
            self.screen_surface,
            destination_top_left=(hw, hh, depth),
            destination_top_right=(hw, hh, 0.0),
            destination_bottom_left=(hw, -hh, depth),
            destination_bottom_right=(hw, -hh, 0.0),
            total_duration=total_duration, fps=fps, half_width=hw)

    def folded_past(self, fraction):
        return self.rotator is not None and self.rotator.progress >= fraction

    def update_caption(self):
        if not self.caption_ready:
            return
        self.caption_timer += 1
        if self.caption_timer >= self.caption_durations[self.caption_index]:
            self.caption_timer = 0
            self.caption_index = (self.caption_index + 1) % len(self.captions)
            self.mesh_caption = self.captions[self.caption_index]

    def render(self, frame):
        self._compose_texture(frame)
        self._present()

    def _compose_texture(self, frame):
        glBindFramebuffer(GL_FRAMEBUFFER, self.fbo)
        # the FBO is WIDTH x HEIGHT; match the viewport to it so the ortho content
        # fills it exactly. Otherwise it inherits the window's viewport, which in
        # fullscreen is the (larger) native resolution, and the top of the face
        # overflows the FBO and is clipped away.
        previous_viewport = glGetIntegerv(GL_VIEWPORT)
        glViewport(0, 0, Constants.WIDTH, Constants.HEIGHT)
        glDisable(GL_DEPTH_TEST)
        glClearColor(0.0, 0.0, 0.0, 1.0)
        glClear(GL_COLOR_BUFFER_BIT)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(-self.half_width, self.half_width, -self.half_height, self.half_height, -1.0, 1.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

        glDisable(GL_TEXTURE_2D)
        glColor3f(*self.gl_color())
        glBegin(GL_QUADS)
        glVertex3f(-self.half_width, self.half_height, 0.0)
        glVertex3f(self.half_width, self.half_height, 0.0)
        glVertex3f(self.half_width, -self.half_height, 0.0)
        glVertex3f(-self.half_width, -self.half_height, 0.0)
        glEnd()

        if not self.loading:
            self.draw_background()
            if self.arrived():
                self.begin_headers(frame)
                self.start_music()
                self.draw_header(frame)
                self.draw_mesh(frame)

        glBindFramebuffer(GL_FRAMEBUFFER, 0)
        glViewport(*previous_viewport)
        glEnable(GL_DEPTH_TEST)

    def _present(self):
        glEnable(GL_TEXTURE_2D)
        self._begin_3d()
        glColor3f(1.0, 1.0, 1.0)
        glBindTexture(GL_TEXTURE_2D, self.fbo_texture)
        if self.rotator is None:
            self._draw_screen_quad()
        else:
            self._draw_rotated_screen_quad()

    def _draw_screen_quad(self):
        glBegin(GL_QUADS)
        glTexCoord2f(0, 1); glVertex3f(-self.half_width, self.half_height, self.z)
        glTexCoord2f(1, 1); glVertex3f(self.half_width, self.half_height, self.z)
        glTexCoord2f(1, 0); glVertex3f(self.half_width, -self.half_height, self.z)
        glTexCoord2f(0, 0); glVertex3f(-self.half_width, -self.half_height, self.z)
        glEnd()

    def _draw_rotated_screen_quad(self):
        front_bias = 0.05
        texture_coords = ((0, 1), (1, 1), (1, 0), (0, 0))
        glBegin(GL_QUADS)
        for corner, (u, v) in zip(self.rotator.current_vertices(), texture_coords):
            glTexCoord2f(u, v)
            glVertex3f(corner.x, corner.y, corner.z + self.z + front_bias)
        glEnd()

    def draw_mesh(self, frame):
        pass

    def arrived(self):
        return self._arrived

    def header_written(self, frame):
        return self.header_start is not None and frame >= self.mesh_start_frame

    def begin_headers(self, frame):
        if self.header_start is not None:
            return
        self.header_start = frame
        self.header_typer1.start_frame = frame
        self.header_typer2.start_frame = frame + C64BaseScreen.HEADER2_OFFSET
        self.header_typer3.start_frame = frame + C64BaseScreen.HEADER3_OFFSET
        self.mesh_start_frame = max(t.start_frame + len(t.text) * t.speed
                                    for t in self.header_typers)

    def _begin_3d(self):
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(Constants.FOV, Constants.WIDTH / Constants.HEIGHT, 0.1,
                       C64BaseScreen.FAR_PLANE)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glTranslatef(0.0, 0.0, Constants.CAMERA_Z)

    def load_sound(self, filename):
        path = os.path.join(os.path.dirname(__file__), "resources", filename)
        return pygame.mixer.Sound(path)

    def start_music(self):
        if self.music_started:
            return
        self.wolf.play()
        self.wolf_background.play()
        self.music_started = True

    def gl_color(self):
        return tuple(channel / 255 for channel in self.color)

    def change_color_rgb(self, frame, amplitude, offset):
        t = (frame - 20) / 6
        r = int(amplitude * math.sin(t) + offset)
        g = int(amplitude * math.sin(t + 2 * math.pi / 3) + offset)
        b = int(amplitude * math.sin(t + 4 * math.pi / 3) + offset)
        r = max(0, min(255, r))
        g = max(0, min(255, g))
        b = max(0, min(255, b))
        self.color = r, g, b

    def draw_background(self, color=(0, 0, 0)):
        glColor3f(*color)
        z = 0.0
        glBegin(GL_QUADS)
        glVertex3f(-self.inset_w, self.inset_h, z)
        glVertex3f(self.inset_w, self.inset_h, z)
        glVertex3f(self.inset_w, -self.inset_h, z)
        glVertex3f(-self.inset_w, -self.inset_h, z)
        glEnd()

    def reveal_bruce_stage(self, stage, surface_size):
        """Start growing a Bruce Lee stage up from the bottom of the screen face,
        centred horizontally and anchored to the bottom of screen_surface."""
        stage.render_progress = 0
        stage_width, stage_height = stage.size()
        surface_width, surface_height = surface_size
        self.bruce_origin = ((surface_width - stage_width) // 2,
                             surface_height - stage_height)
        self.bruce_stage = stage

    def draw_bruce_stage(self):
        """Advance the bottom-up reveal onto screen_surface: light-gray (colour 15)
        fills the band it has reached, the stage is drawn over that, and everything
        above the reveal line is left untouched."""
        if self.bruce_stage is None:
            return
        self.bruce_stage.advance_reveal()
        top_row = self.bruce_stage.revealed_top_row()
        if top_row is None:
            return
        cell_height = self.bruce_stage.font(self.bruce_stage.char_size).size("W")[1]
        top_y = max(0, self.bruce_origin[1] + top_row * cell_height)
        self.screen_surface.fill(Constants.PALETTE[15],
                                 pygame.Rect(0, top_y, Constants.WIDTH, Constants.HEIGHT - top_y))
        self.bruce_stage.draw_from_bottom(self.screen_surface, origin=self.bruce_origin)

    def start_falling_bruce(self, bruce):
        """Hand the screen a Bruce sprite and start his drop-in; the sprite drives
        its own fall, run and kick from there."""
        bruce.start_fall()
        self.falling_bruce = bruce

    def draw_falling_bruce(self):
        """Advance the Bruce sprite by one frame and draw him onto screen_surface,
        on top of whatever is already there."""
        if self.falling_bruce is None:
            return
        self.falling_bruce.update()
        self.falling_bruce.render_at_origin(self.screen_surface)

    def show_bruce_pose(self, bruce):
        """Stamp a static Bruce Lee pose (a BruceLee picture) onto this screen's
        face as part of the scene, aligned with the stage already revealed on it."""
        self.bruce_pose = bruce

    def draw_bruce_pose(self):
        """Draw the static Bruce pose over the stage -- only its non-blank cells,
        at the same origin the stage sits at, so it lands on the stage's grid."""
        if self.bruce_pose is None:
            return
        self.bruce_pose.render(self.screen_surface, transparent_space=True,
                               origin=self.bruce_origin)

    def bruce_reveal_top_y(self):
        """World-space y of the reveal front on this screen face, or None when no
        stage is growing -- used to hide captions the rising stage has reached."""
        if self.bruce_stage is None:
            return None
        top_row = self.bruce_stage.revealed_top_row()
        if top_row is None:
            return None
        cell_height = self.bruce_stage.font(self.bruce_stage.char_size).size("W")[1]
        top_y = self.bruce_origin[1] + top_row * cell_height
        return self.inset_h * (1 - 2 * top_y / Constants.HEIGHT)

    def draw_header(self, frame):
        for typer in self.header_typers:
            typer.type(frame)

        self.draw_bruce_stage()
        self.draw_falling_bruce()
        self.draw_bruce_pose()
        # the stage carries its own colours; drop the pulsing face tint over it
        face_color = (1.0, 1.0, 1.0) if self.bruce_stage is not None else self.gl_color()
        self._upload(self.screen_surface)
        z = 0.0
        glEnable(GL_TEXTURE_2D)
        glColor3f(*face_color)
        glBegin(GL_QUADS)
        glTexCoord2f(0, 0); glVertex3f(-self.inset_w, self.inset_h, z)
        glTexCoord2f(1, 0); glVertex3f(self.inset_w, self.inset_h, z)
        glTexCoord2f(1, 1); glVertex3f(self.inset_w, -self.inset_h, z)
        glTexCoord2f(0, 1); glVertex3f(-self.inset_w, -self.inset_h, z)
        glEnd()

    def draw_layer(self, texture, inset_w, inset_h, z, color, x_offset=0.0):
        glBindTexture(GL_TEXTURE_2D, texture)
        glColor3f(*color)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        left = -inset_w + x_offset
        right = inset_w + x_offset
        glBegin(GL_QUADS)
        glTexCoord2f(0, 0); glVertex3f(left, inset_h, z)
        glTexCoord2f(1, 0); glVertex3f(right, inset_h, z)
        glTexCoord2f(1, 1); glVertex3f(right, -inset_h, z)
        glTexCoord2f(0, 1); glVertex3f(left, -inset_h, z)
        glEnd()
        glDisable(GL_BLEND)

    def caption_offset(self, frames, amplitude):
        steps = frames // self.caption_step
        if steps < amplitude:
            return -steps
        steps -= amplitude
        period = 4 * amplitude
        phase = steps % period
        if phase < 2 * amplitude:
            return -amplitude + phase
        return amplitude - (phase - 2 * amplitude)

    def _upload(self, surface, texture=None):
        if texture is None:
            texture = self.texture
        data = pygame.image.tobytes(surface, "RGBA")
        glBindTexture(GL_TEXTURE_2D, texture)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, surface.get_width(), surface.get_height(),
                     0, GL_RGBA, GL_UNSIGNED_BYTE, data)
