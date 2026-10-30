import math
import random

import pygame
from OpenGL.GL import *


def blend_colors(first_color, second_color, amount):
	return tuple(first + (second - first) * amount for first, second in zip(first_color, second_color))


class Spark:

	def __init__(self, position, velocity, lifetime_seconds):
		self.position = list(position)
		self.velocity = list(velocity)
		self.lifetime_seconds = lifetime_seconds
		self.age_seconds = 0.0

	def update(self, seconds, gravity):
		self.velocity[1] -= gravity * seconds
		for axis in range(3):
			self.position[axis] += self.velocity[axis] * seconds
		self.age_seconds += seconds

	@property
	def age_fraction(self):
		return min(1.0, self.age_seconds / self.lifetime_seconds)

	@property
	def expired(self):
		return self.age_seconds >= self.lifetime_seconds


class SparkShower:

	def __init__(self, outward_vertical_direction, sparks_per_second=280.0, speed_range=(2.5, 8.5),
	             lifetime_range_seconds=(0.25, 0.85), gravity=16.0, horizontal_spread=0.9,
	             backward_kick_against_laser_movement=0.7, toward_viewer_spread=0.8, trail_seconds=0.03,
	             hot_color=(1.0, 1.0, 0.8), cool_color=(1.0, 0.3, 0.03), line_width=2.0):
		self.outward_vertical_direction = outward_vertical_direction
		self.sparks_per_second = sparks_per_second
		self.speed_range = speed_range
		self.lifetime_range_seconds = lifetime_range_seconds
		self.gravity = gravity
		self.horizontal_spread = horizontal_spread
		self.backward_kick_against_laser_movement = backward_kick_against_laser_movement
		self.toward_viewer_spread = toward_viewer_spread
		self.trail_seconds = trail_seconds
		self.hot_color = hot_color
		self.cool_color = cool_color
		self.line_width = line_width
		self.sparks = []
		self.unspent_spark_emissions = 0.0

	def emit(self, seconds, emitter_position, laser_movement_direction):
		self.unspent_spark_emissions += self.sparks_per_second * seconds
		while self.unspent_spark_emissions >= 1.0:
			self.sparks.append(self._create_spark(emitter_position, laser_movement_direction))
			self.unspent_spark_emissions -= 1.0

	def _create_spark(self, emitter_position, laser_movement_direction):
		horizontal = (random.uniform(-self.horizontal_spread, self.horizontal_spread)
		              - laser_movement_direction * self.backward_kick_against_laser_movement)
		vertical = self.outward_vertical_direction * random.uniform(0.2, 1.0)
		toward_viewer = random.uniform(0.0, self.toward_viewer_spread)
		length = math.sqrt(horizontal * horizontal + vertical * vertical + toward_viewer * toward_viewer)
		speed = random.uniform(*self.speed_range)
		velocity = (horizontal / length * speed, vertical / length * speed, toward_viewer / length * speed)
		return Spark(emitter_position, velocity, random.uniform(*self.lifetime_range_seconds))

	def update(self, seconds):
		for spark in self.sparks:
			spark.update(seconds, self.gravity)
		self.sparks = [spark for spark in self.sparks if not spark.expired]

	def draw(self):
		if not self.sparks:
			return
		glLineWidth(self.line_width)
		glBegin(GL_LINES)
		for spark in self.sparks:
			color = blend_colors(self.hot_color, self.cool_color, spark.age_fraction)
			tail_position = [coordinate - velocity * self.trail_seconds
			                 for coordinate, velocity in zip(spark.position, spark.velocity)]
			glColor4f(*color, 0.0)
			glVertex3f(*tail_position)
			glColor4f(*color, 1.0 - spark.age_fraction)
			glVertex3f(*spark.position)
		glEnd()

	def clear(self):
		self.sparks = []
		self.unspent_spark_emissions = 0.0


