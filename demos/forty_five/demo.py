"""Commodore 64 demo - pygame + OpenGL front-end.

Run from the DEMOS project root:

    python -m demos.c64.demo            # fullscreen
    python -m demos.c64.demo w          # windowed
    python main.py c64 w                # via the top-level launcher

Plays the iny.mp4 intro, then the Commodore 64 is smashed: the keys spelling
the caption fly off into the distance and come back as that caption, the rest
of the machine falls away. "PROUDLY PRESENTS" is typed under the caption,
held for a moment, and the camera flies forward through the caption. Behind
it the MOS Technology team sequence plays (MosTeam). Then Chuck Peddle's photo
rises from the bottom of the screen and drifts to the top-right corner while
Jabba swings in from the left (MosAcquisition), Jack Tramiel buys BASIC from
Bill Gates (BasicLicense), and the PET arrives with the Character ROM; the three
chips used in the PET are listed and linked to it (PetIntroduction), the PET
drops away and 77VIC.mp3 plays over Al Charpentier's photos changing under the
laser line (MosTeam with AlCharpentierParams) - and the demo ends.
Chuck Peddle belongs to the demo, not to a stage, so he can travel between stages.
Music: amorEspacial_AmigaManson.mp3 plays once from the end of the typing;
65xx.mp3 plays on top of it from the moment the MOS logo flies in.
ESC / window-close quits at any time.
"""

import os
import sys

import pygame

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from OpenGL.GL import *

from lib import Globals
from lib.caption_sequence import CaptionSequence
from lib.laser_line import smooth_step
from lib.picture_surface import ScreenPlane
from lib.pygame_demo import PygameDemo
from lib.typer import FONT_PATH
from demos.forty_five.acquisition76 import MosAcquisition
from demos.forty_five.basic77 import BasicLicense
from demos.forty_five.c64c.commodore64 import Commodore64
from demos.forty_five.c64c.crash_animation import CrashAnimationText
from demos.forty_five.chuck_peddle import ChuckPeddleSurface
from demos.forty_five.intro import IntroCaptionVideo
from demos.forty_five.mos_team75 import MosTeamFactory
from demos.forty_five.animation6502 import Processor6502Animation
from demos.forty_five.animation901226 import BasicRom901226Animation
from demos.forty_five.animation901225 import CharacterRom901225Animation
from demos.forty_five.animation6560 import VicChip6560Animation
from demos.forty_five.pet77 import PetIntroduction
from demos.forty_five.scene import setup_scene
from demos.forty_five.typed_label import TypedLabel


