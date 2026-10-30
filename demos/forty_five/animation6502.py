from lib.flying_logo import ease_out_cubic
from demos.forty_five.chip_animation import ChipAnimation, ChipPose
from demos.forty_five.chips.mos65xx import MOS65xx


class Processor6502Animation(ChipAnimation):

	def __init__(self, aspect_ratio, field_of_view_degrees, photo_camera_distance, photo_width, photo_height,
	             **chip_animation_options):
		super().__init__(MOS65xx("6502"), aspect_ratio, field_of_view_degrees, photo_camera_distance, photo_width,
		                 photo_height, **chip_animation_options)

	def pose_in_left_margin_beside_photo(self, height_in_photo_heights=1.0):
		photo_width_fraction = self.photo_width / self.visible_width_on_photo_plane
		return ChipPose((1.0 - photo_width_fraction) / 4, 0.5, 0.0, height_in_photo_heights)

	def slide_in_from_left(self, slide_seconds):
		self.pose = self.pose_just_beyond_left_edge()
		self.glide_to(self.pose_in_left_margin_beside_photo(), slide_seconds, easing=ease_out_cubic)

	def move_behind_photo(self, move_seconds, depth_behind_photo=8.0):
		target_pose = ChipPose(0.5, 0.5, depth_behind_photo, self.pose.height_in_photo_heights)
		self.glide_to(target_pose, move_seconds)

	def zoom_out_to_top_left_corner(self, travel_seconds, height_in_photo_heights=0.4):
		self.glide_to(self.pose_in_top_left_corner(height_in_photo_heights, self.pose.depth_behind_photo),
		              travel_seconds)
