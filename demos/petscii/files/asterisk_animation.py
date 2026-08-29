import math
import random

import pygame
from pygame.locals import KEYDOWN, K_ESCAPE, QUIT
from OpenGL.GL import (
    GL_BLEND,
    GL_COLOR_BUFFER_BIT,
    GL_DEPTH_BUFFER_BIT,
    GL_DEPTH_TEST,
    GL_LINEAR,
    GL_MODELVIEW,
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
    glBindTexture,
    glBlendFunc,
    glClear,
    glColor4f,
    glDisable,
    glEnable,
    glEnd,
    glGenTextures,
    glLoadIdentity,
    glMatrixMode,
    glOrtho,
    glPopMatrix,
    glPushMatrix,
    glRotatef,
    glTexCoord2f,
    glTexImage2D,
    glTexParameteri,
    glTranslatef,
    glVertex2f,
)

from demos.petscii.files.globals import Constants


class _Speck:
    """One asterisk in the trailing swarm: a screen position, a depth (which sets
    its size) and a horizontal speed in pixels per frame."""

    def __init__(self, x, y, z, speed):
        self.x = x
        self.y = y
        self.z = z
        self.speed = speed


class AsteriskAnimation:
    """A single C64 asterisk that flies in from the right, zooms to the front and
    sways, spirals a few times, then exits to the left trailing a swarm of 200.

    The world is drawn in plain screen pixels (top-left origin, y down). Depth is
    faked with a `z` value that only scales the glyph: the on-screen height is
    ``front_height / z``, so **z = 1 is right at the front (largest), and larger z
    is farther away (smaller)** -- matching the z=10 (far) / z=3 (mid) / z=1
    (front) values the choreography uses.

    The four phase methods each run their own frame loop and return when that
    phase is done; :meth:`animate` plays them in order. The class draws into an
    OpenGL context that already exists (see ``test/asterisk_test.py`` for a
    standalone runner that opens the window first).
    """

    ASTERISK = ord("*")   # PETSCII 0x2A; drawn as chr(FONT_BASE + 0x2A)

    def __init__(self, width=Constants.WIDTH, height=Constants.HEIGHT,
                 fps=Constants.FPS, glyph_pixels=220):
        self.width = width
        self.height = height
        self.fps = fps

        # --- depth (z) -> size ------------------------------------------------
        self.z_far = 10.0      # entrance depth: small, far to the right
        self.z_front = 1.0     # the very front: largest
        self.z_mid = 3.0       # resting depth after the zoom
        self.front_height = 0.8 * height   # glyph height in pixels at z = 1

        # --- where the asterisk lives ----------------------------------------
        self.center_x = width / 2
        self.center_y = height / 2
        self.entrance_stop_x = width * 0.66

        # --- per-phase timing / shape (instance config, easy to nudge) -------
        self.entrance_seconds = 1.3
        self.zoom_in_seconds = 1.1
        self.sway_seconds = 1.6
        self.sway_cycles = 2           # "sways couple times"
        self.sway_degrees = 18.0       # peak tilt of each sway
        self.zoom_out_seconds = 1.1
        self.spiral_seconds = 2.4
        self.spiral_turns = 3          # "a few spiral moves"
        self.spiral_radius = 0.30 * height
        self.spiral_spin = 0.4         # how much the glyph itself twists along the path
        self.exit_seconds = 3.4        # leader's glide off the left edge

        # --- the trailing swarm ----------------------------------------------
        self.swarm_count = 1750
        self.swarm_seconds = 2.4       # roughly how long a speck takes to cross
        self.swarm_depth_range = (27.0, 130.0)   # deeper = smaller, farther specks
        self.swarm_speed_jitter = (0.7, 1.5)
        self.swarm_lead_stagger = 2.8  # specks start up to this*width off the right edge
        self.swarm_to_right = False    # False: swarm streams LEFT, chasing the leader
        self.swarm = []

        # the glyph texture must exist before any _half_width() call, since that
        # reads self.aspect
        self.aspect, self.texture = self._build_glyph_texture(glyph_pixels)

        # --- live state ------------------------------------------------------
        self.x = width + self._half_width(self.z_far)
        self.y = self.center_y
        self.z = self.z_far
        self.angle = 0.0
        self.leader_visible = True

        self.running = True
        self.clock = pygame.time.Clock()

    # ---- public choreography -------------------------------------------------
    def entrance_from_right(self):
        """Glide the asterisk in from just off the right edge (y centered, far away
        at z = 10) until it reaches x = width * 0.66, then return."""
        self.y = self.center_y
        self.z = self.z_far
        self.angle = 0.0
        self.leader_visible = True

        x_start = self.width + self._half_width(self.z_far)
        x_stop = self.entrance_stop_x
        for progress in self._phase(self.entrance_seconds):
            self.x = self._lerp(x_start, x_stop, self._ease_out(progress))
            if not self._present():
                return
        self.x = x_stop

    def zoom(self):
        """Zoom to the very front (z = 1), sway a couple of times, then zoom back
        to z = 3 while sliding to the centre of the screen."""
        # in: z from wherever we are (10) to the front (1), holding position
        z_from = self.z
        for progress in self._phase(self.zoom_in_seconds):
            self.z = self._lerp(z_from, self.z_front, self._smoothstep(progress))
            if not self._present():
                return
        self.z = self.z_front

        # sway: tilt left/right a couple of full cycles at the front
        for progress in self._phase(self.sway_seconds):
            self.angle = self.sway_degrees * math.sin(2 * math.pi * self.sway_cycles * progress)
            if not self._present():
                return
        self.angle = 0.0

        # out: back to z = 3 and home to the screen centre
        x_from = self.x
        for progress in self._phase(self.zoom_out_seconds):
            eased = self._smoothstep(progress)
            self.z = self._lerp(self.z_front, self.z_mid, eased)
            self.x = self._lerp(x_from, self.center_x, eased)
            self.y = self.center_y
            if not self._present():
                return
        self.x, self.y, self.z = self.center_x, self.center_y, self.z_mid

    def spiral(self):
        """Trace a few spiral loops around the screen centre -- the radius swells
        out and back so it starts and ends on the centre, with a slight twist of
        the glyph and a gentle depth pulse for life."""
        for progress in self._phase(self.spiral_seconds):
            radius = self.spiral_radius * math.sin(math.pi * progress)   # 0 -> max -> 0
            sweep = 2 * math.pi * self.spiral_turns * progress
            self.x = self.center_x + radius * math.cos(sweep)
            self.y = self.center_y + radius * math.sin(sweep)
            self.z = self.z_mid + 0.6 * math.sin(2 * math.pi * progress)
            self.angle = math.degrees(sweep) * self.spiral_spin
            if not self._present():
                return
        self.x, self.y, self.z, self.angle = self.center_x, self.center_y, self.z_mid, 0.0

    def exit(self):
        """Send the asterisk off through the left edge, and launch a swarm of 200
        asterisks in from the right edge that streams after it (see
        ``swarm_to_right`` to reverse the swarm's direction)."""
        self._spawn_swarm()

        lead_from_x = self.x
        lead_to_x = -self._half_width(self.z) - 10   # fully past the left edge
        lead_frames = max(1, round(self.exit_seconds * self.fps))

        # run until the slowest speck has actually cleared (plus a second of
        # margin), so a wide/deep swarm is never cut off early
        safety = int(max(lead_frames, self._swarm_clear_frames())) + self.fps
        frame = 0
        while self.running and frame < safety:
            if self.leader_visible:
                eased = self._ease_in(min(1.0, frame / lead_frames))
                self.x = self._lerp(lead_from_x, lead_to_x, eased)
                if self.x < -self._half_width(self.z):
                    self.leader_visible = False

            for speck in self.swarm:
                speck.x += -speck.speed if not self.swarm_to_right else speck.speed

            if not self._present():
                return
            frame += 1
            if not self.leader_visible and self._swarm_gone():
                break

    def animate(self):
        """Play the whole thing: entrance, zoom, spiral, exit."""
        self._reset()
        for phase in (self.entrance_from_right, self.zoom, self.spiral, self.exit):
            if not self.running:
                return
            phase()

    # ---- frame-driven access (for embedding in another loop) ----------------
    def draw(self):
        """Render the current state: the swarm first, then the leading asterisk on
        top. Uses an orthographic pixel projection and additive-free alpha blend."""
        self._setup_projection()
        glEnable(GL_TEXTURE_2D)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glDisable(GL_DEPTH_TEST)
        glBindTexture(GL_TEXTURE_2D, self.texture)

        for speck in self.swarm:
            height_px = self.front_height / speck.z
            alpha = self._clamp(1.25 - speck.z * 0.08, 0.35, 1.0)   # fade the far ones
            self._blit(speck.x, speck.y, height_px, 0.0, alpha)

        if self.leader_visible:
            self._blit(self.x, self.y, self.front_height / self.z, self.angle, 1.0)

        glDisable(GL_BLEND)

    # ---- internals ----------------------------------------------------------
    def _reset(self):
        self.running = True
        self.swarm = []
        self.leader_visible = True
        self.x = self.width + self._half_width(self.z_far)
        self.y = self.center_y
        self.z = self.z_far
        self.angle = 0.0

    def _phase(self, seconds):
        """Yield a 0..1 progress value for each frame of a fixed-length phase."""
        frames = max(1, round(seconds * self.fps))
        for frame in range(1, frames + 1):
            yield frame / frames

    def _present(self):
        """Pump events, draw one frame and pace the clock. Returns False if the
        user asked to quit, so the phase loops can bail out."""
        self._pump_events()
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        self.draw()
        pygame.display.flip()
        self.clock.tick(self.fps)
        return self.running

    def _pump_events(self):
        for event in pygame.event.get():
            if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
                self.running = False

    def _spawn_swarm(self):
        """Populate the swarm just off the right edge, each speck at a random row,
        depth and speed, and staggered back so they trail in rather than arrive as
        a wall."""
        low, high = self.swarm_depth_range
        cross = self.width + 2 * self._half_width(low)   # distance a near speck travels
        base_speed = cross / (self.swarm_seconds * self.fps)
        self.swarm = []
        for _ in range(self.swarm_count):
            z = random.uniform(low, high)
            x = self.width + self._half_width(z) + random.uniform(
                0.0, self.swarm_lead_stagger * self.width)
            y = random.uniform(0.0, self.height)
            speed = base_speed * random.uniform(*self.swarm_speed_jitter)
            self.swarm.append(_Speck(x, y, z, speed))

    def _swarm_gone(self):
        """True once every speck has cleared the edge it is heading for."""
        if self.swarm_to_right:
            return all(speck.x - self._half_width(speck.z) > self.width for speck in self.swarm)
        return all(speck.x + self._half_width(speck.z) < 0 for speck in self.swarm)

    def _swarm_clear_frames(self):
        """How many frames the slowest speck needs to reach the edge it heads for."""
        worst = 0.0
        for speck in self.swarm:
            if self.swarm_to_right:
                distance = self.width - speck.x + self._half_width(speck.z)
            else:
                distance = speck.x + self._half_width(speck.z)
            worst = max(worst, distance / speck.speed)
        return worst

    def _half_width(self, z):
        return 0.5 * self.aspect * self.front_height / z

    def _setup_projection(self):
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0, self.width, self.height, 0, -1, 1)   # pixels, top-left origin
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

    def _blit(self, cx, cy, height_px, angle, alpha):
        half_h = height_px / 2
        half_w = half_h * self.aspect
        glPushMatrix()
        glTranslatef(cx, cy, 0.0)
        if angle:
            glRotatef(angle, 0.0, 0.0, 1.0)
        glColor4f(1.0, 1.0, 1.0, alpha)
        glBegin(GL_QUADS)
        glTexCoord2f(0, 0); glVertex2f(-half_w, -half_h)
        glTexCoord2f(1, 0); glVertex2f(half_w, -half_h)
        glTexCoord2f(1, 1); glVertex2f(half_w, half_h)
        glTexCoord2f(0, 1); glVertex2f(-half_w, half_h)
        glEnd()
        glPopMatrix()

    def _build_glyph_texture(self, glyph_pixels):
        """Render the C64 asterisk once to a transparent surface and upload it as a
        texture. Returns (aspect, texture_id)."""
        pygame.font.init()
        font = pygame.font.Font(Constants.FONT_PATH, glyph_pixels)
        surface = font.render(chr(Constants.FONT_BASE + self.ASTERISK), True, (255, 255, 255))
        data = pygame.image.tobytes(surface, "RGBA")
        width, height = surface.get_size()

        texture = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, texture)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0,
                     GL_RGBA, GL_UNSIGNED_BYTE, data)
        return width / height, texture

    # ---- small maths helpers ------------------------------------------------
    @staticmethod
    def _lerp(a, b, t):
        return a + (b - a) * t

    @staticmethod
    def _ease_out(t):
        return 1.0 - (1.0 - t) ** 3

    @staticmethod
    def _ease_in(t):
        return t * t * t

    @staticmethod
    def _smoothstep(t):
        return t * t * (3.0 - 2.0 * t)

    @staticmethod
    def _clamp(value, low, high):
        return max(low, min(high, value))
