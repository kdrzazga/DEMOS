"""The Commodore 64 blows apart.

The keyboard is shown face-on, parallel to the screen and filling it, for a
moment, then it explodes: every key flies off in its own direction, tumbling,
while the rest of the case drops out of the picture.

The animation owns its camera, so the caller only needs a GL context with the
projection and lighting set up, and a built Commodore64.
"""

import math
import os
import random

import pygame
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
	             case_tilt_speed=18.0, seed=64, play_sound=True,
	             sound_path=os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources", "smasz.wav")):
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
		self.sound = self._load_sound(sound_path) if play_sound else None

		placed = computer.key_world_positions()
		left = min(x - key.width * computer.key_pitch / 2 for key, (x, _, _) in placed)
		right = max(x + key.width * computer.key_pitch / 2 for key, (x, _, _) in placed)
		heights = [y for _, (_, y, _) in placed]
		depths = [z for _, (_, _, z) in placed]
		self.view_target = ((left + right) / 2, (min(heights) + max(heights)) / 2, (min(depths) + max(depths)) / 2)

		self.screen_fill = screen_fill
		self.horizontal_half_fov = math.atan(math.tan(math.radians(fov / 2)) * aspect)
		self.view_distance = ((right - left) / 2 / screen_fill) / math.tan(self.horizontal_half_fov)
		self.restart()

	def restart(self):
		self.elapsed = 0.0
		self.case_drop = 0.0
		self.case_fall_speed = 0.0
		self.case_tilt = 0.0
		self.sound_played = False
		if self.sound:
			self.sound.stop()
		self.flying_keys = self._launch_keys(random.Random(self.seed))

	def _load_sound(self, sound_path):
		if not pygame.mixer.get_init():
			pygame.mixer.init()
		return pygame.mixer.Sound(sound_path)

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
			if self.sound and not self.sound_played:
				self.sound.play()
				self.sound_played = True
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


class CaptionKey:
	"""A key gliding along a chain of cubic Bezier curves to its place in the caption.

	segments - ((start, control_start, control_end, end), ...), each one starting
	           where the previous ended; every segment takes an equal share of the
	           flight and eases in and out, so the key slows down at each joint.

	It spins a whole number of turns on the way, so it lands in its original
	orientation: face-on to the viewer.
	"""

	def __init__(self, key, segments, delay, duration, spin_axis, spin_turns, hidden_before_start=False):
		self.key = key
		self.segments = segments
		self.delay = delay
		self.duration = duration
		self.spin_axis = spin_axis
		self.spin_turns = spin_turns
		self.hidden_before_start = hidden_before_start
		self.time = 0.0

	@property
	def progress(self):
		return min(1.0, max(0.0, (self.time - self.delay) / self.duration))

	@property
	def arrived(self):
		return self.progress >= 1.0

	def update(self, seconds, gravity=None):
		self.time += seconds

	@staticmethod
	def _ease(t):
		return t * t * (3 - 2 * t)

	def _position(self, progress):
		along = progress * len(self.segments)
		index = min(int(along), len(self.segments) - 1)
		t = self._ease(along - index)
		weights = ((1 - t) ** 3, 3 * (1 - t) ** 2 * t, 3 * (1 - t) * t ** 2, t ** 3)
		return tuple(sum(weight * point[axis] for weight, point in zip(weights, self.segments[index]))
		             for axis in range(3))

	def draw(self, slope_degrees):
		if self.hidden_before_start and self.time < self.delay:
			return
		eased = self._ease(self.progress)
		glPushMatrix()
		glTranslatef(*self._position(self.progress))
		glRotatef(self.spin_turns * 360.0 * eased, *self.spin_axis)
		glRotatef(slope_degrees, 1.0, 0.0, 0.0)
		self.key.draw()
		glPopMatrix()


