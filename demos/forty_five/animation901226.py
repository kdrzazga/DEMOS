from lib.flying_logo import ease_out_cubic
from demos.forty_five.chip_animation import ChipAnimation, ChipPose
from demos.forty_five.chips.mos901xxx import MOS901xxx


class BasicRom901226Animation(ChipAnimation):

	def __init__(self, aspect_ratio, field_of_view_degrees, photo_camera_distance, photo_width, photo_height,
	             **chip_animation_options):
		super().__init__(MOS901xxx("901226"), aspect_ratio, field_of_view_degrees, photo_camera_distance, photo_width,
		                 photo_height, **chip_animation_options)

	def appear_between_jack_and_bill(self, appear_seconds, fraction_from_left=0.53, fraction_from_top=0.72,
	                                 height_in_photo_heights=0.4):
		self.grow_into_view_at(ChipPose(fraction_from_left, fraction_from_top, 0.0, height_in_photo_heights),
		                       appear_seconds, easing=ease_out_cubic)

	def rise_next_to(self, neighbour_chip_animation, rise_seconds, gap_fraction=0.02):
		self.glide_to(self.pose_right_of_with_tops_aligned(neighbour_chip_animation,
		                                                   neighbour_chip_animation.resting_pose, gap_fraction),
		              rise_seconds)
