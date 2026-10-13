import math
import os
import random
import sys

import numpy as np
import pygame
from pygame.locals import DOUBLEBUF, OPENGL, QUIT, KEYDOWN, K_ESCAPE, K_r
from OpenGL.GL import *

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from lib.particles import Texture2D


class PhotoPart:
    """Soft elliptical patch of the photo that sways, bobs and breathes around a pivot (image pixels)."""

    def __init__(self, name, center, radii, pivot, swing=0.0, swing_rate=0.1, bob=(0.0, 0.0), bob_rate=0.3,
                 breath=0.0, breath_rate=0.25, phase=0.0, core=0.55):
        self.name = name
        self.center = np.array(center, dtype=np.float64)
        self.radii = np.array(radii, dtype=np.float64)
        self.pivot = np.array(pivot, dtype=np.float64)
        self.swing = swing
        self.swing_rate = swing_rate
        self.bob = bob
        self.bob_rate = bob_rate
        self.breath = breath
        self.breath_rate = breath_rate
        self.phase = phase
        self.core = core

    def weights(self, points):
        offset = (points - self.center) / self.radii
        distance = np.sqrt((offset * offset).sum(axis=1))
        falloff = np.clip((1.0 - distance) / (1.0 - self.core), 0.0, 1.0)
        return falloff * falloff * (3.0 - 2.0 * falloff)

    @staticmethod
    def _wave(time, rate, phase):
        angle = 2.0 * math.pi * rate * time + phase
        return 0.7 * math.sin(angle) + 0.3 * math.sin(1.618 * angle + 1.0)

    def moved(self, points, time):
        swing = math.radians(self.swing) * self._wave(time, self.swing_rate, self.phase)
        breath = self.breath * self._wave(time, self.breath_rate, self.phase + 1.3)
        relative = (points - self.pivot) * (1.0 + 0.5 * breath, 1.0 + breath)
        cos_swing, sin_swing = math.cos(swing), math.sin(swing)
        turned = np.column_stack((relative[:, 0] * cos_swing - relative[:, 1] * sin_swing,
                                  relative[:, 0] * sin_swing + relative[:, 1] * cos_swing))
        shift = (self.bob[0] * self._wave(time, self.bob_rate, self.phase + 2.1),
                 self.bob[1] * self._wave(time, self.bob_rate, self.phase + 0.4))
        return self.pivot + turned + shift


# Rig for res/LodzPrzedWOjna.jpg (1920x1063): who moves, around which point, and how much.
LODZ_STREET_RIG = (
    PhotoPart("butcher body", (1370, 560), (300, 560), (1370, 1045), swing=0.35, swing_rate=0.11, phase=0.3),
    PhotoPart("butcher chest", (1360, 400), (190, 190), (1360, 560), breath=0.008, breath_rate=0.22),
    PhotoPart("butcher head", (1342, 190), (75, 95), (1345, 265), swing=2.0, swing_rate=0.07, phase=0.5, core=0.6),
    PhotoPart("man torso", (360, 450), (230, 230), (280, 640), swing=1.0, swing_rate=0.13, phase=1.7),
    PhotoPart("man head", (462, 295), (55, 70), (445, 350), swing=2.5, swing_rate=0.09, phase=0.2),
    PhotoPart("man right arm", (265, 600), (65, 115), (290, 430), swing=2.0, swing_rate=0.45, phase=2.9, core=0.8),
    PhotoPart("man right hand", (272, 665), (48, 52), (265, 628), swing=5.0, swing_rate=0.9, phase=0.6, core=0.65),
    PhotoPart("tub child head", (615, 530), (55, 60), (615, 580), swing=4.0, swing_rate=0.15, bob=(0.0, 1.5),
              bob_rate=0.4, phase=2.4),
    PhotoPart("tub child body", (630, 640), (110, 90), (630, 720), breath=0.015, breath_rate=0.3, phase=0.9),
    PhotoPart("boy head", (842, 450), (55, 60), (845, 500), swing=3.5, swing_rate=0.12, phase=4.0),
    PhotoPart("boy body", (845, 560), (90, 80), (845, 640), breath=0.012, breath_rate=0.27, phase=1.0),
    PhotoPart("dog head", (835, 630), (60, 55), (840, 680), swing=5.0, swing_rate=0.25, bob=(0.0, 1.0),
              bob_rate=2.2, phase=3.0),
    PhotoPart("girl", (985, 830), (170, 300), (985, 1100), swing=1.0, swing_rate=0.35, bob=(2.0, 1.5),
              bob_rate=0.7, phase=0.7),
    PhotoPart("girl head", (985, 680), (95, 95), (990, 770), swing=3.0, swing_rate=0.2, phase=5.1),
)


