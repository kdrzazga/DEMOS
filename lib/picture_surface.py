import math

from OpenGL.GL import *

from lib.laser_line import smooth_step
from lib.picture_crossfade import PictureCrossfade


class ScreenPlane:

	def __init__(self, aspect_ratio, field_of_view_degrees, camera_distance=20.0):
		self.camera_distance = camera_distance
		self.visible_height = 2 * camera_distance * math.tan(math.radians(field_of_view_degrees) / 2)
		self.visible_width = self.visible_height * aspect_ratio

	def world_point_from_screen_fractions(self, fraction_from_left, fraction_from_top):
		return (fraction_from_left - 0.5) * self.visible_width, (0.5 - fraction_from_top) * self.visible_height

	def screen_fractions_from_world_point(self, world_x, world_y):
		return world_x / self.visible_width + 0.5, 0.5 - world_y / self.visible_height


class PictureGlide:

	def __init__(self, start_screen_fractions, target_screen_fractions, glide_seconds, easing=smooth_step):
		self.start_screen_fractions = start_screen_fractions
		self.target_screen_fractions = target_screen_fractions
		self.glide_seconds = glide_seconds
		self.easing = easing
		self.elapsed_seconds = 0.0

	def update(self, seconds):
		self.elapsed_seconds += seconds

	@property
	def progress(self):
		return min(1.0, self.elapsed_seconds / self.glide_seconds)

	@property
	def finished(self):
		return self.elapsed_seconds >= self.glide_seconds

	@property
	def current_screen_fractions(self):
		eased_progress = self.easing(self.progress)
		return tuple(start + (target - start) * eased_progress
		             for start, target in zip(self.start_screen_fractions, self.target_screen_fractions))


class PictureSurface:

	def __init__(self, picture, screen_plane, height_in_screen_heights, swing_amplitude_degrees=0.0,
	             swing_period_seconds=1.6):
		self.picture = picture
		self.screen_plane = screen_plane
		self.height_in_screen_heights = height_in_screen_heights
		self.picture_height = screen_plane.visible_height * height_in_screen_heights
		self.picture_width = self.picture_height * self.picture.aspect_ratio
		self.width_in_screen_widths = self.picture_width / screen_plane.visible_width
		self.swing_amplitude_degrees = swing_amplitude_degrees
		self.swing_period_seconds = swing_period_seconds
		self.center_screen_fractions = (0.5, 0.5)
		self.active_glide = None
		self.swing_elapsed_seconds = 0.0
		self.opacity = 1.0
		self.horizontal_scale = 1.0
		self.active_crossfade = None

	def show_picture(self, picture):
		self.picture = picture
		self.active_crossfade = None
		self.horizontal_scale = 1.0

	def crossfade_to(self, incoming_picture, fade_seconds):
		self.active_crossfade = PictureCrossfade(self.picture, incoming_picture, fade_seconds)

	@property
	def world_center_point(self):
		return self.screen_plane.world_point_from_screen_fractions(*self.center_screen_fractions)

	def place_center_at(self, center_screen_fractions):
		self.center_screen_fractions = center_screen_fractions
		self.active_glide = None

	def glide_center_to(self, target_screen_fractions, glide_seconds, easing=smooth_step):
		self.active_glide = PictureGlide(self.center_screen_fractions, target_screen_fractions, glide_seconds, easing)
		self.swing_elapsed_seconds = 0.0

	@property
	def is_gliding(self):
		return self.active_glide is not None and not self.active_glide.finished

	def center_fractions_with_bottom_edge_on_screen_bottom(self, fraction_from_left):
		return fraction_from_left, 1.0 - self.height_in_screen_heights / 2

	def center_fractions_in_top_right_corner(self, margin_in_screen_heights=0.0):
		horizontal_margin = margin_in_screen_heights * self.screen_plane.visible_height / self.screen_plane.visible_width
		return (1.0 - self.width_in_screen_widths / 2 - horizontal_margin,
		        self.height_in_screen_heights / 2 + margin_in_screen_heights)

	def center_fractions_just_beyond_left_edge(self, fraction_from_top):
		return -self.width_in_screen_widths / 2, fraction_from_top

	def center_fractions_just_beyond_right_edge(self, fraction_from_top):
		return 1.0 + self.width_in_screen_widths / 2, fraction_from_top

	def center_fractions_just_below_bottom_edge(self):
		fraction_from_left, current_fraction_from_top = self.center_screen_fractions
		top_edge_fraction_from_top = current_fraction_from_top - self.height_in_screen_heights / 2
		return fraction_from_left, max(1.0, top_edge_fraction_from_top) + self.height_in_screen_heights / 2

	def world_point_from_picture_pixel(self, pixel_x, pixel_y):
		center_x, center_y = self.world_center_point
		shown_width = self.picture_width * self.horizontal_scale
		return (center_x + (pixel_x / self.picture.pixel_width - 0.5) * shown_width,
		        center_y + (0.5 - pixel_y / self.picture.pixel_height) * self.picture_height)

	@property
	def world_top_center_point(self):
		center_x, center_y = self.world_center_point
		return center_x, center_y + self.picture_height / 2

	def update(self, seconds):
		self.swing_elapsed_seconds += seconds
		self._advance_crossfade(seconds)
		if self.active_glide is None:
			return
		self.active_glide.update(seconds)
		self.center_screen_fractions = self.active_glide.current_screen_fractions

	def _advance_crossfade(self, seconds):
		if self.active_crossfade is None:
			return
		self.active_crossfade.update(seconds)
		if self.active_crossfade.finished:
			self.picture = self.active_crossfade.incoming_picture
			self.active_crossfade = None

	def _current_swing_degrees(self):
		if self.active_glide is None:
			return 0.0
		swing_strength = 1.0 - self.active_glide.progress
		swing_angle = 2 * math.pi * self.swing_elapsed_seconds / self.swing_period_seconds
		return self.swing_amplitude_degrees * swing_strength * math.sin(swing_angle)

	def draw(self):
		center_x, center_y = self.world_center_point
		glPushAttrib(GL_ENABLE_BIT | GL_CURRENT_BIT | GL_COLOR_BUFFER_BIT)
		glDisable(GL_LIGHTING)
		glDisable(GL_DEPTH_TEST)
		glDisable(GL_CULL_FACE)
		glEnable(GL_TEXTURE_2D)
		glEnable(GL_BLEND)
		glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
		glMatrixMode(GL_MODELVIEW)
		glPushMatrix()
		glLoadIdentity()
		glTranslatef(center_x, center_y, -self.screen_plane.camera_distance)
		glRotatef(self._current_swing_degrees(), 0.0, 1.0, 0.0)
		glScalef(self.horizontal_scale, 1.0, 1.0)
		glColor4f(1.0, 1.0, 1.0, self.opacity)
		if self.active_crossfade is not None:
			self.active_crossfade.draw_pictures(self.picture_width, self.picture_height)
		else:
			self.picture.draw_vertical_strip(0.0, 1.0, self.picture_width, self.picture_height)
		glPopMatrix()
		glPopAttrib()

	def destroy(self):
		self.picture.destroy()
