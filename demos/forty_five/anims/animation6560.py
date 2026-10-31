from demos.forty_five.anims.chip_animation import ChipAnimation
from demos.forty_five.chips.mos65xx import MOS65xx


class VicChip6560Animation(ChipAnimation):

	def __init__(self, aspect_ratio, field_of_view_degrees, photo_camera_distance, photo_width, photo_height,
	             **chip_animation_options):
		super().__init__(MOS65xx("6560"), aspect_ratio, field_of_view_degrees, photo_camera_distance, photo_width,
		                 photo_height, **chip_animation_options)