# Butcher's eyes in res/LodzPrzedWOjna.jpg: (center, half width and half height) in image pixels.
BUTCHER_EYES = (((1325.0, 191.0), (9.0, 5.0)), ((1362.0, 190.0), (9.0, 5.0)))


class Blink:
    """Eyelids made of the skin just above each eye, pulled down over it now and then."""

    def __init__(self, eyes, interval=(2.5, 6.0), duration=0.16, double_chance=0.2, lid_source=7.0,
                 lash_shade=0.6):
        self.eyes = tuple((np.array((center,), dtype=np.float64), np.array(half_size)) for center, half_size in eyes)
        self.interval = interval
        self.duration = duration
        self.double_chance = double_chance
        self.lid_source = lid_source
        self.lash_shade = lash_shade
        self.wait = random.uniform(*interval)
        self.progress = None

    def update(self, dt):
        if self.progress is None:
            self.wait -= dt
            if self.wait <= 0.0:
                self.progress = 0.0
            return
        self.progress += dt / self.duration
        if self.progress >= 1.0:
            self.progress = None
            double = random.random() < self.double_chance
            self.wait = random.uniform(0.12, 0.25) if double else random.uniform(*self.interval)

    def closure(self):
        return 0.0 if self.progress is None else math.sin(math.pi * self.progress)

    def draw(self, photo, image_size, eye_positions, brightness):
        closure = self.closure()
        if closure <= 0.0:
            return
        width, height = image_size
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glBindTexture(GL_TEXTURE_2D, photo.id)
        for (origin, half_size), (eye_x, eye_y) in zip(self.eyes, eye_positions):
            half_width, half_height = half_size
            source_left, source_right = origin[0][0] - half_width, origin[0][0] + half_width
            source_bottom = origin[0][1] - half_height
            source_top = source_bottom - self.lid_source
            lid_top = eye_y - half_height
            lid_bottom = lid_top + 2.0 * half_height * closure
            glBegin(GL_QUAD_STRIP)
            for share, alpha in ((-1.0, 0.0), (-0.5, 1.0), (0.5, 1.0), (1.0, 0.0)):
                source_x = (source_left + source_right) / 2.0 + share * half_width
                screen_x = eye_x + share * half_width
                glColor4f(brightness, brightness, brightness, alpha)
                glTexCoord2f(source_x / width, source_top / height)
                glVertex2f(screen_x, lid_top)
                shade = brightness * self.lash_shade
                glColor4f(shade, shade, shade, alpha)
                glTexCoord2f(source_x / width, source_bottom / height)
                glVertex2f(screen_x, lid_bottom)
            glEnd()
        glDisable(GL_BLEND)


