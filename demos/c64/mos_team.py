import math
import os

from OpenGL.GL import *

from lib.laser_line import LaserLine, LaserSweepPath, PictureTexture, PictureTransition, smooth_step
from lib.caption_sequence import CaptionSequence
from lib.flying_logo import FlyingLogo
from lib.picture_crossfade import PictureCrossfade
from lib.pointed_name_label import PointedNameLabel, ScreenSpaceProjector

LOGO_FILE_NAME = "logo.png"
LOGO_FLIGHT_SECONDS = 6.5
LOGO_CAPTION_LINES = ("In 1975 MOS Technology started working", "on the 65xx processor family")


class TeamMemberAnnotation:

	def __init__(self, name, picture_pixel_point, appear_second, disappear_second, label):
		self.name = name
		self.picture_pixel_point = picture_pixel_point
		self.appear_second = appear_second
		self.disappear_second = disappear_second
		self.label = label

	def is_visible_at(self, timeline_seconds):
		return self.appear_second <= timeline_seconds < self.disappear_second

	def opacity_at(self, timeline_seconds, fade_seconds):
		seconds_since_appearing = timeline_seconds - self.appear_second
		seconds_until_disappearing = self.disappear_second - timeline_seconds
		return max(0.0, min(1.0, seconds_since_appearing / fade_seconds, seconds_until_disappearing / fade_seconds))

	def destroy(self):
		self.label.destroy()


