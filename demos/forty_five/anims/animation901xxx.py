from demos.forty_five.anims.rom_animation import Rom901xxxAnimation


class KernalRom901xxxAnimation(Rom901xxxAnimation):

	def __init__(self, aspect_ratio, field_of_view_degrees, photo_camera_distance, photo_width, photo_height):
		super().__init__("901xxx", aspect_ratio, field_of_view_degrees, photo_camera_distance, photo_width,
		                 photo_height)
