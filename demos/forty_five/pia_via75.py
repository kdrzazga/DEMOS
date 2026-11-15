import os

from demos.forty_five.chips.chip_name_flash import ChipNameFlash
from demos.forty_five.paths import MOS_HISTORY_DIRECTORY
from demos.forty_five.sound import load_sound

PIA_VIA_SOUND_PATH = os.path.join(MOS_HISTORY_DIRECTORY, "PIA-VIA.mp3")


class PiaViaIntroduction:

	def __init__(self, chip_gallery):
		self.chip_gallery = chip_gallery
		self.processor_arrives_with_picture_index = 1
		self.processor_arrives_at_transition_progress = 0.5
		self.processor_hides_with_picture_index = 2
		self.processor_hides_at_transition_progress = 0.5
		self.processor_slide_in_seconds = 2.5
		self.processor_hide_seconds = 1.2
		self.pia_via_slide_in_seconds = 2.5
		self.pia_via_join_seconds = 1.2
		self.pia_via_depth_behind_photo = 2.0
		self.sound = load_sound(PIA_VIA_SOUND_PATH)
		self.sound_seconds = None
		self.have_joined_processor = False
		self.name_flashes = (ChipNameFlash(chip_gallery.pia_6520, "PIA"), ChipNameFlash(chip_gallery.via_6522, "VIA"))
		for name_flash in self.name_flashes:
			name_flash.build()

	def restart(self):
		self.sound_seconds = None
		self.have_joined_processor = False
		for name_flash in self.name_flashes:
			name_flash.reset()

	def move_chips_with_mos_team_photos(self, mos_team):
		processor, pia, via = self.chip_gallery.processor_with_pia_and_via
		incoming_picture_index = mos_team.incoming_picture_index
		transition_progress = mos_team.active_transition_progress
		arrival_time_has_come = (incoming_picture_index == self.processor_arrives_with_picture_index
		                         and transition_progress >= self.processor_arrives_at_transition_progress)
		if arrival_time_has_come and not processor.visible:
			processor.slide_into_left_margin(self.processor_slide_in_seconds)
		hiding_time_has_come = (incoming_picture_index == self.processor_hides_with_picture_index
		                        and transition_progress >= self.processor_hides_at_transition_progress)
		if hiding_time_has_come and not pia.visible:
			processor.move_behind_photo(self.processor_hide_seconds)
			pia.slide_into_left_margin(self.pia_via_slide_in_seconds, self.pia_via_depth_behind_photo)
			via.slide_into_right_margin(self.pia_via_slide_in_seconds, self.pia_via_depth_behind_photo)
			self.sound.play()
			self.sound_seconds = 0.0

	def update(self, seconds):
		if self.sound_seconds is None or self.have_joined_processor:
			return
		self.sound_seconds += seconds
		if self.sound_seconds >= self.sound.get_length():
			self.chip_gallery.line_up_pia_and_via_next_to_processor(self.pia_via_join_seconds)
			self.have_joined_processor = True

	def flash_names(self, seconds):
		for name_flash in self.name_flashes:
			chip_animation = name_flash.chip_animation
			has_slid_in = chip_animation.visible and not chip_animation.is_gliding
			if has_slid_in and not name_flash.started and not self.have_joined_processor:
				name_flash.start()
			name_flash.update(seconds)
			name_flash.draw()

	def destroy_name_flashes(self):
		for name_flash in self.name_flashes:
			name_flash.destroy()