class CigaretteSmoke:
    """Thin smoke curling up from a cigarette tip, with an occasional bigger puff."""

    def __init__(self, rate=7.0, life=(3.5, 6.0), rise=(14.0, 26.0), start_size=5.0, end_size=70.0,
                 opacity=0.16, shade=0.88, puff_every=(6.0, 11.0), puff_burst=14, puff_scale=1.8):
        self.rate = rate
        self.life = life
        self.rise = rise
        self.start_size = start_size
        self.end_size = end_size
        self.opacity = opacity
        self.shade = shade
        self.puff_every = puff_every
        self.puff_burst = puff_burst
        self.puff_scale = puff_scale
        self.particles = []
        self.spawn_debt = 0.0
        self.puff_timer = random.uniform(*puff_every)

    def _spawn(self, tip, scale=1.0):
        self.particles.append({
            "x": tip[0] + random.uniform(-1.5, 1.5), "y": tip[1] + random.uniform(-1.5, 1.5),
            "age": 0.0, "life": random.uniform(*self.life), "rise": random.uniform(*self.rise) * scale,
            "drift": random.uniform(-4.0, 4.0) * scale, "seed": random.uniform(0.0, 2.0 * math.pi), "scale": scale})

    def update(self, dt, time, tip):
        self.spawn_debt += self.rate * dt
        while self.spawn_debt >= 1.0:
            self.spawn_debt -= 1.0
            self._spawn(tip)
        self.puff_timer -= dt
        if self.puff_timer <= 0.0:
            self.puff_timer = random.uniform(*self.puff_every)
            for _ in range(self.puff_burst):
                self._spawn(tip, self.puff_scale)
        for particle in self.particles:
            particle["age"] += dt
            particle["y"] -= particle["rise"] * dt
            particle["x"] += (particle["drift"] + math.sin(time * 0.9 + particle["seed"]) * 9.0) * dt
        self.particles = [particle for particle in self.particles if particle["age"] < particle["life"]]

    def draw(self, sprite):
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glBindTexture(GL_TEXTURE_2D, sprite.id)
        glBegin(GL_QUADS)
        for particle in self.particles:
            progress = particle["age"] / particle["life"]
            half = 0.5 * particle["scale"] * (self.start_size + (self.end_size - self.start_size) * progress ** 0.7)
            alpha = self.opacity * min(1.0, particle["age"] / 0.4) * (1.0 - progress) ** 1.5
            glColor4f(self.shade, self.shade, self.shade, alpha)
            x, y = particle["x"], particle["y"]
            glTexCoord2f(0.0, 0.0)
            glVertex2f(x - half, y - half)
            glTexCoord2f(1.0, 0.0)
            glVertex2f(x + half, y - half)
            glTexCoord2f(1.0, 1.0)
            glVertex2f(x + half, y + half)
            glTexCoord2f(0.0, 1.0)
            glVertex2f(x - half, y + half)
        glEnd()
        glDisable(GL_BLEND)


