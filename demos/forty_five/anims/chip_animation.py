import math

import numpy as np
from OpenGL.GL import *

from lib.flying_logo import ease_in_cubic, ease_out_cubic
from lib.laser_line import smooth_step
from demos.forty_five.rotation import rotation_x, rotation_y, rotation_z, transform_matrix


class ChipPose:

	def __init__(self, fraction_from_left, fraction_from_top, depth_behind_photo, height_in_photo_heights,
	             roll_degrees=0.0):
		self.fraction_from_left = fraction_from_left
		self.fraction_from_top = fraction_from_top
		self.depth_behind_photo = depth_behind_photo
		self.height_in_photo_heights = height_in_photo_heights
		self.roll_degrees = roll_degrees

	def blended_toward(self, target_pose, progress, roll_progress):
		def blend(start_value, target_value, blend_progress=progress):
			return start_value + (target_value - start_value) * blend_progress
		return ChipPose(blend(self.fraction_from_left, target_pose.fraction_from_left),
		                blend(self.fraction_from_top, target_pose.fraction_from_top),
		                blend(self.depth_behind_photo, target_pose.depth_behind_photo),
		                blend(self.height_in_photo_heights, target_pose.height_in_photo_heights),
		                blend(self.roll_degrees, target_pose.roll_degrees, roll_progress))

	def with_height(self, height_in_photo_heights):
		return ChipPose(self.fraction_from_left, self.fraction_from_top, self.depth_behind_photo,
		                height_in_photo_heights, self.roll_degrees)

	def copy(self):
		return self.with_height(self.height_in_photo_heights)


class ChipPoseGlide:

	def __init__(self, start_pose, target_pose, glide_seconds, easing, roll_easing):
		self.start_pose = start_pose
		self.target_pose = target_pose
		self.glide_seconds = glide_seconds
		self.easing = easing
		self.roll_easing = roll_easing
		self.elapsed_seconds = 0.0

	def update(self, seconds):
		self.elapsed_seconds += seconds

	@property
	def finished(self):
		return self.elapsed_seconds >= self.glide_seconds

	@property
	def current_pose(self):
		progress = min(1.0, self.elapsed_seconds / self.glide_seconds)
		return self.start_pose.blended_toward(self.target_pose, self.easing(progress), self.roll_easing(progress))