class CrashAnimationText(CrashAnimation):
	"""The crash, but the keys spelling ``text`` escape and form a caption.

	Keys whose legend (or shifted symbol) matches a character of the text dive
	far away from the viewer along curved paths, turn, come back and line up as
	the caption, parallel to the screen; every other key falls as usual. A key exists once, so a
	repeated character leaves a gap; a second after the caption has formed,
	copies of the missing keys sweep in from the right edge and fill the gaps.
	Spaces and characters with no key stay empty.
	"""

	def __init__(self, computer, aspect, fov, text, caption_min_depth=15.0, caption_spacing=1.1,
	             caption_flight_seconds=4.0, caption_stagger_seconds=0.6, caption_far_depth=90.0,
	             caption_far_spread=25.0, gap_wait_seconds=1.0,
	             fill_flight_seconds=1.2, fill_stagger_seconds=0.3, caption_hold_seconds=2.0,
	             caption_spin_turns=(1, 2), **animation_settings):
		self.text = text.upper()
		self.caption_min_depth = caption_min_depth
		self.caption_spacing = caption_spacing
		self.caption_flight_seconds = caption_flight_seconds
		self.caption_stagger_seconds = caption_stagger_seconds
		self.caption_far_depth = caption_far_depth
		self.caption_far_spread = caption_far_spread
		self.gap_wait_seconds = gap_wait_seconds
		self.fill_flight_seconds = fill_flight_seconds
		self.fill_stagger_seconds = fill_stagger_seconds
		self.caption_hold_seconds = caption_hold_seconds
		self.caption_spin_turns = caption_spin_turns
		self.keys_by_character = self._map_characters(computer)
		super().__init__(computer, aspect, fov, **animation_settings)

	@staticmethod
	def _map_characters(computer):
		keys_by_character = {}
		for key in computer.keys:
			if len(key.legend) == 1:
				keys_by_character[key.legend.upper()] = key
		for key in computer.keys:
			if len(key.shifted) == 1:
				keys_by_character.setdefault(key.shifted, key)
		return keys_by_character

	def restart(self):
		self.formed_at = None
		self.completed_at = None
		super().restart()

	def _offset(self, point, right=0.0, up=0.0, toward_viewer=0.0):
		"""point moved along the screen's right / up / toward-the-viewer directions."""
		return tuple(coordinate + right * screen_right - up * down + toward_viewer * viewer
		             for coordinate, screen_right, down, viewer
		             in zip(point, (1.0, 0.0, 0.0), self.screen_down, self.toward_viewer))

	def _caption_layout(self):
		"""World positions of the caption slots, the caption centre and the screen's right edge there."""
		spacing = self.caption_spacing * self.computer.key_pitch
		caption_width = len(self.text) * spacing
		fitting_distance = (caption_width / 2 / self.screen_fill) / math.tan(self.horizontal_half_fov)
		depth = max(self.caption_min_depth, fitting_distance - self.view_distance)
		centre = self._offset(self.view_target, toward_viewer=-depth)
		slots = tuple(self._offset(centre, right=(index - (len(self.text) - 1) / 2) * spacing)
		              for index in range(len(self.text)))
		right_edge = (self.view_distance + depth) * math.tan(self.horizontal_half_fov)
		return slots, centre, right_edge

	def _launch_keys(self, rng):
		flying = super()._launch_keys(rng)
		slots, centre, right_edge = self._caption_layout()

		first_slot_of_key, missing_slots = {}, []
		for slot, character in zip(slots, self.text):
			key = self.keys_by_character.get(character)
			if key is None:
				continue
			if key in first_slot_of_key:
				missing_slots.append((key, slot))
			else:
				first_slot_of_key[key] = slot

		self.caption_keys = []
		for index, flying_key in enumerate(flying):
			slot = first_slot_of_key.get(flying_key.key)
			if slot is None:
				continue
			start = flying_key.position
			far_point = self._offset(slot, rng.uniform(-self.caption_far_spread, self.caption_far_spread),
			                         rng.uniform(-self.caption_far_spread, self.caption_far_spread) / 2,
			                         -self.caption_far_depth * rng.uniform(0.8, 1.2))
			sweep = (rng.choice((-1.0, 1.0)) * rng.uniform(15.0, 25.0), rng.uniform(-10.0, 10.0), rng.uniform(-5.0, 5.0))
			outward = (
				start,
				self._offset(start, rng.uniform(-10.0, 10.0), rng.uniform(-6.0, 10.0), rng.uniform(6.0, 12.0)),
				self._offset(far_point, *sweep),
				far_point)
			homeward = (
				far_point,
				self._offset(far_point, *(-component for component in sweep)),
				self._offset(slot, rng.uniform(-12.0, 12.0), rng.uniform(-8.0, 8.0), -rng.uniform(4.0, 10.0)),
				slot)
			caption_key = CaptionKey(
				flying_key.key, (outward, homeward),
				rng.uniform(0.0, self.caption_stagger_seconds), self.caption_flight_seconds,
				self._random_axis(rng), rng.randint(*self.caption_spin_turns))
			flying[index] = caption_key
			self.caption_keys.append(caption_key)

		self.copy_keys = []
		for order, (key, slot) in enumerate(missing_slots):
			start = self._offset(self._offset(slot, right=centre[0] - slot[0]), right_edge + 3.0, rng.uniform(-4.0, 4.0))
			self.copy_keys.append(CaptionKey(
				key, ((start,
				       self._offset(start, -rng.uniform(5.0, 10.0), rng.uniform(-6.0, 6.0)),
				       self._offset(slot, rng.uniform(4.0, 8.0), rng.uniform(-4.0, 4.0)),
				       slot),),
				order * self.fill_stagger_seconds, self.fill_flight_seconds,
				self._random_axis(rng), rng.randint(*self.caption_spin_turns), hidden_before_start=True))
		return flying

	@staticmethod
	def _random_axis(rng):
		return rng.gauss(0.0, 1.0), rng.gauss(0.0, 1.0), rng.gauss(0.0, 1.0)

	@property
	def done(self):
		return self.completed_at is not None and self.elapsed >= self.completed_at + self.caption_hold_seconds

	def update(self):
		if self.done:
			return
		super().update()
		if not self.exploded:
			return
		if self.formed_at is None and all(caption_key.arrived for caption_key in self.caption_keys):
			self.formed_at = self.elapsed
		if self.formed_at is not None and self.elapsed >= self.formed_at + self.gap_wait_seconds:
			for copy_key in self.copy_keys:
				copy_key.update(self.frame_seconds)
			if self.completed_at is None and all(copy_key.arrived for copy_key in self.copy_keys):
				self.completed_at = self.elapsed

	def draw(self):
		super().draw()
		for copy_key in self.copy_keys:
			copy_key.draw(self.computer.slope_degrees)
