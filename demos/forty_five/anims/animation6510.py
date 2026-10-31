from lib.flying_logo import ease_out_cubic
from lib.laser_line import smooth_step
from demos.forty_five.anims.chip_animation import ChipAnimation, ChipPose
from demos.forty_five.chips.mos65xx import MOS65xx


class Processor6510Animation(ChipAnimation):

	def __init__(self, aspect_ratio, field_of_view_degrees, photo_camera_distance, photo_width, photo_height):
		super().__init__(MOS65xx("6510"), aspect_ratio, field_of_view_degrees, photo_camera_distance, photo_width,
		                 photo_height)
		self.horizontal_roll_degrees = 90.0
		self.turn_starts_at_drive_progress = 0.5

	def drive_to_screen_centre_turning_horizontal(self, drive_seconds, height_in_photo_heights):
		self.pose = self.pose_just_beyond_left_edge(height_in_photo_heights)
		screen_centre_pose = ChipPose(0.5, 0.5, 0.0, height_in_photo_heights, self.horizontal_roll_degrees)
		self.glide_to(screen_centre_pose, drive_seconds, easing=ease_out_cubic, roll_easing=self._turn_near_the_end)

	def _turn_near_the_end(self, drive_progress):
		turn_progress = (drive_progress - self.turn_starts_at_drive_progress) / (1.0 - self.turn_starts_at_drive_progress)
		return smooth_step(min(1.0, max(0.0, turn_progress)))

	def take_place_turning_vertical(self, place_pose, travel_seconds):
		vertical_place_pose = place_pose.copy()
		vertical_place_pose.roll_degrees = 0.0
		self.glide_to(vertical_place_pose, travel_seconds)
