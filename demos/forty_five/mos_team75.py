import math
import os

from OpenGL.GL import *

from lib.laser_line import LaserLine, LaserSweepPath, PictureTexture, PictureTransition, smooth_step
from lib.caption_sequence import CaptionSequence
from lib.flying_logo import FlyingLogo, ease_in_cubic
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


class MosTeamParams:

	def __init__(self, aspect_ratio, field_of_view_degrees):
		self.aspect_ratio = aspect_ratio
		self.field_of_view_degrees = field_of_view_degrees
		self.picture_directory = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources", "history", "mos")
		self.picture_file_names = ("MOS.png", "MOS2.png", "MOS3.png", "MOS4.png", "MOS5.png")
		self.logo_file_name = LOGO_FILE_NAME
		self.logo_flight_seconds = LOGO_FLIGHT_SECONDS
		self.logo_caption_lines = LOGO_CAPTION_LINES
		self.transition_styles = ("laser_sweep", "laser_sweep", "laser_sweep", "color_fade")
		self.color_fade_seconds = 2.0
		self.hold_seconds_before_color_fade = 0.2
		self.picture_height = 10.0
		self.screen_fill_fraction = 0.8
		self.picture_shift_down_in_picture_heights = 0.0
		self.picture_centre_fraction_from_left = 0.5
		self.drive_in_seconds = 2.0
		self.drive_in_entry_yaw_degrees = -35.0
		self.drive_in_offscreen_margin_in_picture_widths = 0.15
		self.opening_hold_seconds = 1.0
		self.hold_seconds_between_transitions = 1.5
		self.closing_hold_seconds = 1.5
		self.laser_signed_moves_in_picture_widths = (0.40, -0.25, 0.45, -0.30, 0.30, -0.05, 0.40, -0.10, 0.15)
		self.laser_sweep_speed_in_picture_widths_per_second = 0.7
		self.sway_yaw_amplitude_degrees = 14.0
		self.sway_pitch_amplitude_degrees = 5.0
		self.sway_period_seconds = 9.0
		self.team_member_annotation_settings = (("Terry Holdt", (480, 400), 0.0, 2.0),
		                                        ("Wilbur Mathys", (85, 245), 1.0, 3.0),
		                                        ("Sydney-Anne Holt", (715, 300), 2.0, 4.0),
		                                        ("William Mensch", (210, 300), 3.0, 5.0),
		                                        ("Michael Jaynes", (630, 310), 4.0, 6.0),
		                                        ("Rodney Orgill", (280, 280), 5.0, 7.0),
		                                        ("Harry Bawcom", (550, 245), 6.0, 8.0),
		                                        ("Ray Hirt", (390, 210), 7.0, 9.0),
		                                        ("CHUCK PEDDLE", (470, 240), 8.0, 10.0))
		self.annotations_start_with_transition_number = 2
		self.most_annotations_visible_at_once = 2
		self.annotation_fade_seconds = 0.25
		self.annotation_design_screen_height = 800.0
		self.closing_captions = ("Photo transformation is not AI", "It is just GIMP :)")
		self.seconds_per_closing_caption = 1.25
		self.pause_seconds_between_closing_captions = 0.15
		self.closing_caption_color = (230, 40, 40)
		self.zoom_target_pixel_rectangle = ((445, 222), (500, 280))
		self.zoom_seconds = 1.25
		self.zoom_target_screen_fill_fraction = 0.85


