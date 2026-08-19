import math

import pygame
from OpenGL.GL import (
    GL_BLEND,
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
    glBindTexture,
    glBlendFunc,
    glColor3f,
    glDepthMask,
    glDisable,
    glEnable,
    glEnd,
    glGenTextures,
    glLoadIdentity,
    glMatrixMode,
    glRotatef,
    glTexCoord2f,
    glTexImage2D,
    glTexParameteri,
    glTranslatef,
    glVertex3f,
)
from OpenGL.GLU import gluPerspective

from demos.petscii.files.globals import Constants
from demos.petscii.files.petscii.asian import Asian


class AsianAnimation:

    LEAP = 0
    FINISH = 1
    SPEAK = 2
    FLY = 3
    DONE = 4
    APPROACH = 5

    FAR_PLANE = 300.0

    def __init__(self):
        self.asian = Asian(16)
        width, height = self.asian.size()
        self.surface = pygame.Surface((width, height), pygame.SRCALPHA)
        self.texture = glGenTextures(1)

        self.half_width = Constants.HALF_WIDTH * 0.5
        self.half_height = self.half_width * height / width
        self.z_behind = -8.0
        self.z_front = 1.2
        self.peak_y = 2.6
        self.leap_frames = int(Constants.FPS * 1.6)
        self.land_z = self.z_front
        self.land_y = 0.0
        self.leap_peak = self.peak_y
        self.leap_from_z = self.z_behind
        self.leap_from_y = 0.0
        self.approach_from_x = -6.0
        self.approach_frames = int(Constants.FPS * 1.0)
        self.rotation_speed = 8.0
        self.sway_degrees = 15.0
        self.sway_period = Constants.FPS * 4.0
        self.speak_lead = int(Constants.FPS * 1.0)
        self.linger_frames = int(Constants.FPS * 2.0)
        self.fly_frames = int(Constants.FPS * 1.5)
        self.fly_top = 5.0
        self.fly_right = 6.0
        self.z_far = -12.0

        self.phrases = ("say_all_graphics", "say_3d")
        self.phase = AsianAnimation.LEAP
        self.leap_timer = 0
        self.approach_timer = 0
        self.sway_timer = 0
        self.speech_index = 0
        self.linger_timer = 0
        self.fly_timer = 0
        self.angle = 0.0
        self.x = 0.0
        self.y = 0.0
        self.z = self.z_behind
        self.fly_from_x = 0.0
        self.fly_from_z = self.z_front

        self._render_asian()

    @property
    def finished(self):
        return self.phase == AsianAnimation.DONE

    def leap_in_and_say(self, *phrases):
        self.phrases = phrases
        self.phase = AsianAnimation.APPROACH
        self.approach_timer = 0
        self.sway_timer = 0
        self.speech_index = 0
        self.linger_timer = 0
        self.fly_timer = 0
        self.angle = 0.0
        self.x = self.approach_from_x
        self.y = 0.0
        self.z = self.z_behind
        self.land_y = 2.0
        self.land_z = 0.0
        self.leap_peak = 3.0

    def speak(self, phrase):
        """Start a single spoken phrase (audio + lip-sync + on-screen text)
        outside the leap/fly choreography, for the encore. Call advance_speech()
        each frame afterwards to run the lips, then fly_away() when it ends."""
        getattr(self.asian, phrase)()
        self._render_asian()

    def advance_speech(self):
        """Advance the lip-sync one frame, re-rendering when the mouth changes.
        Returns True while the phrase is still being spoken."""
        if self.asian.talk():
            self._render_asian()
        return self.asian.talking

    def glide_to_speak_pose(self, rate=0.08):
        """Ease back to the centred pose the first talk spoke and flew from
        (x=0, y=0, z=z_front). Called while speaking so the encore fly-away
        traces the same arc instead of crossing the screen from behind."""
        self.x += (0.0 - self.x) * rate
        self.y += (0.0 - self.y) * rate
        self.z += (self.z_front - self.z) * rate

    def fly_away(self):
        """Jump back to the top-right corner, the same exit used after the
        first talk."""
        self._begin_fly()

    def update(self, frame):
        if self.phase == AsianAnimation.APPROACH:
            self._update_approach()
        elif self.phase == AsianAnimation.LEAP:
            self._update_leap()
        elif self.phase == AsianAnimation.FINISH:
            self._update_finish()
        elif self.phase == AsianAnimation.SPEAK:
            self._update_speak()
        elif self.phase == AsianAnimation.FLY:
            self._update_fly()
        elif self.phase == AsianAnimation.DONE:
            self._update_rest()

    def _update_approach(self):
        progress = min(1.0, self.approach_timer / self.approach_frames)
        self.x = self.approach_from_x * (1.0 - progress)
        self.approach_timer += 1
        if progress >= 1.0:
            self.x = 0.0
            self.leap_from_z = self.z
            self.leap_from_y = self.y
            self.leap_timer = 0
            self.phase = AsianAnimation.LEAP

    def _update_leap(self):
        progress = min(1.0, self.leap_timer / self.leap_frames)
        self.z = self.leap_from_z + (self.land_z - self.leap_from_z) * progress
        y_base = self.leap_from_y + (self.land_y - self.leap_from_y) * progress
        self.y = y_base + self.leap_peak * math.sin(math.pi * progress)
        self.angle += self.rotation_speed
        self.leap_timer += 1
        if progress >= 1.0:
            self.z = self.land_z
            self.y = self.land_y
            self.phase = AsianAnimation.FINISH

    def _update_finish(self):
        self.angle += self.rotation_speed
        if self.angle % 360.0 < self.rotation_speed:
            self.angle = 0.0
            self.phase = AsianAnimation.SPEAK

    def _update_speak(self):
        self.sway_timer += 1
        self.angle = self.sway_degrees * math.sin(2 * math.pi * self.sway_timer / self.sway_period)
        if self.speech_index == 0 and self.sway_timer >= self.speak_lead:
            self._next_phrase()
        if self.asian.talk():
            self._render_asian()
        elif not self.asian.talking and 0 < self.speech_index:
            if self.speech_index < len(self.phrases):
                self._next_phrase()
            else:
                self.linger_timer += 1
                if self.linger_timer > self.linger_frames:
                    self._begin_fly()

    def _next_phrase(self):
        getattr(self.asian, self.phrases[self.speech_index])()
        self.speech_index += 1
        self._render_asian()

    def _begin_fly(self):
        self.phase = AsianAnimation.FLY
        self.fly_timer = 0
        self.fly_from_x = self.x
        self.fly_from_z = self.z

    def _update_fly(self):
        progress = min(1.0, self.fly_timer / self.fly_frames)
        self.x = self.fly_from_x + (self.fly_right - self.fly_from_x) * progress
        self.y = self.fly_top * math.sin(math.pi / 2 * progress)
        self.z = self.fly_from_z + (self.z_far - self.fly_from_z) * progress
        self.sway_timer += 1
        self.angle = self.sway_degrees * math.sin(2 * math.pi * self.sway_timer / self.sway_period)
        self.fly_timer += 1
        if progress >= 1.0:
            self.phase = AsianAnimation.DONE

    def _update_rest(self):
        self.sway_timer += 1
        self.angle = self.sway_degrees * math.sin(2 * math.pi * self.sway_timer / self.sway_period)

    def draw(self):
        self._begin_3d()
        glTranslatef(self.x, self.y, self.z)
        glRotatef(self.angle, 0.0, 1.0, 0.0)
        glEnable(GL_TEXTURE_2D)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glDepthMask(False)
        glColor3f(1.0, 1.0, 1.0)
        glBindTexture(GL_TEXTURE_2D, self.texture)
        glBegin(GL_QUADS)
        glTexCoord2f(0, 0); glVertex3f(-self.half_width, self.half_height, 0.0)
        glTexCoord2f(1, 0); glVertex3f(self.half_width, self.half_height, 0.0)
        glTexCoord2f(1, 1); glVertex3f(self.half_width, -self.half_height, 0.0)
        glTexCoord2f(0, 1); glVertex3f(-self.half_width, -self.half_height, 0.0)
        glEnd()
        glDepthMask(True)
        glDisable(GL_BLEND)

    def _begin_3d(self):
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(Constants.FOV, Constants.WIDTH / Constants.HEIGHT, 0.1,
                       AsianAnimation.FAR_PLANE)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glTranslatef(0.0, 0.0, Constants.CAMERA_Z)

    def _render_asian(self):
        self.surface.fill((0, 0, 0, 0))
        self.asian.render(self.surface, transparent_space=True)
        self._upload()

    def _upload(self):
        data = pygame.image.tobytes(self.surface, "RGBA")
        glBindTexture(GL_TEXTURE_2D, self.texture)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, self.surface.get_width(),
                     self.surface.get_height(), 0, GL_RGBA, GL_UNSIGNED_BYTE, data)
