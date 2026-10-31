from demos.forty_five.anims.replacing_chip_animation import ReplacingChipAnimation
from demos.forty_five.chips.mos65xx import MOS65xx


class VicIIChip6567Animation(ReplacingChipAnimation):

	def __init__(self, aspect_ratio, field_of_view_degrees, photo_camera_distance, photo_width, photo_height):
		super().__init__(MOS65xx("6567"), aspect_ratio, field_of_view_degrees, photo_camera_distance, photo_width,
		                 photo_height)
