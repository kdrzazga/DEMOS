"""A cassette shows off, then goes into the Datasette and the tape is played.

``CassetteIntoDatasette`` owns the whole sequence and its camera (screen
positions such as "the top right corner" need one): build a Datasette and a
Cassette, then call ``update(seconds)`` and ``draw()`` every frame.

1. The cassette arrives from the distance, side A toward the viewer, and
   settles in front of the camera.
2. It spins once around (360 degrees).
3. Super fast forward, then super rewind (super_wind_minutes_per_second, one
   minute of tape per 0.1 s), swaying all the while.
4. It moves to the top right corner of the screen.
5. The Datasette arrives from the distance and sways for 2 seconds.
6. EJECT opens the lid; the cassette flies into the open lid (the C2N's holder
   is in the lid), sliding in along it, and rides down as the lid closes,
   ending with its hubs on the spindles.
7. "Press play on tape" is heard, PLAY is pressed and the tape plays.

Poses are a position (the cassette's centre, the Datasette's offset) and an
orientation quaternion, so facing the camera, spinning, swaying and lying in
the lid all blend into each other.
"""

import math
import os

import pygame
from OpenGL.GL import *


def axis_angle(axis, degrees):
	"""Quaternion (w, x, y, z) turning like glRotatef(degrees, *axis)."""
	half = math.radians(degrees) / 2
	length = math.sqrt(sum(c * c for c in axis))
	return (math.cos(half), *(c / length * math.sin(half) for c in axis))


def multiply(a, b):
	aw, ax, ay, az = a
	bw, bx, by, bz = b
	return (aw * bw - ax * bx - ay * by - az * bz,
	        aw * bx + ax * bw + ay * bz - az * by,
	        aw * by - ax * bz + ay * bw + az * bx,
	        aw * bz + ax * by - ay * bx + az * bw)


def chain(*quaternions):
	"""Product left to right - the same order as the glRotatef calls would be."""
	result = (1.0, 0.0, 0.0, 0.0)
	for quaternion in quaternions:
		result = multiply(result, quaternion)
	return result


def rotate(quaternion, vector):
	w, x, y, z = multiply(multiply(quaternion, (0.0, *vector)), (quaternion[0], *(-c for c in quaternion[1:])))
	return x, y, z


def slerp(a, b, t):
	dot = sum(p * q for p, q in zip(a, b))
	if dot < 0:
		b, dot = tuple(-c for c in b), -dot
	if dot > 0.9995:
		blended = tuple(p + (q - p) * t for p, q in zip(a, b))
	else:
		angle = math.acos(dot)
		blended = tuple((math.sin((1 - t) * angle) * p + math.sin(t * angle) * q) / math.sin(angle) for p, q in zip(a, b))
	length = math.sqrt(sum(c * c for c in blended))
	return tuple(c / length for c in blended)


def gl_matrix(quaternion):
	"""Column-major 4x4 rotation for glMultMatrixf."""
	w, x, y, z = quaternion
	return (1 - 2 * (y * y + z * z), 2 * (x * y + w * z), 2 * (x * z - w * y), 0.0,
	        2 * (x * y - w * z), 1 - 2 * (x * x + z * z), 2 * (y * z + w * x), 0.0,
	        2 * (x * z + w * y), 2 * (y * z - w * x), 1 - 2 * (x * x + y * y), 0.0,
	        0.0, 0.0, 0.0, 1.0)


def lerp(start, end, t):
	return tuple(s + (e - s) * t for s, e in zip(start, end))


def ease_out(t):
	return 1 - (1 - t) ** 3


def ease_in_out(t):
	return t * t * (3 - 2 * t)


IDENTITY = (1.0, 0.0, 0.0, 0.0)


