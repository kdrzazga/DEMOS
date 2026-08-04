import os

import pygame
from OpenGL.GL import *
from OpenGL.GLU import gluPerspective

try:
    from base_stage import BaseStage
except ModuleNotFoundError:
    from demos.pc45.base_stage import BaseStage

try:
    from building3d.scene import Scene
    from building3d.orbit_camera import OrbitCamera
    from building3d.rendering import LitSurfaceRenderer
    from building3d.linear_algebra import Vector3
    from building3d.building.building_builder import BuildingBuilder
except ModuleNotFoundError:
    from demos.pc45.building3d.scene import Scene
    from demos.pc45.building3d.orbit_camera import OrbitCamera
    from demos.pc45.building3d.rendering import LitSurfaceRenderer
    from demos.pc45.building3d.linear_algebra import Vector3
    from demos.pc45.building3d.building.building_builder import BuildingBuilder


class Stage3(BaseStage):

    FPS = 60
    FAR_DISTANCE = 110.0
    NEAR_DISTANCE = 38.0
    ROTATION_TURNS = 2.0
    FRONT_ROTATION_DEGREES = 0.0
    APPROACH_SECONDS = 6.0
    PHOTO_START_SECONDS = 7.5
    BACKGROUND_COLOR = (0.059, 0.275, 0.627)

    def __init__(self, win_w, win_h, res_path, fov):
        super().__init__(win_w, win_h, res_path, fov)
        self.tunes = (("summary/summary.mp3", 30), ("summary/dominance.mp3", 3))
        self._index = 0
        self._tune_start = 0
        self.bg_image = "summary/HQ.jpg"
        bg = pygame.image.load(os.path.join(res_path, self.bg_image))
        self.bg_w, self.bg_h = bg.get_size()
        self.bg = self.make_texture()
        glBindTexture(GL_TEXTURE_2D, self.bg)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, self.bg_w, self.bg_h, 0,
                     GL_RGBA, GL_UNSIGNED_BYTE, pygame.image.tostring(bg, "RGBA", True))
        self.scene = self._build_scene()
        self._configure_projection()
        self._play(self.tunes[0][0])

    def _build_scene(self):
        building = BuildingBuilder().with_pillar(0.9).with_logo(2, 2).build()
        camera = OrbitCamera(Vector3(0.0, building.total_height * 0.5, 0.0),
                             self.FAR_DISTANCE, azimuth=0.0, elevation=0.15)
        renderer = LitSurfaceRenderer(Vector3(0.4, 0.85, 0.5))
        return Scene(building, camera, renderer)

    def _configure_projection(self):
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(55.0, self.win_w / self.win_h, 0.5, 600.0)
        glMatrixMode(GL_MODELVIEW)

    def _play(self, tune):
        try:
            pygame.mixer.music.load(os.path.join(self.res_path, tune))
            pygame.mixer.music.play()
        except pygame.error as exc:
            print("audio unavailable:", exc)

    def _ease_out(self, value):
        clamped = max(0.0, min(1.0, value))
        return 1.0 - (1.0 - clamped) ** 3

    def _smoothstep(self, value):
        clamped = max(0.0, min(1.0, value))
        return clamped * clamped * (3.0 - 2.0 * clamped)

    def _apply_choreography(self, elapsed_seconds):
        approach_progress = elapsed_seconds / self.APPROACH_SECONDS
        target_rotation = 360.0 * self.ROTATION_TURNS + self.FRONT_ROTATION_DEGREES
        self.scene.building_rotation_degrees = target_rotation * self._ease_out(approach_progress)
        distance_progress = self._smoothstep(approach_progress)
        self.scene.camera.distance = self.FAR_DISTANCE + (self.NEAR_DISTANCE - self.FAR_DISTANCE) * distance_progress

    def _draw_model(self, elapsed_seconds):
        glDisable(GL_TEXTURE_2D)
        glDisable(GL_BLEND)
        glDisable(GL_CULL_FACE)
        glEnable(GL_DEPTH_TEST)
        glClearColor(self.BACKGROUND_COLOR[0], self.BACKGROUND_COLOR[1], self.BACKGROUND_COLOR[2], 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        self._apply_choreography(elapsed_seconds)
        self.scene.draw()

    def _draw_background(self):
        scale = max(self.win_w / self.bg_w, self.win_h / self.bg_h)
        sw = self.bg_w * scale
        sh = self.bg_h * scale
        x0 = (self.win_w - sw) / 2.0
        y0 = (self.win_h - sh) / 2.0
        glDisable(GL_DEPTH_TEST)
        glDisable(GL_BLEND)
        glEnable(GL_TEXTURE_2D)
        glColor3f(1.0, 1.0, 1.0)
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(0.0, self.win_w, 0.0, self.win_h, -1.0, 1.0)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        glBindTexture(GL_TEXTURE_2D, self.bg)
        glBegin(GL_QUADS)
        glTexCoord2f(0.0, 0.0); glVertex2f(x0, y0)
        glTexCoord2f(1.0, 0.0); glVertex2f(x0 + sw, y0)
        glTexCoord2f(1.0, 1.0); glVertex2f(x0 + sw, y0 + sh)
        glTexCoord2f(0.0, 1.0); glVertex2f(x0, y0 + sh)
        glEnd()
        glMatrixMode(GL_MODELVIEW)
        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)

    def render(self):
        elapsed_seconds = self.frame / self.FPS
        if elapsed_seconds < self.PHOTO_START_SECONDS:
            self._draw_model(elapsed_seconds)
        else:
            glClearColor(0.0, 0.0, 0.0, 1.0)
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            self._draw_background()
        if self._index < len(self.tunes):
            elapsed = (self.frame - self._tune_start) / self.FPS
            if elapsed >= self.tunes[self._index][1]:
                self._index += 1
                self._tune_start = self.frame
                if self._index < len(self.tunes):
                    self._play(self.tunes[self._index][0])
        self.frame += 1

    @property
    def done(self):
        return self._index >= len(self.tunes)

    def destroy(self):
        pygame.mixer.music.stop()
        glDeleteTextures([self.bg])