class ChipAnimation:

	def __init__(self, chip, aspect_ratio, field_of_view_degrees, photo_camera_distance, photo_width, photo_height,
	             sway_yaw_amplitude_degrees=12.0, sway_pitch_amplitude_degrees=4.0, sway_period_seconds=5.0,
	             light_direction=(-0.35, 0.5, 1.0, 0.0), screen_margin_fraction=0.03):
		self.aspect_ratio = aspect_ratio
		self.photo_camera_distance = photo_camera_distance
		self.photo_width = photo_width
		self.photo_height = photo_height
		self.sway_yaw_amplitude_degrees = sway_yaw_amplitude_degrees
		self.sway_pitch_amplitude_degrees = sway_pitch_amplitude_degrees
		self.sway_period_seconds = sway_period_seconds
		self.light_direction = light_direction
		self.screen_margin_fraction = screen_margin_fraction
		self.gap_to_left_neighbour_fraction = 0.08
		self.visible_height_on_photo_plane = 2 * photo_camera_distance * math.tan(math.radians(field_of_view_degrees) / 2)
		self.visible_width_on_photo_plane = self.visible_height_on_photo_plane * aspect_ratio
		self.chip = chip
		self.chip.build()
		self.chip_length = 2 * self.chip.body_half_length
		self.chip_width_with_legs = 2 * (self.chip.package.row_spacing_cm / 2 + self.chip.leg_thickness)
		self.eye_transform_override = None
		self.restart()

	def restart(self):
		self.visible = False
		self.pose = self.pose_just_beyond_left_edge()
		self.active_glide = None
		self.sway_elapsed_seconds = 0.0

	@property
	def is_behind_photo(self):
		return self.pose.depth_behind_photo > 0.0

	@property
	def is_gliding(self):
		return self.active_glide is not None and not self.active_glide.finished

	@property
	def resting_pose(self):
		return self.pose if self.active_glide is None else self.active_glide.target_pose

	def _apparent_scale(self, pose):
		return self.photo_camera_distance / (self.photo_camera_distance + pose.depth_behind_photo)

	def screen_size_fractions(self, pose):
		chip_world_length = pose.height_in_photo_heights * self.photo_height * self._apparent_scale(pose)
		chip_world_width = chip_world_length * self.chip_width_with_legs / self.chip_length
		roll_radians = math.radians(pose.roll_degrees)
		roll_cosine, roll_sine = abs(math.cos(roll_radians)), abs(math.sin(roll_radians))
		world_width = roll_cosine * chip_world_width + roll_sine * chip_world_length
		world_height = roll_sine * chip_world_width + roll_cosine * chip_world_length
		return world_width / self.visible_width_on_photo_plane, world_height / self.visible_height_on_photo_plane

	def bottom_center_screen_fractions(self):
		_, height_fraction = self.screen_size_fractions(self.pose)
		return self.pose.fraction_from_left, self.pose.fraction_from_top + height_fraction / 2

	def resting_bottom_fraction_from_top(self):
		_, height_fraction = self.screen_size_fractions(self.resting_pose)
		return self.resting_pose.fraction_from_top + height_fraction / 2

	def height_matching_scale_of(self, other_chip_animation, pose_of_other_chip):
		return pose_of_other_chip.height_in_photo_heights * self.chip_length / other_chip_animation.chip_length

	def pose_just_beyond_left_edge(self, height_in_photo_heights=1.0):
		resting_pose = ChipPose(0.0, 0.5, 0.0, height_in_photo_heights)
		width_fraction, _ = self.screen_size_fractions(resting_pose)
		resting_pose.fraction_from_left = -width_fraction
		return resting_pose

	def pose_just_beyond_right_edge(self, height_in_photo_heights=1.0):
		resting_pose = ChipPose(1.0, 0.5, 0.0, height_in_photo_heights)
		width_fraction, _ = self.screen_size_fractions(resting_pose)
		resting_pose.fraction_from_left = 1.0 + width_fraction
		return resting_pose

	def pose_in_left_margin_beside_photo(self, height_in_photo_heights=1.0):
		photo_width_fraction = self.photo_width / self.visible_width_on_photo_plane
		return ChipPose((1.0 - photo_width_fraction) / 4, 0.5, 0.0, height_in_photo_heights)

	def pose_in_right_margin_beside_photo(self, height_in_photo_heights=1.0):
		left_margin_pose = self.pose_in_left_margin_beside_photo(height_in_photo_heights)
		left_margin_pose.fraction_from_left = 1.0 - left_margin_pose.fraction_from_left
		return left_margin_pose

	def slide_in_from_right(self, fraction_from_left, slide_seconds, height_in_photo_heights=1.0):
		self.pose = self.pose_just_beyond_right_edge(height_in_photo_heights)
		self.glide_to(ChipPose(fraction_from_left, 0.5, 0.0, height_in_photo_heights), slide_seconds,
		              easing=ease_out_cubic)

	def slide_into_left_margin(self, slide_seconds, depth_behind_photo=0.0):
		self._slide_in(self.pose_just_beyond_left_edge(), self.pose_in_left_margin_beside_photo(), slide_seconds,
		               depth_behind_photo)

	def slide_into_right_margin(self, slide_seconds, depth_behind_photo=0.0):
		self._slide_in(self.pose_just_beyond_right_edge(), self.pose_in_right_margin_beside_photo(), slide_seconds,
		               depth_behind_photo)

	def _slide_in(self, start_pose, target_pose, slide_seconds, depth_behind_photo):
		start_pose.depth_behind_photo = depth_behind_photo
		target_pose.depth_behind_photo = depth_behind_photo
		self.pose = start_pose
		self.glide_to(target_pose, slide_seconds, easing=ease_out_cubic)

	def pose_just_beyond_top_edge(self):
		_, height_fraction = self.screen_size_fractions(self.pose)
		return ChipPose(self.pose.fraction_from_left, -height_fraction, self.pose.depth_behind_photo,
		                self.pose.height_in_photo_heights)

	def leave_through_top_edge(self, leave_seconds):
		self.glide_to(self.pose_just_beyond_top_edge(), leave_seconds, easing=ease_in_cubic)

	def drop_in_from_top_edge_to(self, place_pose, drop_seconds):
		self.pose = place_pose.copy()
		_, height_fraction = self.screen_size_fractions(self.pose)
		self.pose.fraction_from_top = -height_fraction
		self.glide_to(place_pose.copy(), drop_seconds, easing=ease_out_cubic)

	@property
	def has_left_through_top_edge(self):
		return self.active_glide is not None and self.active_glide.finished and self.pose.fraction_from_top < 0.0

	def pose_in_top_left_corner(self, height_in_photo_heights, depth_behind_photo):
		corner_pose = ChipPose(0.0, 0.0, depth_behind_photo, height_in_photo_heights)
		width_fraction, height_fraction = self.screen_size_fractions(corner_pose)
		vertical_margin = self.screen_margin_fraction * self.aspect_ratio
		corner_pose.fraction_from_left = self.screen_margin_fraction + width_fraction / 2
		corner_pose.fraction_from_top = vertical_margin + height_fraction / 2
		return corner_pose

	def pose_right_of_with_tops_aligned(self, neighbour_chip_animation, neighbour_pose, gap_fraction):
		resting_pose = ChipPose(0.0, 0.0, neighbour_pose.depth_behind_photo,
		                        self.height_matching_scale_of(neighbour_chip_animation, neighbour_pose))
		neighbour_width, neighbour_height = neighbour_chip_animation.screen_size_fractions(neighbour_pose)
		own_width, own_height = self.screen_size_fractions(resting_pose)
		resting_pose.fraction_from_left = neighbour_pose.fraction_from_left + neighbour_width / 2 + gap_fraction + own_width / 2
		neighbour_top = neighbour_pose.fraction_from_top - neighbour_height / 2
		resting_pose.fraction_from_top = neighbour_top + own_height / 2
		return resting_pose

	def glide_to(self, target_pose, glide_seconds, easing=smooth_step, roll_easing=None):
		self.visible = True
		self.active_glide = ChipPoseGlide(self.pose, target_pose, glide_seconds, easing, roll_easing or easing)

	def rise_next_to(self, neighbour_chip_animation, rise_seconds):
		self.glide_to(self.pose_right_of_with_tops_aligned(neighbour_chip_animation,
		                                                   neighbour_chip_animation.resting_pose,
		                                                   self.gap_to_left_neighbour_fraction),
		              rise_seconds)

	def grow_into_view_at(self, target_pose, grow_seconds, easing=smooth_step):
		self.pose = target_pose.with_height(0.0)
		self.glide_to(target_pose, grow_seconds, easing)

	def update(self, seconds):
		self.sway_elapsed_seconds += seconds
		if self.active_glide is None:
			return
		self.active_glide.update(seconds)
		self.pose = self.active_glide.current_pose

	def _world_position(self):
		distance_from_camera = self.photo_camera_distance + self.pose.depth_behind_photo
		depth_spread = distance_from_camera / self.photo_camera_distance
		world_x = (self.pose.fraction_from_left - 0.5) * self.visible_width_on_photo_plane * depth_spread
		world_y = (0.5 - self.pose.fraction_from_top) * self.visible_height_on_photo_plane * depth_spread
		return world_x, world_y, -distance_from_camera

	def eye_transform(self):
		if self.eye_transform_override is not None:
			return self.eye_transform_override
		sway_angle = 2 * math.pi * self.sway_elapsed_seconds / self.sway_period_seconds
		rotation = (rotation_z(self.pose.roll_degrees)
		            @ rotation_y(self.sway_yaw_amplitude_degrees * math.sin(sway_angle))
		            @ rotation_x(self.sway_pitch_amplitude_degrees * math.sin(sway_angle * 0.7))
		            @ rotation_x(90.0))
		chip_scale = self.pose.height_in_photo_heights * self.photo_height / self.chip_length
		return np.array(self._world_position()), rotation, chip_scale

	def draw(self):
		if not self.visible:
			return
		position, rotation, chip_scale = self.eye_transform()
		glPushAttrib(GL_ENABLE_BIT | GL_LIGHTING_BIT | GL_CURRENT_BIT | GL_DEPTH_BUFFER_BIT | GL_TEXTURE_BIT)
		glEnable(GL_DEPTH_TEST)
		glEnable(GL_LIGHTING)
		glEnable(GL_LIGHT0)
		glEnable(GL_NORMALIZE)
		glDisable(GL_BLEND)
		glMatrixMode(GL_MODELVIEW)
		glPushMatrix()
		glLoadIdentity()
		glLightfv(GL_LIGHT0, GL_POSITION, self.light_direction)
		glMultMatrixf(transform_matrix(position, rotation).T.copy())
		glScalef(chip_scale, chip_scale, chip_scale)
		self.chip.draw()
		glPopMatrix()
		glPopAttrib()

	def destroy(self):
		self.chip.destroy()
