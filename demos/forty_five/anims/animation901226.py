from demos.forty_five.anims.rom_animation import Rom901xxxAnimation


class BasicRom901226Animation(Rom901xxxAnimation):

	def __init__(self, aspect_ratio, field_of_view_degrees, photo_camera_distance, photo_width, photo_height,
	             **chip_animation_options):
		super().__init__("901226", aspect_ratio, field_of_view_degrees, photo_camera_distance, photo_width,
		                 photo_height, **chip_animation_options)

	def appear_between_jack_and_bill(self, appear_seconds, fraction_from_left=0.53, fraction_from_top=0.72,
	                                 height_in_photo_heights=0.4):
		self.appear_at(fraction_from_left, fraction_from_top, appear_seconds, height_in_photo_heights)