class LaserLine:

	def __init__(self, surface_top_y, surface_bottom_y, core_color=(1.0, 0.9, 0.9), glow_color=(1.0, 0.06, 0.04),
	             core_half_width=0.025, glow_layer_half_widths=(0.07, 0.16, 0.34),
	             glow_layer_alphas=(0.85, 0.45, 0.2), flicker_strength=0.25, touch_point_flare_radius=0.45,
	             flare_segment_count=20):
		self.surface_top_y = surface_top_y
		self.surface_bottom_y = surface_bottom_y
		self.core_color = core_color
		self.glow_color = glow_color
		self.core_half_width = core_half_width
		self.glow_layer_half_widths = glow_layer_half_widths
		self.glow_layer_alphas = glow_layer_alphas
		self.flicker_strength = flicker_strength
		self.touch_point_flare_radius = touch_point_flare_radius
		self.flare_segment_count = flare_segment_count
		self.top_touch_point_spark_shower = SparkShower(outward_vertical_direction=1.0)
		self.bottom_touch_point_spark_shower = SparkShower(outward_vertical_direction=-1.0)
		self.x = 0.0
		self.movement_direction = 0.0
		self.switched_on = False

	def switch_on(self):
		self.switched_on = True

	def switch_off(self):
		self.switched_on = False

	def move_to(self, x, movement_direction):
		self.x = x
		self.movement_direction = movement_direction

	def reset(self):
		self.switch_off()
		self.top_touch_point_spark_shower.clear()
		self.bottom_touch_point_spark_shower.clear()

	def update(self, seconds):
		if self.switched_on:
			self.top_touch_point_spark_shower.emit(seconds, (self.x, self.surface_top_y, 0.0),
			                                       self.movement_direction)
			self.bottom_touch_point_spark_shower.emit(seconds, (self.x, self.surface_bottom_y, 0.0),
			                                          self.movement_direction)
		self.top_touch_point_spark_shower.update(seconds)
		self.bottom_touch_point_spark_shower.update(seconds)

	def draw(self):
		glPushAttrib(GL_ENABLE_BIT | GL_CURRENT_BIT | GL_COLOR_BUFFER_BIT | GL_LINE_BIT)
		glDisable(GL_LIGHTING)
		glDisable(GL_TEXTURE_2D)
		glEnable(GL_BLEND)
		glBlendFunc(GL_SRC_ALPHA, GL_ONE)
		if self.switched_on:
			self._draw_beam()
		self.top_touch_point_spark_shower.draw()
		self.bottom_touch_point_spark_shower.draw()
		glPopAttrib()

	def _draw_beam(self):
		flicker_scale = 1.0 + random.uniform(-self.flicker_strength, self.flicker_strength)
		for glow_half_width, glow_alpha in zip(self.glow_layer_half_widths, self.glow_layer_alphas):
			self._draw_soft_vertical_band(glow_half_width * flicker_scale, self.glow_color, glow_alpha)
		self._draw_soft_vertical_band(self.core_half_width, self.core_color, 1.0)
		for touch_point_y in (self.surface_top_y, self.surface_bottom_y):
			self._draw_touch_point_flare(touch_point_y, self.touch_point_flare_radius * flicker_scale)

	def _draw_soft_vertical_band(self, half_width, color, alpha):
		glBegin(GL_QUAD_STRIP)
		for edge_x, edge_alpha in ((self.x - half_width, 0.0), (self.x, alpha), (self.x + half_width, 0.0)):
			glColor4f(*color, edge_alpha)
			glVertex3f(edge_x, self.surface_bottom_y, 0.0)
			glVertex3f(edge_x, self.surface_top_y, 0.0)
		glEnd()

	def _draw_touch_point_flare(self, center_y, radius):
		glBegin(GL_TRIANGLE_FAN)
		glColor4f(*self.core_color, 1.0)
		glVertex3f(self.x, center_y, 0.0)
		glColor4f(*self.glow_color, 0.0)
		for step in range(self.flare_segment_count + 1):
			angle = 2 * math.pi * step / self.flare_segment_count
			glVertex3f(self.x + radius * math.cos(angle), center_y + radius * math.sin(angle), 0.0)
		glEnd()


def smooth_step(progress):
	return progress * progress * (3.0 - 2.0 * progress)


