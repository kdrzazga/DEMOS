import math
import random
from OpenGL.GL import *
from OpenGL.GLU import *


class Bonfire:
    def __init__(self, x, y, z, scale=1.0, seed=0, smoke_fade_height=8.0):
        self.x = x
        self.y = y
        self.z = z
        self.scale = scale
        self.random_generator = random.Random(seed)
        self.log_color = (0.36, 0.22, 0.11)
        self.flame_colors = ((0.85, 0.10, 0.02), (1.0, 0.45, 0.05), (1.0, 0.85, 0.25))
        self.flame_base_y = 0.2
        self.smoke_color = (0.72, 0.72, 0.75)
        self.smoke_start = 1.5
        self.smoke_fade_height = smoke_fade_height
        self.smoke_rise_rate = 0.12
        self.time = 0.0
        self.quadric = gluNewQuadric()
        gluQuadricNormals(self.quadric, GLU_SMOOTH)
        self.logs = self._build_logs()
        self.flames = self._build_flames()
        self.smoke_puffs = self._build_smoke()

    def update(self, dt):
        self.time += dt

    def glow_intensity(self):
        flicker = 0.72 + 0.18 * math.sin(self.time * 7.0) + 0.10 * math.sin(self.time * 13.0 + 1.3)
        return max(0.4, min(1.0, flicker))

    def light_position(self):
        return (self.x, self.y + (self.flame_base_y + 0.9) * self.scale, self.z, 1.0)

    def _build_logs(self):
        logs = []
        length = 1.6
        radius = 0.13
        gap = length * 0.31
        layer_height = radius * 2.0
        axes = ("x", "z", "x")
        for layer, axis in enumerate(axes):
            y = radius + layer * layer_height
            for offset in (-gap, gap):
                shade = self.random_generator.uniform(0.85, 1.12)
                color = (self.log_color[0] * shade, self.log_color[1] * shade, self.log_color[2] * shade)
                logs.append((axis, offset, y, length, radius, color))
        return logs

    def _build_flames(self):
        flames = []
        for _ in range(5):
            angle = self.random_generator.uniform(0.0, math.tau)
            spread = self.random_generator.uniform(0.0, 0.22)
            base_x = math.cos(angle) * spread
            base_z = math.sin(angle) * spread
            height = self.random_generator.uniform(1.3, 2.1)
            radius = self.random_generator.uniform(0.26, 0.44)
            phase = self.random_generator.uniform(0.0, math.tau)
            speed = self.random_generator.uniform(3.0, 6.0)
            flames.append((base_x, base_z, height, radius, phase, speed))
        return flames

    def _draw_logs(self):
        for axis, offset, y, length, radius, color in self.logs:
            glColor3f(*color)
            glPushMatrix()
            if axis == "x":
                glTranslatef(-length / 2.0, y, offset)
                glRotatef(90.0, 0.0, 1.0, 0.0)
            else:
                glTranslatef(offset, y, -length / 2.0)
            gluCylinder(self.quadric, radius, radius, length, 10, 1)
            glPopMatrix()

    def _flame_radius_profile(self, fraction):
        return (1.0 - fraction) * (1.0 + 0.4 * math.sin(math.pi * fraction))

    def _flame_color(self, fraction):
        red, orange, yellow = self.flame_colors
        if fraction < 0.5:
            mix = fraction / 0.5
            rgb = tuple(red[channel] + (orange[channel] - red[channel]) * mix for channel in range(3))
        else:
            mix = (fraction - 0.5) / 0.5
            rgb = tuple(orange[channel] + (yellow[channel] - orange[channel]) * mix for channel in range(3))
        alpha = max(0.06, 0.75 - 0.62 * fraction)
        return rgb[0], rgb[1], rgb[2], alpha

    def _draw_flame_tongue(self, base_x, base_z, height, base_radius):
        rings = 10
        segments = 12
        for ring in range(rings):
            lower = ring / rings
            upper = (ring + 1) / rings
            glBegin(GL_QUAD_STRIP)
            for segment in range(segments + 1):
                angle = math.tau * segment / segments
                for fraction in (upper, lower):
                    ring_radius = base_radius * self._flame_radius_profile(fraction)
                    sway = math.sin(self.time * 2.2 + fraction * 5.0 + base_x * 3.0) * 0.06 * fraction
                    glColor4f(*self._flame_color(fraction))
                    glVertex3f(base_x + math.cos(angle) * ring_radius + sway,
                               self.flame_base_y + height * fraction,
                               base_z + math.sin(angle) * ring_radius)
            glEnd()

    def _draw_flames(self):
        glDisable(GL_LIGHTING)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glDepthMask(GL_FALSE)
        for base_x, base_z, height, radius, phase, speed in self.flames:
            flicker = 0.82 + 0.18 * math.sin(self.time * speed + phase) + 0.08 * math.sin(self.time * speed * 1.7 + phase)
            self._draw_flame_tongue(base_x, base_z, height * flicker, radius * (0.92 + 0.08 * flicker))
        glDepthMask(GL_TRUE)
        glDisable(GL_BLEND)
        glEnable(GL_LIGHTING)

    def _build_smoke(self):
        puffs = []
        count = 20
        for index in range(count):
            phase = index / count
            sway_phase = self.random_generator.uniform(0.0, math.tau)
            sway_amp = self.random_generator.uniform(0.12, 0.30)
            puffs.append((phase, sway_phase, sway_amp))
        return puffs

    def _draw_smoke(self):
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        glDisable(GL_LIGHTING)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glDepthMask(GL_FALSE)
        rise = self.smoke_fade_height - self.smoke_start
        for phase, sway_phase, sway_amp in self.smoke_puffs:
            progress = (self.time * self.smoke_rise_rate + phase) % 1.0
            drift = sway_amp * progress * progress
            offset_x = math.sin(progress * 3.0 + sway_phase) * drift
            offset_z = math.cos(progress * 2.4 + sway_phase * 1.3) * drift
            alpha = 0.34 * min(progress * 4.0, 1.0) * (1.0 - progress)
            glColor4f(self.smoke_color[0], self.smoke_color[1], self.smoke_color[2], alpha)
            glPushMatrix()
            glTranslatef(offset_x, self.smoke_start + progress * rise, offset_z)
            gluSphere(self.quadric, 0.05 + 0.6 * progress * progress, 8, 8)
            glPopMatrix()
        glDepthMask(GL_TRUE)
        glDisable(GL_BLEND)
        glEnable(GL_LIGHTING)
        glPopMatrix()

    def draw(self):
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        glScalef(self.scale, self.scale, self.scale)
        self._draw_logs()
        self._draw_flames()
        glPopMatrix()
        self._draw_smoke()
