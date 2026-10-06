"""The Commodore 64 blows apart.

The keyboard is shown face-on, parallel to the screen and filling it, for a
moment, then it explodes: every key flies off in its own direction, tumbling,
while the rest of the case drops out of the picture.

The animation owns its camera, so the caller only needs a GL context with the
projection and lighting set up, and a built Commodore64.
"""

import math
import random

from OpenGL.GL import *


class FlyingKey:

	def __init__(self, key, position, velocity, spin_axis, spin_speed):
		self.key = key
		self.position = position
		self.velocity = velocity
		self.spin_axis = spin_axis
		self.spin_speed = spin_speed
		self.angle = 0.0

	def update(self, seconds, gravity):
		self.velocity = tuple(speed + pull * seconds for speed, pull in zip(self.velocity, gravity))
		self.position = tuple(place + speed * seconds for place, speed in zip(self.position, self.velocity))
		self.angle += self.spin_speed * seconds

	def draw(self, slope_degrees):
		glPushMatrix()
		glTranslatef(*self.position)
		glRotatef(self.angle, *self.spin_axis)
		glRotatef(slope_degrees, 1.0, 0.0, 0.0)
		self.key.draw()
		glPopMatrix()


class CrashAnimation:

	def __init__(self, computer, aspect, fov, fps=60, hold_seconds=0.25, explosion_seconds=3.0,
	             screen_fill=0.96, model_centre_y=2.8,
	             light_direction=(-0.35, 1.0, 0.7, 0.0), gravity=60.0,
	             key_speed=(18.0, 42.0), key_lift=0.7, key_spin=(180.0, 720.0),
	             case_tilt_speed=18.0, seed=64):
		self.computer = computer
		self.frame_seconds = 1.0 / fps
		self.hold_seconds = hold_seconds
		self.explosion_seconds = explosion_seconds
		self.view_pitch = 90.0 - computer.slope_degrees
		view_pitch_radians = math.radians(self.view_pitch)
		self.screen_down = (0.0, -math.cos(view_pitch_radians), math.sin(view_pitch_radians))
		self.toward_viewer = (0.0, math.sin(view_pitch_radians), math.cos(view_pitch_radians))
		self.model_centre_y = model_centre_y
		self.light_direction = light_direction
		self.gravity = gravity
		self.key_speed = key_speed
		self.key_lift = key_lift
		self.key_spin = key_spin
		self.case_tilt_speed = case_tilt_speed
		self.seed = seed

		placed = computer.key_world_positions()
		left = min(x - key.width * computer.key_pitch / 2 for key, (x, _, _) in placed)
		right = max(x + key.width * computer.key_pitch / 2 for key, (x, _, _) in placed)
		heights = [y for _, (_, y, _) in placed]
		depths = [z for _, (_, _, z) in placed]
		self.view_target = ((left + right) / 2, (min(heights) + max(heights)) / 2, (min(depths) + max(depths)) / 2)

		horizontal_half_fov = math.atan(math.tan(math.radians(fov / 2)) * aspect)
		self.view_distance = ((right - left) / 2 / screen_fill) / math.tan(horizontal_half_fov)
		self.restart()

	def restart(self):
		self.elapsed = 0.0
		self.case_drop = 0.0
		self.case_fall_speed = 0.0
		self.case_tilt = 0.0
		self.flying_keys = self._launch_keys(random.Random(self.seed))

	def _launch_keys(self, rng):
		placed = self.computer.key_world_positions()
		centre_x = sum(position[0] for _, position in placed) / len(placed)
		centre_z = sum(position[2] for _, position in placed) / len(placed)
		flying = []
		for key, (x, y, z) in placed:
			outward_x, outward_z = (x - centre_x) / self.computer.width, (z - centre_z) / self.computer.width
			upward = rng.gauss(0.0, 1.0) + self.key_lift
			toward_viewer = abs(rng.gauss(0.0, 1.0))
			direction = tuple(scatter + outward + toward_viewer * viewer - upward * down
			                  for scatter, outward, viewer, down in zip(
			                      (rng.gauss(0.0, 1.0), 0.0, rng.gauss(0.0, 1.0)),
			                      (outward_x * 2.0, 0.0, outward_z * 2.0),
			                      self.toward_viewer, self.screen_down))
			length = math.sqrt(sum(component * component for component in direction))
			speed = rng.uniform(*self.key_speed)
			velocity = tuple(component / length * speed for component in direction)
			axis = (rng.gauss(0.0, 1.0), rng.gauss(0.0, 1.0), rng.gauss(0.0, 1.0))
			spin = rng.uniform(*self.key_spin) * rng.choice((-1.0, 1.0))
			flying.append(FlyingKey(key, (x, y, z), velocity, axis, spin))
		return flying

	@property
	def exploded(self):
		return self.elapsed >= self.hold_seconds

	@property
	def done(self):
		return self.elapsed >= self.hold_seconds + self.explosion_seconds

	def update(self):
		if self.done:
			return
		if self.exploded:
			for flying_key in self.flying_keys:
				flying_key.update(self.frame_seconds, tuple(component * self.gravity for component in self.screen_down))
			self.case_fall_speed += self.gravity * self.frame_seconds
			self.case_drop += self.case_fall_speed * self.frame_seconds
			self.case_tilt += self.case_tilt_speed * self.frame_seconds
		self.elapsed += self.frame_seconds

	def draw(self):
		glLoadIdentity()
		glTranslatef(0.0, 0.0, -self.view_distance)
		glRotatef(self.view_pitch, 1.0, 0.0, 0.0)
		glLightfv(GL_LIGHT0, GL_POSITION, self.light_direction)
		target_x, target_y, target_z = self.view_target
		glTranslatef(-target_x, -target_y, -target_z)

		glPushMatrix()
		glTranslatef(*(component * self.case_drop for component in self.screen_down))
		glTranslatef(0.0, self.model_centre_y, 0.0)
		glRotatef(self.case_tilt, 1.0, 0.0, 0.0)
		glTranslatef(0.0, -self.model_centre_y, 0.0)
		self.computer.draw_case()
		glPopMatrix()

		for flying_key in self.flying_keys:
			flying_key.draw(self.computer.slope_degrees)