class FilmLook:
    """Old film projection: flicker, gate weave, grain, vignette, scratches and dust."""

    def __init__(self, width, height, grain_frames=6, grain_size=256, grain_strength=0.10, grain_texel=1.6,
                 vignette=0.38, flicker_low=0.88, weave=1.2, scratch_rate=0.5, dust_rate=6.0):
        self.width = width
        self.height = height
        self.grain_size = grain_size
        self.grain_strength = grain_strength
        self.grain_repeat = (width / (grain_size * grain_texel), height / (grain_size * grain_texel))
        self.vignette_strength = vignette
        self.flicker_low = flicker_low
        self.weave_reach = weave
        self.scratch_rate = scratch_rate
        self.dust_rate = dust_rate

        self.brightness = 1.0
        self.flicker_target = 1.0
        self.flicker_timer = 0.0
        self.weave = np.zeros(2)
        self.weave_target = np.zeros(2)
        self.weave_timer = 0.0
        self.scratches = []
        self.dust = []
        self.grain_frame = 0
        self.grain_offset = (0.0, 0.0)

        self.grains = tuple(self._repeating(Texture2D(self._grain())) for _ in range(grain_frames))
        self.vignette = Texture2D(self._vignette())

    @staticmethod
    def _repeating(texture):
        glBindTexture(GL_TEXTURE_2D, texture.id)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
        return texture

    @staticmethod
    def _gray_rgba(values):
        gray = np.clip(values, 0.0, 1.0) * 255.0
        return np.dstack((gray, gray, gray, np.full_like(gray, 255.0)))

    def _grain(self):
        return self._gray_rgba(np.random.normal(0.5, self.grain_strength, (self.grain_size, self.grain_size)))

    def _vignette(self, size=256):
        axis = np.linspace(-1.0, 1.0, size)
        grid_x, grid_y = np.meshgrid(axis, axis)
        reach = np.clip(np.sqrt(grid_x * grid_x + grid_y * grid_y) / math.sqrt(2.0), 0.0, 1.0)
        return self._gray_rgba(0.5 * (1.0 - self.vignette_strength * reach ** 2.2))

    def update(self, dt):
        self.flicker_timer -= dt
        if self.flicker_timer <= 0.0:
            self.flicker_timer = random.uniform(0.04, 0.12)
            self.flicker_target = random.uniform(self.flicker_low, 1.0)
        self.brightness += (self.flicker_target - self.brightness) * min(1.0, dt * 25.0)

        self.weave_timer -= dt
        if self.weave_timer <= 0.0:
            self.weave_timer = random.uniform(0.06, 0.14)
            self.weave_target = np.random.uniform(-self.weave_reach, self.weave_reach, 2)
        self.weave += (self.weave_target - self.weave) * min(1.0, dt * 12.0)

        self.grain_frame = random.randrange(len(self.grains))
        self.grain_offset = (random.random(), random.random())

        if random.random() < self.scratch_rate * dt:
            self.scratches.append({"x": random.uniform(0.05, 0.95) * self.width, "life": random.uniform(0.1, 0.6),
                                   "width": random.uniform(1.0, 2.5), "shade": random.choice((0.95, 0.1)),
                                   "alpha": random.uniform(0.12, 0.3)})
        for scratch in self.scratches:
            scratch["life"] -= dt
            scratch["x"] += random.uniform(-0.6, 0.6)
        self.scratches = [scratch for scratch in self.scratches if scratch["life"] > 0.0]

        self.dust = []
        if random.random() < self.dust_rate * dt:
            self.dust.append((random.uniform(0.0, self.width), random.uniform(0.0, self.height),
                              random.uniform(2.0, 5.0), random.choice((0.05, 0.05, 0.9))))

    def _full_quad(self, repeat=(1.0, 1.0), offset=(0.0, 0.0)):
        glBegin(GL_QUADS)
        glTexCoord2f(offset[0], offset[1])
        glVertex2f(0.0, 0.0)
        glTexCoord2f(offset[0] + repeat[0], offset[1])
        glVertex2f(self.width, 0.0)
        glTexCoord2f(offset[0] + repeat[0], offset[1] + repeat[1])
        glVertex2f(self.width, self.height)
        glTexCoord2f(offset[0], offset[1] + repeat[1])
        glVertex2f(0.0, self.height)
        glEnd()

    def draw_overlay(self):
        glEnable(GL_BLEND)
        glBlendFunc(GL_DST_COLOR, GL_SRC_COLOR)
        glColor4f(1.0, 1.0, 1.0, 1.0)
        glBindTexture(GL_TEXTURE_2D, self.grains[self.grain_frame].id)
        self._full_quad(self.grain_repeat, self.grain_offset)
        glBindTexture(GL_TEXTURE_2D, self.vignette.id)
        self._full_quad()

        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glDisable(GL_TEXTURE_2D)
        glBegin(GL_QUADS)
        for scratch in self.scratches:
            glColor4f(scratch["shade"], scratch["shade"], scratch["shade"], scratch["alpha"])
            left, right = scratch["x"] - scratch["width"] / 2.0, scratch["x"] + scratch["width"] / 2.0
            glVertex2f(left, 0.0)
            glVertex2f(right, 0.0)
            glVertex2f(right, self.height)
            glVertex2f(left, self.height)
        glEnd()
        for x, y, size, shade in self.dust:
            glPointSize(size)
            glColor4f(shade, shade, shade, 0.7)
            glBegin(GL_POINTS)
            glVertex2f(x, y)
            glEnd()
        glEnable(GL_TEXTURE_2D)
        glDisable(GL_BLEND)


