from demos.forty_five.chips.chip_name_flash import ChipNameFlash
from demos.forty_five.overlay import screen_overlay
from demos.forty_five.sound import load_sound


class ChipSwap:

	def __init__(self, screen_plane, sound_path, predecessor_name):
		self.screen_plane = screen_plane
		self.predecessor_name = predecessor_name
		self.predecessor_name_flash = None
		self.swap_sound = load_sound(sound_path)
		self.newcomer = None
		self.predecessor = None
		self.sound_seconds = 0.0
		self.phase = "idle"

	@property
	def done(self):
		return self.phase == "done"

	@property
	def _seconds_of_sound_left(self):
		return self.swap_sound.get_length() - self.sound_seconds

	def begin(self, newcomer, predecessor):
		self.newcomer = newcomer
		self.predecessor = predecessor
		self.predecessor_name_flash = ChipNameFlash.before_gallery_removal(predecessor, self.predecessor_name)
		self.predecessor_name_flash.build()
		self.sound_seconds = 0.0
		self.swap_sound.play()
		self._begin_choreography()

	def update(self, seconds):
		self.sound_seconds += seconds
		self.predecessor_name_flash.update(seconds)
		self._advance_choreography()

	def _begin_choreography(self):
		raise NotImplementedError

	def _advance_choreography(self):
		raise NotImplementedError

	def _caption_is_visible(self):
		return True

	def _draw_caption(self):
		raise NotImplementedError

	def _destroy_caption(self):
		raise NotImplementedError

	def draw_overlay(self):
		if not self._caption_is_visible():
			return
		with screen_overlay():
			self._draw_caption()
		self.predecessor_name_flash.draw()

	def destroy(self):
		self.swap_sound.stop()
		self._destroy_caption()
		if self.predecessor_name_flash:
			self.predecessor_name_flash.destroy()
