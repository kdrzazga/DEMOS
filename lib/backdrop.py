import math

import numpy as np
from OpenGL.GL import *
from OpenGL.GLU import gluPerspective, gluLookAt

from lib.particles import TextureLibrary
from lib.nebula import Config, NebulaGas, StarField, SpikeStars
from lib.round_nebula import RoundNebula


class SpaceBackdrop:
    def __init__(self, aspect, fov=55.0, far=3200.0, tilt=90.0, view_distance=220.0):
        self.aspect = aspect
        self.fov = fov
        self.far = far
        self.tilt = tilt
        self.view_distance = view_distance
        self.world_up = np.array([0.0, 1.0, 0.0], dtype=np.float32)
        self.config = Config()
        self.config.stars = 8000
        self.config.star_volume = (-620.0, 620.0, -540.0, 520.0, -1800.0, 500.0)
        self.textures = TextureLibrary()
        self.batches = (#NebulaGas(self.config, self.textures.glow),
                        StarField(self.config, self.textures.glow),
                        SpikeStars(self.config, self.textures.spike)
                        )
        self.round_nebulas = self._build_round_nebulas()

    def _build_round_nebulas(self):
        glow = self.textures.glow
        return (RoundNebula(glow, center=(-210.0, 214.0, -900.0), radius=170.0, seed=3, spin_speed=0.08),
                RoundNebula(glow, center=(330.0, -260.0, -1200.0), radius=190.0, seed=2, spin_speed=-0.05,
                            inner_color=(0.10, 0.96, 0.10)),
                RoundNebula(glow, center=(-200.0, -436.0, -1500.0), radius=200.0, seed=2, spin_speed=0.10,
                            rim_color=(0.0, 0.94, 0.30)),
                RoundNebula(glow, center=(520.0, 300.0, -1800.0), radius=240.0, seed=5, spin_speed=-0.09,
                            rim_color=(0.0, 0.15, 0.99)),
                RoundNebula(glow, center=(-620.0, -280.0, -2100.0), radius=250.0, seed=1, spin_speed=-0.06),
                RoundNebula(glow, center=(150.0, 212.0, -700.0), radius=130.0, seed=6, spin_speed=-0.045,
                            rim_color=(1.0, 0.34, 0.30), shell_color=(1.0, 0.58, 0.34),
                            inner_color=(0.40, 0.46, 0.92)))

    def _camera_basis(self, eye, target):
        forward = np.array(target, dtype=np.float32) - np.array(eye, dtype=np.float32)
        forward = forward / np.linalg.norm(forward)
        right = np.cross(forward, self.world_up)
        right = right / np.linalg.norm(right)
        return forward, right.astype(np.float32), np.cross(right, forward).astype(np.float32)

    def _to_local(self, vector):
        angle = math.radians(-self.tilt)
        cos_value = math.cos(angle)
        sin_value = math.sin(angle)
        return np.array([vector[0],
                         vector[1] * cos_value - vector[2] * sin_value,
                         vector[1] * sin_value + vector[2] * cos_value], dtype=np.float32)

    def update(self, moment, brightness):
        if brightness <= 0.01:
            return
        for batch in self.batches:
            batch.update(moment)
            batch.colors[:, 3] *= brightness
        for nebula in self.round_nebulas:
            nebula.update(moment)
            nebula.colors[:, 3] *= brightness

    def draw(self, brightness, eye, target, travel=0.0):
        if brightness <= 0.01:
            return
        forward, right, up = self._camera_basis(eye, target)
        local_right = self._to_local(right)
        local_up = self._to_local(up)

        glPushAttrib(GL_ENABLE_BIT | GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT | GL_TEXTURE_BIT)
        glPushClientAttrib(GL_CLIENT_VERTEX_ARRAY_BIT)
        glDisable(GL_LIGHTING)
        glDisable(GL_FOG)
        glDisable(GL_DEPTH_TEST)
        glDisable(GL_CULL_FACE)
        glDepthMask(GL_FALSE)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE)
        glEnable(GL_TEXTURE_2D)
        glTexEnvf(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_MODULATE)
        glEnableClientState(GL_VERTEX_ARRAY)
        glEnableClientState(GL_COLOR_ARRAY)
        glEnableClientState(GL_TEXTURE_COORD_ARRAY)

        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        gluPerspective(self.fov, self.aspect, 1.0, self.far)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        gluLookAt(0.0, 0.0, 0.0, forward[0], forward[1], forward[2],
                  self.world_up[0], self.world_up[1], self.world_up[2])
        glRotatef(self.tilt, 1.0, 0.0, 0.0)
        glTranslatef(0.0, 0.0, -(self.view_distance - travel))

        for batch in self.batches:
            batch.render(local_right, local_up)
        for nebula in self.round_nebulas:
            nebula.render(local_right, local_up)

        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glPopClientAttrib()
        glPopAttrib()
