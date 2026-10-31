from lib.flying_logo import ease_out_cubic
from demos.forty_five.anims.chip_animation import ChipAnimation, ChipPose
from demos.forty_five.chips.mos65xx import MOS65xx


class VicChip6560Animation(ChipAnimation):

	def __init__(self, aspect_ratio, field_of_view_degrees, photo_camera_distance, photo_width, photo_height,
	             **chip_animation_options):
		super().__init__(MOS65xx("6560"), aspect_ratio, field_of_view_degrees, photo_camera_distance, photo_width,
		                 photo_height, **chip_animation_options)

	def slide_in_from_right(self, fraction_from_left, slide_seconds, height_in_photo_heights=1.0):
		self.pose = self.pose_just_beyond_right_edge(height_in_photo_heights)
		self.glide_to(ChipPose(fraction_from_left, 0.5, 0.0, height_in_photo_heights), slide_seconds,
		              easing=ease_out_cubic)