class MosTeam:

	def __init__(self, params: MosTeamParams):
		self.params = params
		self.pictures = [PictureTexture.load(os.path.join(params.picture_directory, file_name))
		                 for file_name in params.picture_file_names]
		self.picture_width = params.picture_height * self.pictures[0].aspect_ratio
		self.camera_distance = self._camera_distance_that_fits_picture_on_screen()
		self.drive_in_start_x = self._drive_in_start_x_just_beyond_right_screen_edge()
		self.zoom_target_center, self.zoom_target_scale = (
			self._zoom_target_center_and_scale() if params.zoom_target_pixel_rectangle is not None else (None, None))
		self.laser_line = LaserLine(surface_top_y=params.picture_height / 2, surface_bottom_y=-params.picture_height / 2)
		self.team_member_annotations = self._build_team_member_annotations(params.team_member_annotation_settings)
		self.closing_caption_sequence = CaptionSequence(
			params.closing_captions, seconds_per_caption=params.seconds_per_closing_caption,
			pause_seconds_between_captions=params.pause_seconds_between_closing_captions,
			text_color=params.closing_caption_color, screen_scale=self._screen_scale())
		self.flying_logo = None
		if params.logo_file_name is not None:
			self.flying_logo = FlyingLogo(os.path.join(params.picture_directory, params.logo_file_name),
			                              params.aspect_ratio, params.field_of_view_degrees, self.camera_distance,
			                              flight_seconds=params.logo_flight_seconds,
			                              settled_caption_lines=params.logo_caption_lines)
		self.restart()

	@property
	def logo_is_flying(self):
		return self.flying_logo is not None and not self.flying_logo.finished

	def _screen_scale(self):
		return glGetIntegerv(GL_VIEWPORT)[3] / self.params.annotation_design_screen_height

	def _build_team_member_annotations(self, annotation_settings):
		screen_scale = self._screen_scale()
		return [TeamMemberAnnotation(name, picture_pixel_point, appear_second, disappear_second,
		                             PointedNameLabel(name, screen_scale=screen_scale))
		        for name, picture_pixel_point, appear_second, disappear_second in annotation_settings]

	def _camera_distance_that_fits_picture_on_screen(self):
		vertical_half_angle_tangent = math.tan(math.radians(self.params.field_of_view_degrees) / 2)
		horizontal_half_angle_tangent = vertical_half_angle_tangent * self.params.aspect_ratio
		distance_fitting_height = self.params.picture_height / 2 / self.params.screen_fill_fraction / vertical_half_angle_tangent
		distance_fitting_width = self.picture_width / 2 / self.params.screen_fill_fraction / horizontal_half_angle_tangent
		return max(distance_fitting_height, distance_fitting_width)

	def _zoom_target_center_and_scale(self):
		(left_pixel, top_pixel), (right_pixel, bottom_pixel) = self.params.zoom_target_pixel_rectangle
		left_x, top_y, _ = self._picture_point_from_pixel_point((left_pixel, top_pixel))
		right_x, bottom_y, _ = self._picture_point_from_pixel_point((right_pixel, bottom_pixel))
		target_center = ((left_x + right_x) / 2, (top_y + bottom_y) / 2)
		visible_height = 2 * self.camera_distance * math.tan(math.radians(self.params.field_of_view_degrees) / 2)
		visible_width = visible_height * self.params.aspect_ratio
		scale_fitting_height = visible_height * self.params.zoom_target_screen_fill_fraction / abs(top_y - bottom_y)
		scale_fitting_width = visible_width * self.params.zoom_target_screen_fill_fraction / abs(right_x - left_x)
		return target_center, min(scale_fitting_height, scale_fitting_width)

	def _drive_in_start_x_just_beyond_right_screen_edge(self):
		vertical_half_angle_tangent = math.tan(math.radians(self.params.field_of_view_degrees) / 2)
		visible_half_width = self.camera_distance * vertical_half_angle_tangent * self.params.aspect_ratio
		offscreen_margin = self.picture_width * self.params.drive_in_offscreen_margin_in_picture_widths
		return visible_half_width + self.picture_width / 2 + offscreen_margin - self._picture_centre_x()

	def _visible_width(self):
		vertical_half_angle_tangent = math.tan(math.radians(self.params.field_of_view_degrees) / 2)
		return 2 * self.camera_distance * vertical_half_angle_tangent * self.params.aspect_ratio

	def _picture_centre_x(self):
		return (self.params.picture_centre_fraction_from_left - 0.5) * self._visible_width()

	@property
	def picture_right_edge_screen_fraction(self):
		return self.params.picture_centre_fraction_from_left + self.picture_screen_width_fraction / 2

	def restart(self):
		if self.flying_logo is not None:
			self.flying_logo.restart()
		self.total_elapsed_seconds = 0.0
		self.drive_in_elapsed_seconds = 0.0
		self.shown_picture_index = 0
		self.active_transition = None
		self.remaining_hold_seconds = self.params.opening_hold_seconds
		self.finished = False
		self.started_transition_count = 0
		self.annotation_timeline_seconds = None
		self.zoom_elapsed_seconds = None
		self.exit_seconds = None
		self.exit_elapsed_seconds = None
		self.laser_line.reset()
		self.closing_caption_sequence.reset()

	@property
	def done(self):
		return self.finished

	@property
	def incoming_picture_index(self):
		if self.active_transition is None:
			return None
		return self.shown_picture_index + 1

	@property
	def active_transition_progress(self):
		if self.active_transition is None:
			return 0.0
		return self.active_transition.progress

	@property
	def last_transition_has_started(self):
		return self.incoming_picture_index == len(self.pictures) - 1

	@property
	def picture_screen_width_fraction(self):
		visible_height = 2 * self.camera_distance * math.tan(math.radians(self.params.field_of_view_degrees) / 2)
		return self.picture_width / (visible_height * self.params.aspect_ratio)

	def picture_right_edge_point_on_plane_at(self, plane_distance, fraction_from_bottom):
		plane_scale = plane_distance / self.camera_distance
		picture_bottom_y = (-self.params.picture_shift_down_in_picture_heights * self.params.picture_height
		                    - self._exit_drop() - self.params.picture_height / 2)
		edge_y = picture_bottom_y + fraction_from_bottom * self.params.picture_height
		return (self._picture_centre_x() + self.picture_width / 2) * plane_scale, edge_y * plane_scale

	def leave_through_bottom(self, exit_seconds):
		self.exit_seconds = exit_seconds
		self.exit_elapsed_seconds = 0.0

	@property
	def is_leaving(self):
		return self.exit_elapsed_seconds is not None

	@property
	def has_left(self):
		return self.is_leaving and self.exit_elapsed_seconds >= self.exit_seconds

	def _exit_drop(self):
		if not self.is_leaving:
			return 0.0
		visible_half_height = self.camera_distance * math.tan(math.radians(self.params.field_of_view_degrees) / 2)
		swaying_picture_half_height = self.params.picture_height / 2 * 1.2
		return (visible_half_height + swaying_picture_half_height) * ease_in_cubic(
			min(1.0, self.exit_elapsed_seconds / self.exit_seconds))

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
		return smooth_step(min(1.0, self.zoom_elapsed_seconds / self.params.zoom_seconds))

	@property
	def is_driving_in(self):
		return self.drive_in_elapsed_seconds < self.params.drive_in_seconds

	@property
	def eased_drive_in_progress(self):
		progress = min(1.0, self.drive_in_elapsed_seconds / self.params.drive_in_seconds)
		return 1.0 - (1.0 - progress) ** 3

	def update(self, seconds):
		if self.logo_is_flying:
			self.flying_logo.update(seconds)
			return
		self.total_elapsed_seconds += seconds
		if self.is_leaving:
			self.exit_elapsed_seconds += seconds
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
			return self.params.closing_hold_seconds
		if self.params.transition_styles[self.shown_picture_index] == "color_fade":
			return self.params.hold_seconds_before_color_fade
		return self.params.hold_seconds_between_transitions

	def _advance_hold(self, seconds):
		self.remaining_hold_seconds -= seconds
		if self.remaining_hold_seconds > 0.0:
			return
		if self.is_showing_last_picture:
			if self.all_annotations_have_disappeared and self.closing_caption_sequence.finished:
				if self.zoom_target_center is None:
					self.finished = True
				else:
					self.zoom_elapsed_seconds = 0.0
		else:
			self._start_transition_to_next_picture()

	def _advance_zoom(self, seconds):
		self.zoom_elapsed_seconds += seconds
		if self.zoom_elapsed_seconds >= self.params.zoom_seconds:
			self.finished = True

	def _start_transition_to_next_picture(self):
		outgoing_picture = self.pictures[self.shown_picture_index]
		incoming_picture = self.pictures[self.shown_picture_index + 1]
		if self.params.transition_styles[self.shown_picture_index] == "color_fade":
			self.active_transition = PictureCrossfade(outgoing_picture, incoming_picture, self.params.color_fade_seconds)
		else:
			self._start_laser_sweep_transition(outgoing_picture, incoming_picture)
		self.started_transition_count += 1
		if self.started_transition_count == self.params.annotations_start_with_transition_number:
			self.annotation_timeline_seconds = 0.0

	def _start_laser_sweep_transition(self, outgoing_picture, incoming_picture):
		laser_sweep_path = LaserSweepPath(self.params.laser_signed_moves_in_picture_widths,
		                                  self.params.laser_sweep_speed_in_picture_widths_per_second)
		self.active_transition = PictureTransition(outgoing_picture, incoming_picture, laser_sweep_path)
		self._move_laser_line_to_transition_position()
		self.laser_line.switch_on()

	def _move_laser_line_to_transition_position(self):
		laser_x = (self.active_transition.laser_position_fraction - 0.5) * self.picture_width
		self.laser_line.move_to(laser_x, self.active_transition.laser_movement_direction)

	def draw(self):
		if (self.finished and not self.is_leaving) or self.has_left:
			return
		if self.logo_is_flying:
			self.flying_logo.draw()
			return
		glPushAttrib(GL_ENABLE_BIT | GL_CURRENT_BIT | GL_COLOR_BUFFER_BIT)
		glDisable(GL_LIGHTING)
		glDisable(GL_DEPTH_TEST)
		glMatrixMode(GL_MODELVIEW)
		glPushMatrix()
		glLoadIdentity()
		picture_shift_down = self.params.picture_shift_down_in_picture_heights * self.params.picture_height
		glTranslatef(self._picture_centre_x(), -self._exit_drop() - picture_shift_down, -self.camera_distance)
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
		return visible_annotations[-self.params.most_annotations_visible_at_once:]

	def _picture_point_from_pixel_point(self, picture_pixel_point):
		pixel_x, pixel_y = picture_pixel_point
		reference_picture = self.pictures[0]
		x = (pixel_x / reference_picture.pixel_width - 0.5) * self.picture_width
		y = (0.5 - pixel_y / reference_picture.pixel_height) * self.params.picture_height
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
			                      annotation.opacity_at(self.annotation_timeline_seconds, self.params.annotation_fade_seconds))
		projector.end_pixel_overlay()

	def _apply_sway(self):
		sway_angle = 2 * math.pi * self.total_elapsed_seconds / self.params.sway_period_seconds
		sway_strength = 1.0 - self.eased_zoom_progress
		glRotatef(self.params.sway_yaw_amplitude_degrees * sway_strength * math.sin(sway_angle), 0.0, 1.0, 0.0)
		glRotatef(self.params.sway_pitch_amplitude_degrees * sway_strength * math.sin(sway_angle * 0.7), 1.0, 0.0, 0.0)

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
		glRotatef(self.params.drive_in_entry_yaw_degrees * remaining_drive_in, 0.0, 1.0, 0.0)

	def _draw_pictures(self):
		glEnable(GL_TEXTURE_2D)
		glEnable(GL_BLEND)
		glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
		glColor4f(1.0, 1.0, 1.0, 1.0)
		if self.active_transition is not None:
			self.active_transition.draw_pictures(self.picture_width, self.params.picture_height)
		else:
			self.pictures[self.shown_picture_index].draw_vertical_strip(0.0, 1.0, self.picture_width,
			                                                            self.params.picture_height)
		glDisable(GL_TEXTURE_2D)

	def destroy(self):
		for picture in self.pictures:
			picture.destroy()
		self.pictures = []
		for annotation in self.team_member_annotations:
			annotation.destroy()
		self.team_member_annotations = []
		self.closing_caption_sequence.destroy()
		if self.flying_logo is not None:
			self.flying_logo.destroy()