class PictureTexture:

	def __init__(self, surface):
		self.pixel_width, self.pixel_height = surface.get_size()
		self.aspect_ratio = self.pixel_width / self.pixel_height
		self.texture_id = self._upload_surface_as_texture(surface)

	@classmethod
	def load(cls, image_path):
		return cls(pygame.image.load(image_path).convert_alpha())

	@staticmethod
	def _upload_surface_as_texture(surface):
		width, height = surface.get_size()
		rgba_bytes_bottom_row_first = pygame.image.tobytes(surface, "RGBA", True)
		texture_id = glGenTextures(1)
		glBindTexture(GL_TEXTURE_2D, texture_id)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
		glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
		glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE,
		             rgba_bytes_bottom_row_first)
		return texture_id

	def draw_vertical_strip(self, left_edge_fraction, right_edge_fraction, picture_width, picture_height):
		if right_edge_fraction <= left_edge_fraction:
			return
		half_height = picture_height / 2
		left_x = (left_edge_fraction - 0.5) * picture_width
		right_x = (right_edge_fraction - 0.5) * picture_width
		glBindTexture(GL_TEXTURE_2D, self.texture_id)
		glBegin(GL_QUADS)
		glTexCoord2f(left_edge_fraction, 0.0)
		glVertex3f(left_x, -half_height, 0.0)
		glTexCoord2f(right_edge_fraction, 0.0)
		glVertex3f(right_x, -half_height, 0.0)
		glTexCoord2f(right_edge_fraction, 1.0)
		glVertex3f(right_x, half_height, 0.0)
		glTexCoord2f(left_edge_fraction, 1.0)
		glVertex3f(left_x, half_height, 0.0)
		glEnd()

	def destroy(self):
		glDeleteTextures([self.texture_id])


class LaserSweepSegment:

	def __init__(self, start_position_fraction, end_position_fraction, start_second, duration_seconds):
		self.start_position_fraction = start_position_fraction
		self.end_position_fraction = end_position_fraction
		self.start_second = start_second
		self.duration_seconds = duration_seconds

	@property
	def end_second(self):
		return self.start_second + self.duration_seconds

	@property
	def movement_direction(self):
		return math.copysign(1.0, self.end_position_fraction - self.start_position_fraction)

	def position_at(self, elapsed_seconds):
		progress = min(1.0, max(0.0, (elapsed_seconds - self.start_second) / self.duration_seconds))
		travelled = (self.end_position_fraction - self.start_position_fraction) * smooth_step(progress)
		return self.start_position_fraction + travelled


class LaserSweepPath:

	def __init__(self, signed_moves_in_picture_widths, sweep_speed_in_picture_widths_per_second,
	             shortest_move_seconds=0.2):
		self.sweep_speed_in_picture_widths_per_second = sweep_speed_in_picture_widths_per_second
		self.shortest_move_seconds = shortest_move_seconds
		self.segments = self._build_segments(signed_moves_in_picture_widths)
		self.total_seconds = self.segments[-1].end_second

	def _build_segments(self, signed_moves_in_picture_widths):
		segments = []
		position_fraction = 0.0
		start_second = 0.0
		for signed_move in signed_moves_in_picture_widths:
			end_position_fraction = min(1.0, max(0.0, position_fraction + signed_move))
			duration_seconds = max(self.shortest_move_seconds,
			                       abs(signed_move) / self.sweep_speed_in_picture_widths_per_second)
			segments.append(LaserSweepSegment(position_fraction, end_position_fraction, start_second, duration_seconds))
			position_fraction = end_position_fraction
			start_second += duration_seconds
		return segments

	def _segment_at(self, elapsed_seconds):
		for segment in self.segments:
			if elapsed_seconds < segment.end_second:
				return segment
		return None

	def position_at(self, elapsed_seconds):
		segment = self._segment_at(elapsed_seconds)
		if segment is None:
			return self.segments[-1].end_position_fraction
		return segment.position_at(elapsed_seconds)

	def movement_direction_at(self, elapsed_seconds):
		segment = self._segment_at(elapsed_seconds)
		return 0.0 if segment is None else segment.movement_direction

	def is_finished_at(self, elapsed_seconds):
		return elapsed_seconds >= self.total_seconds


class PictureTransition:

	def __init__(self, outgoing_picture, incoming_picture, laser_sweep_path):
		self.uses_laser_line = True
		self.outgoing_picture = outgoing_picture
		self.incoming_picture = incoming_picture
		self.laser_sweep_path = laser_sweep_path
		self.elapsed_seconds = 0.0

	def update(self, seconds):
		self.elapsed_seconds += seconds

	@property
	def laser_position_fraction(self):
		return self.laser_sweep_path.position_at(self.elapsed_seconds)

	@property
	def laser_movement_direction(self):
		return self.laser_sweep_path.movement_direction_at(self.elapsed_seconds)

	@property
	def finished(self):
		return self.laser_sweep_path.is_finished_at(self.elapsed_seconds)

	def draw_pictures(self, picture_width, picture_height):
		laser_position_fraction = self.laser_position_fraction
		self.incoming_picture.draw_vertical_strip(0.0, laser_position_fraction, picture_width, picture_height)
		self.outgoing_picture.draw_vertical_strip(laser_position_fraction, 1.0, picture_width, picture_height)