class RevivedPhoto:
    """Brings an old photograph to life: a mesh-warped rig, cigarette smoke and a black and white film look."""

    def __init__(self, image_path=None, rig=LODZ_STREET_RIG, view=(0.0, 0.0, 1892.0, 1063.0), mesh_step=8,
                 smoke_tip=(1362.0, 242.0), eyes=BUTCHER_EYES, overscan=1.025, levels=(0.5, 99.5), gamma=0.95):
        self.image_path = image_path or os.path.join(os.path.dirname(os.path.abspath(__file__)), "res",
                                                     "LodzPrzedWOjna.jpg")
        self.view = view
        self.mesh_step = mesh_step
        self.smoke_tip = np.array((smoke_tip,), dtype=np.float64)
        self.overscan = overscan
        self.levels = levels
        self.gamma = gamma
        self.show_rig = False
        self.time = 0.0

        pixels = self._load_monochrome()
        self.height, self.width = pixels.shape[:2]
        self.photo = Texture2D(pixels)
        self._build_mesh()
        self.rig = tuple((part, *self._bind(part)) for part in rig)
        self.smoke = CigaretteSmoke()
        self.smoke_sprite = Texture2D(self._smoke_sprite())
        self.blink = Blink(eyes)
        self.eye_positions = ()
        self.film = FilmLook(self.width, self.height)

    def _load_monochrome(self):
        image = pygame.image.load(self.image_path)
        rgb = np.frombuffer(pygame.image.tobytes(image, "RGB"), dtype=np.uint8)
        rgb = rgb.reshape(image.get_height(), image.get_width(), 3).astype(np.float64) / 255.0
        luminance = rgb @ np.array((0.299, 0.587, 0.114))
        low, high = np.percentile(luminance, self.levels)
        gray = np.clip((luminance - low) / (high - low), 0.0, 1.0) ** self.gamma * 255.0
        return np.dstack((gray, gray, gray, np.full_like(gray, 255.0)))

    def _smoke_sprite(self, size=64):
        axis = np.linspace(-1.0, 1.0, size)
        grid_x, grid_y = np.meshgrid(axis, axis)
        alpha = np.exp(-4.0 * (grid_x * grid_x + grid_y * grid_y)) * 255.0
        return np.dstack((np.full_like(alpha, 255.0), np.full_like(alpha, 255.0), np.full_like(alpha, 255.0), alpha))

    def _build_mesh(self):
        columns = int(math.ceil(self.width / self.mesh_step)) + 1
        rows = int(math.ceil(self.height / self.mesh_step)) + 1
        grid_x, grid_y = np.meshgrid(np.linspace(0.0, self.width, columns), np.linspace(0.0, self.height, rows))
        self.rest = np.column_stack((grid_x.ravel(), grid_y.ravel()))
        self.positions = self.rest.astype(np.float32)
        self.texcoords = np.ascontiguousarray((self.rest / (self.width, self.height)).astype(np.float32))
        corner = (np.arange(rows - 1)[:, None] * columns + np.arange(columns - 1)[None, :]).ravel()
        self.indices = np.column_stack((corner, corner + 1, corner + columns,
                                        corner + 1, corner + columns + 1, corner + columns)).ravel().astype(np.uint32)

    def _bind(self, part):
        weights = part.weights(self.rest)
        touched = np.nonzero(weights > 1e-3)[0]
        return touched, weights[touched][:, None]

    def _displaced(self, points, rig_bindings):
        moved = points.copy()
        for part, touched, weights in rig_bindings:
            moved[touched] += weights * (part.moved(points[touched], self.time) - points[touched])
        return moved

    def _displaced_point(self, point):
        bindings = []
        for part, _, _ in self.rig:
            weight = part.weights(point)
            if weight[0] > 1e-3:
                bindings.append((part, np.array((0,)), weight[:, None]))
        return self._displaced(point, bindings)[0]

    def update(self, dt):
        self.time += dt
        self.positions = np.ascontiguousarray(self._displaced(self.rest, self.rig).astype(np.float32))
        self.smoke.update(dt, self.time, self._displaced_point(self.smoke_tip))
        self.blink.update(dt)
        self.eye_positions = tuple(self._displaced_point(origin) for origin, _ in self.blink.eyes)
        self.film.update(dt)

    def _set_camera(self, window_width, window_height):
        left, top, right, bottom = self.view
        aspect = (right - left) / (bottom - top)
        fitted_width = min(window_width, int(window_height * aspect))
        fitted_height = int(fitted_width / aspect)
        glViewport((window_width - fitted_width) // 2, (window_height - fitted_height) // 2,
                   fitted_width, fitted_height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(left, right, bottom, top, -1.0, 1.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        center_x, center_y = (left + right) / 2.0, (top + bottom) / 2.0
        glTranslatef(center_x + self.film.weave[0], center_y + self.film.weave[1], 0.0)
        glScalef(self.overscan, self.overscan, 1.0)
        glTranslatef(-center_x, -center_y, 0.0)

    def _draw_photo(self):
        glBindTexture(GL_TEXTURE_2D, self.photo.id)
        glTexEnvf(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_MODULATE)
        glColor4f(self.film.brightness, self.film.brightness, self.film.brightness, 1.0)
        glEnableClientState(GL_VERTEX_ARRAY)
        glEnableClientState(GL_TEXTURE_COORD_ARRAY)
        glVertexPointer(2, GL_FLOAT, 0, self.positions)
        glTexCoordPointer(2, GL_FLOAT, 0, self.texcoords)
        glDrawElements(GL_TRIANGLES, len(self.indices), GL_UNSIGNED_INT, self.indices)
        glDisableClientState(GL_TEXTURE_COORD_ARRAY)
        glDisableClientState(GL_VERTEX_ARRAY)

    def _draw_rig(self):
        glDisable(GL_TEXTURE_2D)
        glColor4f(1.0, 0.25, 0.1, 1.0)
        for part, _, _ in self.rig:
            glBegin(GL_LINE_LOOP)
            for step in range(48):
                angle = 2.0 * math.pi * step / 48
                glVertex2f(part.center[0] + part.radii[0] * math.cos(angle),
                           part.center[1] + part.radii[1] * math.sin(angle))
            glEnd()
            glPointSize(6.0)
            glBegin(GL_POINTS)
            glVertex2f(*part.pivot)
            glEnd()
        glColor4f(0.2, 0.6, 1.0, 1.0)
        for (eye_x, eye_y), (_, (half_width, half_height)) in zip(self.eye_positions, self.blink.eyes):
            glBegin(GL_LINE_LOOP)
            glVertex2f(eye_x - half_width, eye_y - half_height)
            glVertex2f(eye_x + half_width, eye_y - half_height)
            glVertex2f(eye_x + half_width, eye_y + half_height)
            glVertex2f(eye_x - half_width, eye_y + half_height)
            glEnd()
        glEnable(GL_TEXTURE_2D)

    def draw(self, window_width, window_height):
        glDisable(GL_DEPTH_TEST)
        glDisable(GL_LIGHTING)
        glEnable(GL_TEXTURE_2D)
        self._set_camera(window_width, window_height)
        self._draw_photo()
        self.blink.draw(self.photo, (self.width, self.height), self.eye_positions, self.film.brightness)
        self.smoke.draw(self.smoke_sprite)
        self.film.draw_overlay()
        if self.show_rig:
            self._draw_rig()


def main(width=1280, height=720):
    pygame.init()
    pygame.display.set_mode((width, height), DOUBLEBUF | OPENGL)
    pygame.display.set_caption("Lodz before the war")
    photo = RevivedPhoto()
    clock = pygame.time.Clock()
    running = True
    while running:
        delta_seconds = clock.tick(60) / 1000.0
        for event in pygame.event.get():
            if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
                running = False
            elif event.type == KEYDOWN and event.key == K_r:
                photo.show_rig = not photo.show_rig
        photo.update(delta_seconds)
        glClearColor(0.0, 0.0, 0.0, 1.0)
        glClear(GL_COLOR_BUFFER_BIT)
        photo.draw(width, height)
        pygame.display.flip()
    pygame.quit()


if __name__ == "__main__":
    main()
