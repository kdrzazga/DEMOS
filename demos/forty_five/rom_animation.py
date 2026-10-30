from lib.flying_logo import ease_out_cubic
from demos.forty_five.chip_animation import ChipAnimation, ChipPose
from demos.forty_five.chips.mos901xxx import MOS901xxx


class Rom901xxxAnimation(ChipAnimation):

	def __init__(self, label, aspect_ratio, field_of_view_degrees, photo_camera_distance, photo_width, photo_height,
	             **chip_animation_options):
		super().__init__(MOS901xxx(label), aspect_ratio, field_of_view_degrees, photo_camera_distance, photo_width,
		                 photo_height, **chip_animation_options)

	def appear_at(self, fraction_from_left, fraction_from_top, appear_seconds, height_in_photo_heights=0.4):
		self.grow_into_view_at(ChipPose(fraction_from_left, fraction_from_top, 0.0, height_in_photo_heights),
		                       appear_seconds, easing=ease_out_cubic)
