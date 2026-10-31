from demos.forty_five.anims.rom_animation import Rom901xxxAnimation


class CharacterRom901225Animation(Rom901xxxAnimation):

	def __init__(self, aspect_ratio, field_of_view_degrees, photo_camera_distance, photo_width, photo_height,
	             **chip_animation_options):
		super().__init__("901225", aspect_ratio, field_of_view_degrees, photo_camera_distance, photo_width,
		                 photo_height, **chip_animation_options)
