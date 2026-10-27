import math
import random

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