class MosTeam:

	def __init__(self, aspect_ratio, field_of_view_degrees, picture_directory=None,
	             picture_file_names=("MOS.png", "MOS2.png", "MOS3.png", "MOS4.png", "MOS5.png"),
	             transition_styles=("laser_sweep", "laser_sweep", "laser_sweep", "color_fade"),
	             color_fade_seconds=2.0, hold_seconds_before_color_fade=0.2, picture_height=10.0,
	             screen_fill_fraction=0.8, drive_in_seconds=2.0, drive_in_entry_yaw_degrees=-35.0,
	             drive_in_offscreen_margin_in_picture_widths=0.15,
	             opening_hold_seconds=1.0, hold_seconds_between_transitions=1.5,
	             closing_hold_seconds=1.5,
	             laser_signed_moves_in_picture_widths=(0.40, -0.25, 0.45, -0.30, 0.30, -0.05, 0.40, -0.10, 0.15),
	             laser_sweep_speed_in_picture_widths_per_second=0.7, sway_yaw_amplitude_degrees=14.0,
	             sway_pitch_amplitude_degrees=5.0, sway_period_seconds=9.0,
	             team_member_annotations=(("Terry Holdt", (480, 400), 0.0, 2.0),
	                                      ("Wilbur Mathys", (85, 245), 1.0, 3.0),
	                                      ("Sydney-Anne Holt", (715, 300), 2.0, 4.0),
	                                      ("William Mensch", (210, 300), 3.0, 5.0),
	                                      ("Michael Jaynes", (630, 310), 4.0, 6.0),
	                                      ("Rodney Orgill", (280, 280), 5.0, 7.0),
	                                      ("Harry Bawcom", (550, 245), 6.0, 8.0),
	                                      ("Ray Hirt", (390, 210), 7.0, 9.0),
	                                      ("CHUCK PEDDLE", (470, 240), 8.0, 10.0)),
	             annotations_start_with_transition_number=2, most_annotations_visible_at_once=2,
	             annotation_fade_seconds=0.25, annotation_design_screen_height=800.0,
	             closing_captions=("Photo transformation is not AI", "It is just GIMP :)"), seconds_per_closing_caption=1.25,
	             pause_seconds_between_closing_captions=0.15, closing_caption_color=(230, 40, 40),
	             zoom_target_pixel_rectangle=((445, 222), (500, 280)), zoom_seconds=1.25,
	             zoom_target_screen_fill_fraction=0.85):

		self.aspect_ratio = aspect_ratio
		self.field_of_view_degrees = field_of_view_degrees
		self.picture_directory = picture_directory or os.path.join(
			os.path.dirname(os.path.abspath(__file__)), "resources", "history", "mos")
		self.transition_styles = transition_styles
		self.color_fade_seconds = color_fade_seconds
		self.hold_seconds_before_color_fade = hold_seconds_before_color_fade
		self.picture_height = picture_height
		self.screen_fill_fraction = screen_fill_fraction
		self.drive_in_seconds = drive_in_seconds
		self.drive_in_entry_yaw_degrees = drive_in_entry_yaw_degrees
		self.drive_in_offscreen_margin_in_picture_widths = drive_in_offscreen_margin_in_picture_widths
		self.opening_hold_seconds = opening_hold_seconds
		self.hold_seconds_between_transitions = hold_seconds_between_transitions
		self.closing_hold_seconds = closing_hold_seconds
		self.laser_signed_moves_in_picture_widths = laser_signed_moves_in_picture_widths
		self.laser_sweep_speed_in_picture_widths_per_second = laser_sweep_speed_in_picture_widths_per_second
		self.sway_yaw_amplitude_degrees = sway_yaw_amplitude_degrees
		self.sway_pitch_amplitude_degrees = sway_pitch_amplitude_degrees
		self.sway_period_seconds = sway_period_seconds
		self.annotations_start_with_transition_number = annotations_start_with_transition_number
		self.most_annotations_visible_at_once = most_annotations_visible_at_once
		self.annotation_fade_seconds = annotation_fade_seconds
		self.annotation_design_screen_height = annotation_design_screen_height
		self.zoom_target_pixel_rectangle = zoom_target_pixel_rectangle
		self.zoom_seconds = zoom_seconds
		self.zoom_target_screen_fill_fraction = zoom_target_screen_fill_fraction

		self.pictures = [PictureTexture.load(os.path.join(self.picture_directory, file_name))
		                 for file_name in picture_file_names]
		self.picture_width = picture_height * self.pictures[0].aspect_ratio
		self.camera_distance = self._camera_distance_that_fits_picture_on_screen()
		self.drive_in_start_x = self._drive_in_start_x_just_beyond_right_screen_edge()
		self.zoom_target_center, self.zoom_target_scale = self._zoom_target_center_and_scale()
		self.laser_line = LaserLine(surface_top_y=picture_height / 2, surface_bottom_y=-picture_height / 2)
		self.team_member_annotations = self._build_team_member_annotations(team_member_annotations)
		self.closing_caption_sequence = CaptionSequence(closing_captions, seconds_per_caption=seconds_per_closing_caption,
		                                                pause_seconds_between_captions=pause_seconds_between_closing_captions,
		                                                text_color=closing_caption_color,
		                                                screen_scale=self._screen_scale())
		self.flying_logo = FlyingLogo(os.path.join(self.picture_directory, LOGO_FILE_NAME), aspect_ratio,
		                              field_of_view_degrees, self.camera_distance, flight_seconds=LOGO_FLIGHT_SECONDS,
		                              settled_caption_lines=LOGO_CAPTION_LINES)
		self.restart()

	def _screen_scale(self):
		return glGetIntegerv(GL_VIEWPORT)[3] / self.annotation_design_screen_height

	def _build_team_member_annotations(self, annotation_settings):
		screen_scale = self._screen_scale()
		return [TeamMemberAnnotation(name, picture_pixel_point, appear_second, disappear_second,
		                             PointedNameLabel(name, screen_scale=screen_scale))
		        for name, picture_pixel_point, appear_second, disappear_second in annotation_settings]

	def _camera_distance_that_fits_picture_on_screen(self):
		vertical_half_angle_tangent = math.tan(math.radians(self.field_of_view_degrees) / 2)
		horizontal_half_angle_tangent = vertical_half_angle_tangent * self.aspect_ratio
		distance_fitting_height = self.picture_height / 2 / self.screen_fill_fraction / vertical_half_angle_tangent
		distance_fitting_width = self.picture_width / 2 / self.screen_fill_fraction / horizontal_half_angle_tangent
		return max(distance_fitting_height, distance_fitting_width)

	def _zoom_target_center_and_scale(self):
		(left_pixel, top_pixel), (right_pixel, bottom_pixel) = self.zoom_target_pixel_rectangle
		left_x, top_y, _ = self._picture_point_from_pixel_point((left_pixel, top_pixel))
		right_x, bottom_y, _ = self._picture_point_from_pixel_point((right_pixel, bottom_pixel))
		target_center = ((left_x + right_x) / 2, (top_y + bottom_y) / 2)
		visible_height = 2 * self.camera_distance * math.tan(math.radians(self.field_of_view_degrees) / 2)
		visible_width = visible_height * self.aspect_ratio
		scale_fitting_height = visible_height * self.zoom_target_screen_fill_fraction / abs(top_y - bottom_y)
		scale_fitting_width = visible_width * self.zoom_target_screen_fill_fraction / abs(right_x - left_x)
		return target_center, min(scale_fitting_height, scale_fitting_width)

	def _drive_in_start_x_just_beyond_right_screen_edge(self):
		vertical_half_angle_tangent = math.tan(math.radians(self.field_of_view_degrees) / 2)
		visible_half_width = self.camera_distance * vertical_half_angle_tangent * self.aspect_ratio
		offscreen_margin = self.picture_width * self.drive_in_offscreen_margin_in_picture_widths
		return visible_half_width + self.picture_width / 2 + offscreen_margin

	def restart(self):
		self.flying_logo.restart()
		self.total_elapsed_seconds = 0.0
		self.drive_in_elapsed_seconds = 0.0
		self.shown_picture_index = 0
		self.active_transition = None
		self.remaining_hold_seconds = self.opening_hold_seconds
		self.finished = False
		self.started_transition_count = 0
		self.annotation_timeline_seconds = None
		self.zoom_elapsed_seconds = None
		self.laser_line.reset()
		self.closing_caption_sequence.reset()

	@property
	def done(self):
		return self.finished

	@property
	def is_showing_last_picture(self):
		return self.shown_picture_index >= len(self.pictures) - 1

	@property
	def all_annotations_have_disappeared(self):
		if not self.team_member_annotations:
			return True
		if self.annotation_timeline_seconds is None:
			return False
		last_disappear_second = max(annotation.disappear_second for annotation in self.team_member_annotations)
		return self.annotation_timeline_seconds >= last_disappear_second

	@property
	def is_zooming_to_target(self):
		return self.zoom_elapsed_seconds is not None and not self.finished

	@property
	def eased_zoom_progress(self):
		if self.zoom_elapsed_seconds is None:
			return 0.0
		return smooth_step(min(1.0, self.zoom_elapsed_seconds / self.zoom_seconds))

	@property
	def is_driving_in(self):
		return self.drive_in_elapsed_seconds < self.drive_in_seconds

	@property
	def eased_drive_in_progress(self):
		progress = min(1.0, self.drive_in_elapsed_seconds / self.drive_in_seconds)
		return 1.0 - (1.0 - progress) ** 3

	def update(self, seconds):
		if not self.flying_logo.finished:
			self.flying_logo.update(seconds)
			return
		self.total_elapsed_seconds += seconds
		if self.annotation_timeline_seconds is not None:
			self.annotation_timeline_seconds += seconds
		if self.is_driving_in:
			self.drive_in_elapsed_seconds += seconds
		elif self.active_transition is not None:
			self._advance_active_transition(seconds)
		elif self.is_zooming_to_target:
			self._advance_zoom(seconds)
		elif not self.finished:
			self._advance_hold(seconds)
		self.laser_line.update(seconds)
		self.closing_caption_sequence.update(seconds)

	def _advance_active_transition(self, seconds):
		self.active_transition.update(seconds)
		if self.active_transition.uses_laser_line:
			self._move_laser_line_to_transition_position()
		if self.active_transition.finished:
			self.active_transition = None
			self.laser_line.switch_off()
			self.shown_picture_index += 1
			if self.is_showing_last_picture:
				self.closing_caption_sequence.start()
			self.remaining_hold_seconds = self._hold_seconds_after_reaching_shown_picture()

	def _hold_seconds_after_reaching_shown_picture(self):
		if self.is_showing_last_picture:
			return self.closing_hold_seconds
		if self.transition_styles[self.shown_picture_index] == "color_fade":
			return self.hold_seconds_before_color_fade
		return self.hold_seconds_between_transitions

	def _advance_hold(self, seconds):
		self.remaining_hold_seconds -= seconds
		if self.remaining_hold_seconds > 0.0:
			return
		if self.is_showing_last_picture:
			if self.all_annotations_have_disappeared and self.closing_caption_sequence.finished:
				self.zoom_elapsed_seconds = 0.0
		else:
			self._start_transition_to_next_picture()

	def _advance_zoom(self, seconds):
		self.zoom_elapsed_seconds += seconds
		if self.zoom_elapsed_seconds >= self.zoom_seconds:
			self.finished = True

	def _start_transition_to_next_picture(self):
		outgoing_picture = self.pictures[self.shown_picture_index]
		incoming_picture = self.pictures[self.shown_picture_index + 1]
		if self.transition_styles[self.shown_picture_index] == "color_fade":
			self.active_transition = PictureCrossfade(outgoing_picture, incoming_picture, self.color_fade_seconds)
		else:
			self._start_laser_sweep_transition(outgoing_picture, incoming_picture)
		self.started_transition_count += 1
		if self.started_transition_count == self.annotations_start_with_transition_number:
			self.annotation_timeline_seconds = 0.0

	def _start_laser_sweep_transition(self, outgoing_picture, incoming_picture):
		laser_sweep_path = LaserSweepPath(self.laser_signed_moves_in_picture_widths,
		                                  self.laser_sweep_speed_in_picture_widths_per_second)
		self.active_transition = PictureTransition(outgoing_picture, incoming_picture, laser_sweep_path)
		self._move_laser_line_to_transition_position()
		self.laser_line.switch_on()

	def _move_laser_line_to_transition_position(self):
		laser_x = (self.active_transition.laser_position_fraction - 0.5) * self.picture_width
		self.laser_line.move_to(laser_x, self.active_transition.laser_movement_direction)

	def draw(self):
		if self.finished:
			return
		if not self.flying_logo.finished:
			self.flying_logo.draw()
			return
		glPushAttrib(GL_ENABLE_BIT | GL_CURRENT_BIT | GL_COLOR_BUFFER_BIT)
		glDisable(GL_LIGHTING)
		glDisable(GL_DEPTH_TEST)
		glMatrixMode(GL_MODELVIEW)
		glPushMatrix()
		glLoadIdentity()
		glTranslatef(0.0, 0.0, -self.camera_distance)
		self._apply_drive_in_offset_and_turn()
		self._apply_sway()
		self._apply_zoom_to_target()
		self._draw_pictures()
		self.laser_line.draw()
		self._draw_team_member_annotations()
		self.closing_caption_sequence.draw()
		glPopMatrix()
		glPopAttrib()

	def _currently_visible_annotations(self):
		if self.annotation_timeline_seconds is None:
			return []
		visible_annotations = [annotation for annotation in self.team_member_annotations
		                       if annotation.is_visible_at(self.annotation_timeline_seconds)]
		visible_annotations.sort(key=lambda annotation: annotation.appear_second)
		return visible_annotations[-self.most_annotations_visible_at_once:]

	def _picture_point_from_pixel_point(self, picture_pixel_point):
		pixel_x, pixel_y = picture_pixel_point
		reference_picture = self.pictures[0]
		x = (pixel_x / reference_picture.pixel_width - 0.5) * self.picture_width
		y = (0.5 - pixel_y / reference_picture.pixel_height) * self.picture_height
		return x, y, 0.0

	def _draw_team_member_annotations(self):
		visible_annotations = self._currently_visible_annotations()
		if not visible_annotations:
			return
		projector = ScreenSpaceProjector()
		pointed_screen_positions = [
			projector.screen_position_from_top_left(*self._picture_point_from_pixel_point(annotation.picture_pixel_point))
			for annotation in visible_annotations]
		projector.begin_pixel_overlay()
		for annotation, (screen_x, screen_y) in zip(visible_annotations, pointed_screen_positions):
			label_goes_to_the_right = annotation.picture_pixel_point[0] >= self.pictures[0].pixel_width / 2
			annotation.label.draw(screen_x, screen_y, label_goes_to_the_right,
			                      self.annotation_timeline_seconds - annotation.appear_second,
			                      annotation.opacity_at(self.annotation_timeline_seconds, self.annotation_fade_seconds))
		projector.end_pixel_overlay()

	def _apply_sway(self):
		sway_angle = 2 * math.pi * self.total_elapsed_seconds / self.sway_period_seconds
		sway_strength = 1.0 - self.eased_zoom_progress
		glRotatef(self.sway_yaw_amplitude_degrees * sway_strength * math.sin(sway_angle), 0.0, 1.0, 0.0)
		glRotatef(self.sway_pitch_amplitude_degrees * sway_strength * math.sin(sway_angle * 0.7), 1.0, 0.0, 0.0)

	def _apply_zoom_to_target(self):
		zoom_progress = self.eased_zoom_progress
		if zoom_progress <= 0.0:
			return
		zoom_scale = math.exp(math.log(self.zoom_target_scale) * zoom_progress)
		target_center_x, target_center_y = self.zoom_target_center
		glScalef(zoom_scale, zoom_scale, 1.0)
		glTranslatef(-target_center_x * zoom_progress, -target_center_y * zoom_progress, 0.0)

	def _apply_drive_in_offset_and_turn(self):
		remaining_drive_in = 1.0 - self.eased_drive_in_progress
		glTranslatef(self.drive_in_start_x * remaining_drive_in, 0.0, 0.0)
		glRotatef(self.drive_in_entry_yaw_degrees * remaining_drive_in, 0.0, 1.0, 0.0)

	def _draw_pictures(self):
		glEnable(GL_TEXTURE_2D)
		glEnable(GL_BLEND)
		glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
		glColor4f(1.0, 1.0, 1.0, 1.0)
		if self.active_transition is not None:
			self.active_transition.draw_pictures(self.picture_width, self.picture_height)
		else:
			self.pictures[self.shown_picture_index].draw_vertical_strip(0.0, 1.0, self.picture_width,
			                                                            self.picture_height)
		glDisable(GL_TEXTURE_2D)

	def destroy(self):
		for picture in self.pictures:
			picture.destroy()
		self.pictures = []
		for annotation in self.team_member_annotations:
			annotation.destroy()
		self.team_member_annotations = []
		self.closing_caption_sequence.destroy()
		self.flying_logo.destroy()