class MosTeamFactory:

	@staticmethod
	def create_default_mos_team(aspect_ratio, field_of_view_degrees):
		return MosTeam(MosTeamParams(aspect_ratio, field_of_view_degrees))

	@staticmethod
	def create_al_charpentier_show(aspect_ratio, field_of_view_degrees):
		return MosTeam(AlCharpentierParams(aspect_ratio, field_of_view_degrees))

	@staticmethod
	def create_robert_yannes_show(aspect_ratio, field_of_view_degrees):
		return MosTeam(RobertYannesParams(aspect_ratio, field_of_view_degrees))


class AlCharpentierParams(MosTeamParams):

	def __init__(self, aspect_ratio, field_of_view_degrees):
		super().__init__(aspect_ratio, field_of_view_degrees)
		self.picture_directory = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources", "history", "c=")
		self.picture_file_names = ("al-charpentier1.png", "al-charpentier2.png", "al-charpentier3.png")
		self.transition_styles = ("laser_sweep", "laser_sweep")
		self.logo_file_name = None
		self.team_member_annotation_settings = ()
		self.closing_captions = ()
		self.closing_hold_seconds = 1.0
		self.zoom_target_pixel_rectangle = None
		self.screen_fill_fraction = 0.72
		self.picture_shift_down_in_picture_heights = 0.06


class RobertYannesParams(AlCharpentierParams):

	def __init__(self, aspect_ratio, field_of_view_degrees):
		super().__init__(aspect_ratio, field_of_view_degrees)
		self.picture_file_names = ("RobertYannes.png", "RobertYannes2.png")
		self.transition_styles = ("laser_sweep",)
		self.screen_fill_fraction = 0.25
		self.picture_centre_fraction_from_left = 1.0 / 3.0
		self.picture_shift_down_in_picture_heights = 0.1
