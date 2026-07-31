"""A single 3D firework effect for pygame + OpenGL.

A Firework has two phases: a rising "shaft" that climbs at a launch angle up to
the burst point, then an explosion that throws PARTICLE_COUNT sparks outward in
every direction, each spark's colour fading to black as it dies out.

The caller owns the projection / modelview (the camera); draw() only emits the
firework's geometry in world space and restores whatever GL state it touches.
"""

import math
import random

from OpenGL.GL import *


class Particle:

	def __init__(self, x, y, z, vx, vy, vz):
		self.x, self.y, self.z = x, y, z
		self.vx, self.vy, self.vz = vx, vy, vz
		self.age = 0

	def update(self, gravity, drag):
		self.age += 1
		self.vy -= gravity
		self.vx *= drag
		self.vy *= drag
		self.vz *= drag
		self.x += self.vx
		self.y += self.vy
		self.z += self.vz


class Firework:

	PARTICLE_COUNT = 75
	PARTICLE_LIFE = 80
	PARTICLE_RADIUS = 0.035
	PARTICLE_SEGMENTS = 10

	SHAFT_LENGTH = 3.0
	ASCENT_FRAMES = 50
	SHAFT_WIDTH = 2.0

	SPEED_MIN = 0.03
	SPEED_MAX = 0.07
	GRAVITY = 0.0015
	DRAG = 0.97

	def __init__(self, x, y, z, angle_deg=135, color=(1, 1, 1)):
		self.color = color
		self._burst = (x, y, z)
		rad = math.radians(angle_deg)
		self._launch = (x - math.cos(rad) * self.SHAFT_LENGTH,
		                y - math.sin(rad) * self.SHAFT_LENGTH,
		                z)
		self._frame = 0
		self._exploded = False
		self._particles = []

	@property
	def done(self):
		return self._exploded and not self._particles

	def update(self):
		if not self._exploded:
			self._frame += 1
			if self._frame >= self.ASCENT_FRAMES:
				self._explode()
			return
		for p in self._particles:
			p.update(self.GRAVITY, self.DRAG)
		self._particles = [p for p in self._particles if p.age < self.PARTICLE_LIFE]

	def _explode(self):
		self._exploded = True
		bx, by, bz = self._burst
		for _ in range(self.PARTICLE_COUNT):
			theta = random.uniform(0.0, 2.0 * math.pi)
			phi = math.acos(random.uniform(-1.0, 1.0))
			speed = random.uniform(self.SPEED_MIN, self.SPEED_MAX)
			vx = speed * math.sin(phi) * math.cos(theta)
			vy = speed * math.sin(phi) * math.sin(theta)
			vz = speed * math.cos(phi)
			self._particles.append(Particle(bx, by, bz, vx, vy, vz))

	def draw(self):
		glPushAttrib(GL_ENABLE_BIT | GL_CURRENT_BIT | GL_LINE_BIT | GL_COLOR_BUFFER_BIT)
		glDisable(GL_TEXTURE_2D)
		glDisable(GL_DEPTH_TEST)
		glEnable(GL_BLEND)
		glBlendFunc(GL_SRC_ALPHA, GL_ONE)
		if not self._exploded:
			self._draw_shaft()
		else:
			for p in self._particles:
				fade = max(0.0, 1.0 - p.age / self.PARTICLE_LIFE)
				faded = (self.color[0] * fade, self.color[1] * fade, self.color[2] * fade)
				self._circle(p.x, p.y, p.z, self.PARTICLE_RADIUS, faded)
		glPopAttrib()

	def _draw_shaft(self):
		t = self._frame / self.ASCENT_FRAMES
		lx, ly, lz = self._launch
		bx, by, bz = self._burst
		tx = lx + (bx - lx) * t
		ty = ly + (by - ly) * t
		tz = lz + (bz - lz) * t
		glLineWidth(self.SHAFT_WIDTH)
		glColor3f(*self.color)
		glBegin(GL_LINES)
		glVertex3f(lx, ly, lz)
		glVertex3f(tx, ty, tz)
		glEnd()
		self._circle(tx, ty, tz, self.PARTICLE_RADIUS * 1.5, self.color)

	def _circle(self, cx, cy, cz, r, color):
		glColor3f(*color)
		glBegin(GL_TRIANGLE_FAN)
		glVertex3f(cx, cy, cz)
		for i in range(self.PARTICLE_SEGMENTS + 1):
			a = 2.0 * math.pi * i / self.PARTICLE_SEGMENTS
			glVertex3f(cx + r * math.cos(a), cy + r * math.sin(a), cz)
		glEnd()