class C64Demo(PygameDemo):

	def __init__(self, windowed=False, triggered=False, caption="KOMODA & AMIGA PLUS", presents="PROUDLY PRESENTS"):
		self.caption = caption
		self.presents = presents
		self.fov = 40.0
		self.background = (0.0, 0.0, 0.0)
		self.resources = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources")
		self.intro_video = "iny.mp4"
		self.intro_audio = "iny.wav"
		self.presents_height = 1.1
		self.presents_gap = 1.0
		self.presents_hold_seconds = 1.0
		self.fly_through_seconds = 2.2
		self.fly_through_overshoot = 4.0
		self.beat_path = os.path.join(self.resources, "amorEspacial_AmigaManson.mp3")
		self.mos_team_sound_path = os.path.join(self.resources, "history", "mos", "65xx.mp3")
		self.mos_acquisition_sound_path = os.path.join(self.resources, "history", "mos", "76acquisition.mp3")
		self.vic_sound_path = os.path.join(self.resources, "history", "c=", "77VIC.mp3")
		self.chuck_peddle_drift_seconds = 6.0
		self.music_volume = 1.0
		self.music_volume_while_speaking = 0.5
		self.processor_arrives_with_picture_index = 3
		self.processor_hides_with_picture_index = 4
		self.processor_hides_at_transition_progress = 0.5
		self.processor_slide_in_seconds = 2.5
		self.processor_hide_seconds = 1.2
		self.basic_rom_appear_seconds = 0.4
		self.vic_chip_slide_in_seconds = 2.5
		self.al_charpentier_exit_seconds = 1.5
		self.year_flash_count = 3
		self.year_flash_seconds = 0.5
		self.pause_seconds_between_year_flashes = 0.25
		self.year_flash_color = (230, 40, 40)
		self.year_flash_font_pixel_size = 110
		self.year_flash_left_margin_pixels = 170.0
		self.year_flash_design_screen_height = 800.0
		self.year_flash_gap_below_chips_pixels = 30.0
		super().__init__(1280, 800, "Commodore 64", fps=60, windowed=windowed, triggered=triggered)

	def setup(self):
		aspect = self.width / self.height
		setup_scene(aspect, self.fov, self.background)

		self.computer = Commodore64()
		self.computer.build()
		self.animation = CrashAnimationText(self.computer, aspect, self.fov, self.caption, fps=self.fps,
		                                    caption_hold_seconds=0.0)
		self.presents_label = TypedLabel(self.presents, self.presents_height)
		self.presents_label.build()

		self.mos_team = MosTeamFactory.create_default_mos_team(aspect, self.fov)
		self.mos_team_sound = self._load_sound(self.mos_team_sound_path)
		self.processor_6502 = Processor6502Animation(aspect, self.fov, self.mos_team.camera_distance,
		                                             self.mos_team.picture_width, self.mos_team.params.picture_height)
		self.basic_rom_901226 = BasicRom901226Animation(aspect, self.fov, self.mos_team.camera_distance,
		                                                self.mos_team.picture_width,
		                                                self.mos_team.params.picture_height)
		self.character_rom_901225 = CharacterRom901225Animation(aspect, self.fov, self.mos_team.camera_distance,
		                                                        self.mos_team.picture_width,
		                                                        self.mos_team.params.picture_height)
		self.vic_chip_6560 = VicChip6560Animation(aspect, self.fov, self.mos_team.camera_distance,
		                                          self.mos_team.picture_width, self.mos_team.params.picture_height)

		self.screen_plane = ScreenPlane(aspect, self.fov)
		self.chuck_peddle = ChuckPeddleSurface(self.screen_plane)
		self.mos_acquisition = MosAcquisition(self.screen_plane)
		self.mos_acquisition_sound = self._load_sound(self.mos_acquisition_sound_path)
		self.mos_acquisition_sound_seconds = None
		self.basic_license = BasicLicense(self.screen_plane)
		self.pet_introduction = PetIntroduction(self.screen_plane)
		self.al_charpentier_show = MosTeamFactory.create_al_charpentier_show(aspect, self.fov)
		self.vic_sound = self._load_sound(self.vic_sound_path)

		self.intro = IntroCaptionVideo(os.path.join(self.resources, self.intro_video),
		                        os.path.join(self.resources, self.intro_audio), aspect)
		self.phase = "intro"
		self.phase_seconds = 0.0

	def _enter(self, phase):
		self.phase = phase
		self.phase_seconds = 0.0

	def step(self):
		if self.phase == "intro":
			self.intro.render()
			if self.intro.done:
				self.intro.destroy()
				self.intro = None
				self._enter("caption")
			return

		seconds = 1.0 / self.fps
		self.phase_seconds += seconds
		glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
		if self.phase == "mos_team":
			self._mos_team_step(seconds)
		elif self.phase == "mos_acquisition":
			self._mos_acquisition_step(seconds)
		elif self.phase == "basic_license":
			self._basic_license_step(seconds)
		elif self.phase == "pet_introduction":
			self._pet_introduction_step(seconds)
		elif self.phase == "al_charpentier":
			self._al_charpentier_step(seconds)
		elif self.phase == "year_1980":
			self._year_1980_step(seconds)
		else:
			self._caption_step()
		self._lower_music_while_speaking()

	def _spoken_sounds(self):
		spoken_sounds = [self.mos_team_sound, self.mos_acquisition_sound, self.pet_introduction.pet_sound,
		                 self.vic_sound]
		if self.basic_license is not None:
			spoken_sounds.append(self.basic_license.basic_license_sound)
		return spoken_sounds

	def _lower_music_while_speaking(self):
		speaking = any(sound.get_num_channels() > 0 for sound in self._spoken_sounds())
		music_volume = self.music_volume * (self.music_volume_while_speaking if speaking else 1.0)
		if pygame.mixer.get_init() and pygame.mixer.music.get_volume() != music_volume:
			pygame.mixer.music.set_volume(music_volume)

	def _caption_step(self):
		"""The smash and the caption, "PROUDLY PRESENTS", the hold and the fly-through."""
		self.animation.update()
		if self.phase == "caption" and self.animation.done:
			self._enter("presents")
		elif self.phase == "presents":
			self.presents_label.update()
			if self.presents_label.finished:
				self._enter("presents_hold")
				self._play_music(self.beat_path)
		elif self.phase == "presents_hold" and self.phase_seconds >= self.presents_hold_seconds:
			self._enter("fly_through")
		elif self.phase == "fly_through":
			centre, right, up, caption_distance = self.animation.caption_frame()
			progress = min(1.0, self.phase_seconds / self.fly_through_seconds)
			self.animation.camera_advance = (caption_distance + self.fly_through_overshoot) * smooth_step(progress)
			if progress >= 1.0:
				self._enter("mos_team")
				self.mos_team.restart()
				self.processor_6502.restart()
				self.basic_rom_901226.restart()
				self.character_rom_901225.restart()
				self.vic_chip_6560.restart()
				self.mos_team_sound.play()

		self.animation.draw()
		if self.phase != "caption":
			centre, right, up, _ = self.animation.caption_frame()
			below = self.computer.key_pitch / 2 + self.presents_gap + self.presents_height / 2
			self.presents_label.draw(tuple(c - below * u for c, u in zip(centre, up)), right, up)

	def _mos_team_step(self, seconds):
		self.mos_team.update(seconds)
		self._move_processor_with_mos_team_photos()
		self.processor_6502.update(seconds)
		if self.processor_6502.is_behind_photo:
			self.processor_6502.draw()
			self.mos_team.draw()
		else:
			self.mos_team.draw()
			self.processor_6502.draw()
		if self.mos_team.done:
			self._enter("mos_acquisition")
			self.chuck_peddle.place_at_bottom_middle()
			self.chuck_peddle.drift_to_top_right_corner(self.chuck_peddle_drift_seconds)
			self.processor_6502.zoom_out_to_top_left_corner(self.chuck_peddle_drift_seconds)
			self.mos_acquisition.restart()
			self.mos_acquisition_sound_seconds = None

	def _move_processor_with_mos_team_photos(self):
		incoming_picture_index = self.mos_team.incoming_picture_index
		if incoming_picture_index == self.processor_arrives_with_picture_index and not self.processor_6502.visible:
			self.processor_6502.slide_in_from_left(self.processor_slide_in_seconds)
		hiding_time_has_come = (incoming_picture_index == self.processor_hides_with_picture_index
		                        and self.mos_team.active_transition_progress >= self.processor_hides_at_transition_progress)
		if hiding_time_has_come and not self.processor_6502.is_behind_photo:
			self.processor_6502.move_behind_photo(self.processor_hide_seconds)

	def _update_travellers(self, seconds):
		self.processor_6502.update(seconds)
		self.basic_rom_901226.update(seconds)
		self.character_rom_901225.update(seconds)
		self.vic_chip_6560.update(seconds)
		if self.chuck_peddle is not None:
			self.chuck_peddle.update(seconds)

	def _update_and_draw_travellers(self, seconds):
		self._update_travellers(seconds)
		self.processor_6502.draw()
		self.chuck_peddle.draw()

	def _mos_acquisition_step(self, seconds):
		self.mos_acquisition.update(seconds)
		if self.mos_acquisition.morph_finished and self.mos_acquisition_sound_seconds is None:
			self.mos_acquisition_sound_seconds = 0.0
			self.mos_acquisition_sound.play()
		elif self.mos_acquisition_sound_seconds is not None:
			self.mos_acquisition_sound_seconds += seconds
			sound_has_stopped = self.mos_acquisition_sound_seconds >= self.mos_acquisition_sound.get_length()
			if sound_has_stopped and not self.mos_acquisition.big_jack_revealed:
				self.mos_acquisition.reveal_big_jack()
		self._update_and_draw_travellers(seconds)
		self.mos_acquisition.draw()
		if self.mos_acquisition.done and not self.chuck_peddle.is_gliding:
			self._enter("basic_license")
			self.basic_license.begin(talking_jack=self.mos_acquisition.big_jack,
			                         fading_logo=self.mos_acquisition.mos_logo)

	def _basic_license_step(self, seconds):
		self.mos_acquisition.update(seconds)
		self.basic_license.update(seconds)
		self._move_basic_rom_with_basic_license()
		self._update_and_draw_travellers(seconds)
		self.mos_acquisition.draw()
		self.basic_license.draw()
		self.basic_rom_901226.draw()
		if self.basic_license.done:
			self._destroy_everything_but_chuck_peddle()
			self._enter("pet_introduction")
			self.pet_introduction.begin(self.chuck_peddle, self.processor_6502, self.basic_rom_901226,
			                            self.character_rom_901225)

	def _move_basic_rom_with_basic_license(self):
		if self.basic_license.talk_finished and not self.basic_rom_901226.visible:
			self.basic_rom_901226.appear_between_jack_and_bill(self.basic_rom_appear_seconds)
		rom_is_still_between_jack_and_bill = self.basic_rom_901226.resting_pose.depth_behind_photo == 0.0
		if self.basic_license.exit_has_started and rom_is_still_between_jack_and_bill:
			self.basic_rom_901226.rise_next_to(self.processor_6502, self.basic_license.exit_seconds)

	def _destroy_everything_but_chuck_peddle(self):
		for finished_stage in (self.mos_team, self.mos_acquisition, self.basic_license):
			finished_stage.destroy()
		self.mos_team = None
		self.mos_acquisition = None
		self.basic_license = None

	def _pet_introduction_step(self, seconds):
		self._update_travellers(seconds)
		self.pet_introduction.update(seconds)
		if self.pet_introduction.peddle_destroyed:
			self.chuck_peddle = None
		self.pet_introduction.draw_pet()
		if self.chuck_peddle is not None:
			self.chuck_peddle.draw()
		self._draw_chips()
		self.pet_introduction.draw_overlay()
		if self.pet_introduction.done:
			self.pet_introduction.destroy()
			self._enter("al_charpentier")
			self.al_charpentier_show.restart()
			self.vic_sound.play()

	def _draw_chips(self):
		for chip_animation in (self.processor_6502, self.basic_rom_901226, self.character_rom_901225,
		                       self.vic_chip_6560):
			chip_animation.draw()

	def _al_charpentier_step(self, seconds):
		self._update_travellers(seconds)
		self.al_charpentier_show.update(seconds)
		self._move_vic_chip_with_al_charpentier()
		self.al_charpentier_show.draw()
		self._draw_chips()
		vic_sound_has_stopped = self.vic_sound.get_num_channels() == 0
		vic_chip_has_joined = self.al_charpentier_show.has_left and not self.vic_chip_6560.is_gliding
		if vic_chip_has_joined and vic_sound_has_stopped:
			self.al_charpentier_show.destroy()
			self._start_year_1980_flashes()

	def _chip_row_bottom_fraction(self):
		return max(chip_animation.bottom_center_screen_fractions()[1]
		           for chip_animation in (self.processor_6502, self.basic_rom_901226, self.character_rom_901225,
		                                  self.vic_chip_6560))

	def _start_year_1980_flashes(self):
		top_margin_pixels = (self._chip_row_bottom_fraction() * self.year_flash_design_screen_height
		                     + self.year_flash_gap_below_chips_pixels)
		self.year_1980_flashes = CaptionSequence(
			("1980",) * self.year_flash_count, seconds_per_caption=self.year_flash_seconds,
			pause_seconds_between_captions=self.pause_seconds_between_year_flashes, text_color=self.year_flash_color,
			screen_scale=glGetIntegerv(GL_VIEWPORT)[3] / self.year_flash_design_screen_height,
			font_pixel_size=self.year_flash_font_pixel_size, margin_from_top_left_pixels=(self.year_flash_left_margin_pixels, top_margin_pixels),
			font_path=FONT_PATH)
		self.year_1980_flashes.start()
		self._enter("year_1980")

	def _year_1980_step(self, seconds):
		self._update_travellers(seconds)
		self.year_1980_flashes.update(seconds)
		self._draw_chips()
		self.year_1980_flashes.draw()
		if self.year_1980_flashes.finished:
			self.year_1980_flashes.destroy()
			self._finish()

	def _move_vic_chip_with_al_charpentier(self):
		show = self.al_charpentier_show
		if show.last_transition_has_started and not self.vic_chip_6560.visible:
			right_margin_middle = 1.0 - (1.0 - show.picture_screen_width_fraction) / 4
			self.vic_chip_6560.slide_in_from_right(right_margin_middle, self.vic_chip_slide_in_seconds)
		if show.done and not show.is_leaving:
			show.leave_through_bottom(self.al_charpentier_exit_seconds)
			self.vic_chip_6560.rise_next_to(self.character_rom_901225, self.al_charpentier_exit_seconds)

	@staticmethod
	def _load_sound(path):
		if not pygame.mixer.get_init():
			pygame.mixer.init()
		return pygame.mixer.Sound(path)

	@staticmethod
	def _play_music(path, loops=0):
		if not pygame.mixer.get_init():
			pygame.mixer.init()
		pygame.mixer.music.load(path)
		pygame.mixer.music.play(loops)

	def _finish(self):
		self.running = False
		print(Globals.get_duration())
		print("BYE !")


def c64_demo(windowed=False, triggered=False):
	C64Demo(windowed=windowed, triggered=triggered).run()


if __name__ == "__main__":
	args = [arg.lower() for arg in sys.argv[1:]]
	c64_demo(windowed=any(arg in ("w", "window", "windowed") for arg in args),
	         triggered=any(arg in ("t", "trigger", "triggered") for arg in args))
