from demos.forty_five.chips.chip_listing import ChipListing
from demos.forty_five.phased_scene import PhasedScene
from demos.forty_five.sound import load_sound
from lib.flying_logo import ease_in_cubic, ease_out_cubic
from lib.laser_line import PictureTexture
from lib.picture_surface import PictureSurface


class ComputerWithChipListing(PhasedScene):

	def __init__(self, screen_plane, image_path, sound_path, height_in_screen_heights, chips_header, chip_names,
	             line_targets_in_picture_fractions):
		super().__init__()
		self.screen_plane = screen_plane
		self.wait_seconds = 1.0
		self.computer_enter_seconds = 3.0
		self.computer_swing_amplitude_degrees = 12.0
		self.listing_hold_seconds = 4.0
		self.computer_drop_seconds = 1.5
		self.chip_listing_margin_in_screen_heights = 0.04
		self.computer_drop_start_y = None
		self.computer_picture = PictureTexture.load(image_path)
		self.computer = PictureSurface(self.computer_picture, screen_plane, height_in_screen_heights,
		                               swing_amplitude_degrees=self.computer_swing_amplitude_degrees)
		self.computer_sound = load_sound(sound_path)
		self.chip_listing = ChipListing(screen_plane, chips_header, chip_names, self.computer,
		                                line_targets_in_picture_fractions)
		self.chip_listing.place_in_bottom_right_corner(self.chip_listing_margin_in_screen_heights
		                                               * screen_plane.visible_height)

	@property
	def done(self):
		return self.phase == "done"

	@property
	def computer_visible(self):
		return self.phase not in ("idle", "wait")

	@property
	def _fraction_from_top_standing_on_screen_bottom(self):
		return self.computer.center_fractions_with_bottom_edge_on_screen_bottom(0.0)[1]

	def _send_computer_in_from_left(self, rest_center_fractions):
		_, fraction_from_top = rest_center_fractions
		self.computer.place_center_at(self.computer.center_fractions_just_beyond_left_edge(fraction_from_top))
		self.computer.glide_center_to(rest_center_fractions, self.computer_enter_seconds, easing=ease_out_cubic)

	def update(self, seconds):
		self.phase_seconds += seconds
		self.computer.update(seconds)
		if self.phase in ("typing", "hold", "computer_drops"):
			self.chip_listing.update(seconds)
		if self.phase == "wait" and self.phase_seconds >= self.wait_seconds:
			self._enter("computer_arrives")
			self.computer_sound.play()
			self._start_computer_arrival()
		elif self.phase == "computer_arrives" and self.phase_seconds >= self.computer_sound.get_length():
			self._continue_after_computer_sound()
		elif self.phase == "typing" and self.chip_listing.finished:
			self._enter("hold")
		elif self.phase == "hold" and self.phase_seconds >= self.listing_hold_seconds:
			self._drop_computer_with_listing()
		elif self.phase == "computer_drops":
			self._move_listing_with_dropping_computer()
		else:
			self._advance_own_phases()

	def _start_computer_arrival(self):
		raise NotImplementedError

	def _continue_after_computer_sound(self):
		raise NotImplementedError

	def _advance_own_phases(self):
		return

	def _drop_computer_with_listing(self):
		self._enter("computer_drops")
		center_x, self.computer_drop_start_y = self.computer.world_center_point
		screen_bottom_y = -self.screen_plane.visible_height / 2
		computer_drop_distance = self.computer_drop_start_y + self.computer.picture_height / 2 - screen_bottom_y
		listing_drop_distance = self.chip_listing.top_y - screen_bottom_y
		drop_distance = max(computer_drop_distance, listing_drop_distance)
		self.computer.glide_center_to(
			self.screen_plane.screen_fractions_from_world_point(center_x, self.computer_drop_start_y - drop_distance),
			self.computer_drop_seconds, easing=ease_in_cubic)

	def _move_listing_with_dropping_computer(self):
		self.chip_listing.fade_lines(max(0.0, 1.0 - self.phase_seconds / self.computer_drop_seconds))
		self.chip_listing.vertical_offset = self.computer.world_center_point[1] - self.computer_drop_start_y
		if self.phase_seconds >= self.computer_drop_seconds:
			self._enter("done")

	def draw(self):
		if self.computer_visible:
			self.computer.draw()

	def draw_overlay(self):
		self.chip_listing.draw()

	def destroy(self):
		self.computer_sound.stop()
		self.computer_picture.destroy()
		self.chip_listing.destroy()
