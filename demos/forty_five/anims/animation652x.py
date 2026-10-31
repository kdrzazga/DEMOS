from demos.forty_five.anims.chip_animation import ChipAnimation
from demos.forty_five.chips.mos652x import MOS652x


class PeripheralChip652xAnimation(ChipAnimation):

	def __init__(self, label, aspect_ratio, field_of_view_degrees, photo_camera_distance, photo_width, photo_height,
	             **chip_animation_options):
		super().__init__(MOS652x(label), aspect_ratio, field_of_view_degrees, photo_camera_distance, photo_width,
		                 photo_height, **chip_animation_options)
