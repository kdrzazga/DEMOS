from demos.forty_five.anims.chip_animation import ChipAnimation
from demos.forty_five.chips.mos6581 import MOS6581


class SidChip6581Animation(ChipAnimation):

	def __init__(self, aspect_ratio, field_of_view_degrees, photo_camera_distance, photo_width, photo_height):
		super().__init__(MOS6581(), aspect_ratio, field_of_view_degrees, photo_camera_distance, photo_width,
		                 photo_height)