class CassetteIntoDatasette:

	def __init__(self, datasette, cassette, aspect, fov, start_roll_position=20.0, play_sound=True,
	             sound_path=os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources", "PressPlayOnTape.mp3")):
		self.datasette = datasette
		self.cassette = cassette
		self.aspect = aspect
		self.fov = fov
		self.start_roll_position = start_roll_position

		self.camera_target = (-1.5, 2.5, -0.5)
		self.camera_yaw = -20.0
		self.camera_pitch = 32.0
		self.camera_distance = 46.0
		self.light_direction = (-0.35, 1.0, 0.7, 0.0)

		self.cassette_far_depth = 300.0
		self.cassette_present_depth = 20.0
		self.cassette_arrival_roll = 180.0
		self.corner_screen = (0.72, 0.66)
		self.corner_depth = 40.0
		self.datasette_far_distance = 220.0
		self.datasette_pivot = (-1.0, 2.0, 0.0)

		self.super_wind_minutes_per_second = 10.0
		self.play_minutes_per_second = 1 / 15
		self.wind_sway_degrees = 9.0
		self.corner_sway_degrees = 3.0
		self.datasette_sway_degrees = 4.0
		self.sway_hertz = 0.9
		self.key_tap_seconds = 0.25
		self.seat_height = 0.25
		self.flight_approach_distance = 6.0
		self.voice_tail_seconds = 0.3

		self.sound = self._load_sound(sound_path) if play_sound else None
		voice_seconds = (self.sound.get_length() if self.sound else 1.6) + self.voice_tail_seconds
		self.phases = (("cassette_arrive", 2.5), ("cassette_spin", 1.5), ("super_fast_forward", 2.0),
		               ("super_rewind", 2.0), ("cassette_to_corner", 1.2), ("datasette_arrive", 2.0),
		               ("datasette_sway", 2.0), ("open", 1.2), ("insert", 2.0), ("close", 1.2),
		               ("voice", voice_seconds), ("play", 3.0))
		self.restart()

	def _load_sound(self, sound_path):
		if not pygame.mixer.get_init():
			pygame.mixer.init()
		return pygame.mixer.Sound(sound_path)

	def restart(self):
		for button in self.datasette.buttons:
			button.held = button.latched = False
			button.travel = 0.0
		self.datasette.door.is_open = False
		self.datasette.door.angle = 0.0
		self.cassette.roll_position = self.start_roll_position
		if self.sound:
			self.sound.stop()
		self.phase_index = 0
		self.phase_elapsed = 0.0
		self.sway_seconds = 0.0
		self.done = False
		self._tapped_button = None
		self._tap_elapsed = 0.0
		self._insert_start = None
		self._enter_phase()

	@property
	def phase(self):
		return self.phases[self.phase_index][0]

	def _phase_progress(self):
		return min(1.0, self.phase_elapsed / self.phases[self.phase_index][1])

	def _enter_phase(self):
		datasette = self.datasette
		if self.phase == "open":
			self._tap(datasette.eject_button)
		elif self.phase == "insert":
			self._insert_start = self._corner_pose()
		elif self.phase == "close":
			datasette.door.is_open = False
		elif self.phase == "voice" and self.sound:
			self.sound.play()
		elif self.phase == "play":
			self._tap(datasette.play_button)

	def _tap(self, button):
		self.datasette.push(button, True)
		self._tapped_button = button
		self._tap_elapsed = 0.0

	def _release_tap(self, seconds):
		if self._tapped_button is None:
			return
		self._tap_elapsed += seconds
		if self._tap_elapsed >= self.key_tap_seconds:
			self.datasette.push(self._tapped_button, False)
			self._tapped_button = None

	def _move_tape(self, seconds):
		if self.phase == "super_fast_forward":
			self.cassette.wind(self.super_wind_minutes_per_second * seconds)
		elif self.phase == "super_rewind":
			self.cassette.wind(-self.super_wind_minutes_per_second * seconds)
		elif self.datasette.play_button.latched:
			self.cassette.wind(self.play_minutes_per_second * seconds)

	def update(self, seconds):
		self._release_tap(seconds)
		self._move_tape(seconds)
		self.datasette.update()
		self.sway_seconds += seconds
		if self.done:
			return
		self.phase_elapsed += seconds
		if self.phase_elapsed >= self.phases[self.phase_index][1]:
			if self.phase_index + 1 < len(self.phases):
				self.phase_index += 1
				self.phase_elapsed = 0.0
				self._enter_phase()
			else:
				self.done = True


	def _camera_to_world(self):
		"""Orientation of the camera in the world (inverse of the view rotation)."""
		return chain(axis_angle((0, 1, 0), -self.camera_yaw), axis_angle((1, 0, 0), -self.camera_pitch))

	def _camera_point(self, screen_x, screen_y, depth):
		"""World point at `depth` in front of the camera that projects to
		(screen_x, screen_y) in -1..1 screen coordinates (y up)."""
		tan_half = math.tan(math.radians(self.fov / 2))
		in_camera = (screen_x * depth * tan_half * self.aspect, screen_y * depth * tan_half,
		             self.camera_distance - depth)
		return tuple(t + o for t, o in zip(self.camera_target, rotate(self._camera_to_world(), in_camera)))

	def _facing_camera(self, *turns):
		"""Side A toward the viewer, label upright, with extra turns in camera
		space applied before standing it up."""
		return chain(self._camera_to_world(), *turns, axis_angle((1, 0, 0), 90.0))

	def _sway(self, degrees):
		phase = 2 * math.pi * self.sway_hertz * self.sway_seconds
		return chain(axis_angle((0, 0, 1), degrees * math.sin(phase)),
		             axis_angle((1, 0, 0), degrees * 0.5 * math.sin(phase * 1.7 + 1.0)))

	def _present_position(self):
		return self._camera_point(0.0, 0.0, self.cassette_present_depth)

	def _corner_pose(self):
		return (self._camera_point(*self.corner_screen, self.corner_depth),
		        self._facing_camera(self._sway(self.corner_sway_degrees)))

	def _seated_centre_offset(self):
		"""Cassette centre relative to the hinge when it lies in the closed
		compartment with its hubs on the spindles."""
		door = self.datasette.door
		spindle_z = door.hub_centres()[0][1]
		return (0.0, -door.compartment_depth + self.seat_height + self.cassette.thickness / 2,
		        spindle_z - self.cassette.hub_z)

	def _lid_pose(self, lid_degrees):
		"""The cassette held in the lid open at lid_degrees."""
		lid = axis_angle((1, 0, 0), -lid_degrees)
		hinge = self.datasette.hinge_position()
		return tuple(h + o for h, o in zip(hinge, rotate(lid, self._seated_centre_offset()))), lid

	def _insert_pose(self, progress):
		"""Quadratic Bezier from the corner into the open lid, arriving along the
		lid's slope; the orientation slerps from the corner's to the lid's."""
		open_degrees = self.datasette.door.open_degrees
		target, target_orientation = self._lid_pose(open_degrees)
		slope = math.radians(open_degrees)
		approach = tuple(t + self.flight_approach_distance * d
		                 for t, d in zip(target, (0.0, math.sin(slope), math.cos(slope))))
		start, start_orientation = self._insert_start
		t = ease_in_out(progress)
		position = tuple((1 - t) ** 2 * s + 2 * (1 - t) * t * a + t * t * e for s, a, e in zip(start, approach, target))
		return position, slerp(start_orientation, target_orientation, t)

	def cassette_pose(self):
		phase, progress = self.phase, self._phase_progress()
		if phase == "cassette_arrive":
			far = self._camera_point(0.0, 0.0, self.cassette_far_depth)
			t = ease_out(progress)
			return (lerp(far, self._present_position(), t),
			        self._facing_camera(axis_angle((0, 0, 1), self.cassette_arrival_roll * (1 - t))))
		if phase == "cassette_spin":
			return self._present_position(), self._facing_camera(axis_angle((0, 1, 0), 360.0 * ease_in_out(progress)))
		if phase in ("super_fast_forward", "super_rewind"):
			return self._present_position(), self._facing_camera(self._sway(self.wind_sway_degrees))
		if phase == "cassette_to_corner":
			t = ease_in_out(progress)
			corner_position, _ = self._corner_pose()
			sway = self.wind_sway_degrees + (self.corner_sway_degrees - self.wind_sway_degrees) * t
			return lerp(self._present_position(), corner_position, t), self._facing_camera(self._sway(sway))
		if phase in ("datasette_arrive", "datasette_sway", "open"):
			return self._corner_pose()
		if phase == "insert":
			return self._insert_pose(progress)
		return self._lid_pose(self.datasette.door.angle)

	def datasette_pose(self):
		"""(offset, orientation about datasette_pivot); None before it arrives."""
		phase, progress = self.phase, self._phase_progress()
		if self.phase_index < [name for name, _ in self.phases].index("datasette_arrive"):
			return None
		if phase == "datasette_arrive":
			forward = rotate(self._camera_to_world(), (0.0, 0.0, -1.0))
			far = tuple(c * self.datasette_far_distance for c in forward)
			return lerp(far, (0.0, 0.0, 0.0), ease_out(progress)), IDENTITY
		if phase == "datasette_sway":
			fade = math.sin(math.pi * progress)
			return (0.0, 0.0, 0.0), self._sway(self.datasette_sway_degrees * fade)
		return (0.0, 0.0, 0.0), IDENTITY


	def _place_datasette(self, pose):
		offset, orientation = pose
		glTranslatef(*offset)
		glTranslatef(*self.datasette_pivot)
		glMultMatrixf(gl_matrix(orientation))
		glTranslatef(*(-c for c in self.datasette_pivot))

	def draw(self):
		glLoadIdentity()
		glTranslatef(0.0, 0.0, -self.camera_distance)
		glRotatef(self.camera_pitch, 1.0, 0.0, 0.0)
		glRotatef(self.camera_yaw, 0.0, 1.0, 0.0)
		glLightfv(GL_LIGHT0, GL_POSITION, self.light_direction)
		glTranslatef(*(-c for c in self.camera_target))

		datasette_pose = self.datasette_pose()
		if datasette_pose:
			glPushMatrix()
			self._place_datasette(datasette_pose)
			self.datasette.draw_body()
			glPopMatrix()

		position, orientation = self.cassette_pose()
		glPushMatrix()
		glTranslatef(*position)
		glMultMatrixf(gl_matrix(orientation))
		glTranslatef(0.0, -self.cassette.thickness / 2, 0.0)
		self.cassette.draw()
		glPopMatrix()

		if datasette_pose:
			glPushMatrix()
			self._place_datasette(datasette_pose)
			self.datasette.draw_lid()
			glPopMatrix()
