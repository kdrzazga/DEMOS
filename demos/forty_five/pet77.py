import os

import pygame
from OpenGL.GL import *

from lib.flying_logo import ease_in_cubic, ease_out_cubic
from lib.laser_line import PictureTexture, smooth_step
from lib.picture_surface import PictureSurface
from demos.forty_five.typed_label import TypedLabel

FORTY_FIVE_DIRECTORY = os.path.dirname(os.path.abspath(__file__))
PET_IMAGE_PATH = os.path.join(os.path.dirname(FORTY_FIVE_DIRECTORY), "common", "commodore", "pet.png")
PET_SOUND_PATH = os.path.join(FORTY_FIVE_DIRECTORY, "resources", "history", "c=", "77PET.mp3")
PET_CHIPS_HEADER = "Chips used in PET:"
PET_CHIP_NAMES = ("Processor 6502", "BASIC ROM", "Character ROM")


class ChipToPetLine:

	def __init__(self, screen_plane, chip_animation, pet, pet_point_in_picture_fractions, grow_seconds, line_width_px):
		self.screen_plane = screen_plane
		self.chip_animation = chip_animation
		self.pet = pet
		self.pet_point_in_picture_fractions = pet_point_in_picture_fractions
		self.grow_seconds = grow_seconds
		self.line_width_px = line_width_px
		self.opacity = 1.0
		self.elapsed_seconds = None

	@property
	def started(self):
		return self.elapsed_seconds is not None

	@property
	def finished(self):
		return self.started and self.elapsed_seconds >= self.grow_seconds

	def start(self):
		self.elapsed_seconds = 0.0
		self.opacity = 1.0

	def update(self, seconds):
		if self.started:
			self.elapsed_seconds += seconds

	def _end_points(self):
		chip_x, chip_y = self.screen_plane.world_point_from_screen_fractions(
			*self.chip_animation.bottom_center_screen_fractions())
		fraction_x, fraction_y = self.pet_point_in_picture_fractions
		pet_x, pet_y = self.pet.world_point_from_picture_pixel(fraction_x * self.pet.picture.pixel_width,
		                                                       fraction_y * self.pet.picture.pixel_height)
		return (chip_x, chip_y), (pet_x, pet_y)

	def draw(self):
		if not self.started:
			return
		progress = smooth_step(min(1.0, self.elapsed_seconds / self.grow_seconds))
		(end_x, end_y), (start_x, start_y) = self._end_points()
		depth = -self.screen_plane.camera_distance
		glLineWidth(self.line_width_px)
		glEnable(GL_BLEND)
		glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
		glColor4f(1.0, 1.0, 1.0, self.opacity)
		glBegin(GL_LINES)
		glVertex3f(start_x, start_y, depth)
		glVertex3f(start_x + (end_x - start_x) * progress, start_y + (end_y - start_y) * progress, depth)
		glEnd()
		glLineWidth(1.0)


class PetIntroduction:

	def __init__(self, screen_plane, wait_seconds=1.0, pet_height_in_screen_heights=0.5, pet_rest_fraction_from_left=0.28,
	             pet_enter_seconds=3.0, pet_swing_amplitude_degrees=12.0, peddle_lower_seconds=2.0,
	             rom_appear_seconds=0.4, rom_sway_seconds=2.0, rom_join_seconds=2.0, rom_fraction_from_top=0.72,
	             clear_stage_seconds=1.5, text_line_height=0.6, text_line_gap=0.3, text_frames_per_letter=4,
	             line_grow_seconds=0.5, line_width_px=2.0, final_hold_seconds=2.0, pet_drop_seconds=1.5,
	             pet_line_targets_in_picture_fractions=((0.35, 0.05), (0.5, 0.05), (0.65, 0.05))):
		self.screen_plane = screen_plane
		self.wait_seconds = wait_seconds
		self.pet_rest_fraction_from_left = pet_rest_fraction_from_left
		self.pet_enter_seconds = pet_enter_seconds
		self.peddle_lower_seconds = peddle_lower_seconds
		self.rom_appear_seconds = rom_appear_seconds
		self.rom_sway_seconds = rom_sway_seconds
		self.rom_join_seconds = rom_join_seconds
		self.rom_fraction_from_top = rom_fraction_from_top
		self.clear_stage_seconds = clear_stage_seconds
		self.text_line_height = text_line_height
		self.text_line_gap = text_line_gap
		self.line_grow_seconds = line_grow_seconds
		self.line_width_px = line_width_px
		self.final_hold_seconds = final_hold_seconds
		self.pet_drop_seconds = pet_drop_seconds
		self.pet_drop_start_y = None
		self.pet_line_targets_in_picture_fractions = pet_line_targets_in_picture_fractions
		self.pet_picture = PictureTexture.load(PET_IMAGE_PATH)
		self.pet = PictureSurface(self.pet_picture, screen_plane, pet_height_in_screen_heights,
		                          swing_amplitude_degrees=pet_swing_amplitude_degrees)
		self.pet_sound = self._load_sound(PET_SOUND_PATH)
		self.labels = tuple(TypedLabel(text, text_line_height, frames_per_letter=text_frames_per_letter)
		                    for text in (PET_CHIPS_HEADER,) + PET_CHIP_NAMES)
		for label in self.labels:
			label.build()
		self.chuck_peddle = None
		self.character_rom = None
		self.chip_lines = ()
		self.peddle_destroyed = False
		self.phase = "idle"
		self.phase_seconds = 0.0
		self.typing_index = 0

	@staticmethod
	def _load_sound(sound_path):
		if not pygame.mixer.get_init():
			pygame.mixer.init()
		return pygame.mixer.Sound(sound_path)

	def begin(self, chuck_peddle, processor, basic_rom, character_rom):
		self.chuck_peddle = chuck_peddle
		self.basic_rom = basic_rom
		self.character_rom = character_rom
		self.peddle_destroyed = False
		self.chip_lines = tuple(
			ChipToPetLine(self.screen_plane, chip, self.pet, target, self.line_grow_seconds, self.line_width_px)
			for chip, target in zip((processor, basic_rom, character_rom), self.pet_line_targets_in_picture_fractions))
		for label in self.labels:
			label.restart()
		self.typing_index = 0
		self.pet_drop_start_y = None
		self._enter("wait")

	def _enter(self, phase):
		self.phase = phase
		self.phase_seconds = 0.0

	@property
	def done(self):
		return self.phase == "done"

	@property
	def pet_visible(self):
		return self.phase not in ("idle", "wait")

	def update(self, seconds):
		self.phase_seconds += seconds
		self.pet.update(seconds)
		for chip_line in self.chip_lines:
			chip_line.update(seconds)
		if self.phase == "wait" and self.phase_seconds >= self.wait_seconds:
			self._start_pet_arrival()
		elif self.phase == "pet_arrives" and self.phase_seconds >= self.pet_sound.get_length():
			self._show_character_rom()
		elif self.phase == "rom_sways" and self.phase_seconds >= self.rom_appear_seconds + self.rom_sway_seconds:
			self.character_rom.rise_next_to(self.basic_rom, self.rom_join_seconds)
			self._enter("rom_joins")
		elif self.phase == "rom_joins" and not self.character_rom.is_gliding:
			self._clear_stage()
		elif self.phase == "clear_stage" and self.phase_seconds >= self.clear_stage_seconds:
			self._destroy_peddle()
			self._enter("typing")
		elif self.phase == "typing":
			self._advance_typing()
		elif self.phase == "hold" and self.phase_seconds >= self.final_hold_seconds:
			self._drop_pet()
		elif self.phase == "pet_drops":
			self._fade_chip_lines()
			if self.phase_seconds >= self.pet_drop_seconds:
				self._enter("done")

	def _drop_pet(self):
		self._enter("pet_drops")
		self.pet_drop_start_y = self.pet.world_center_point[1]
		self.pet.glide_center_to(self.pet.center_fractions_just_below_bottom_edge(), self.pet_drop_seconds,
		                         easing=ease_in_cubic)

	def _fade_chip_lines(self):
		for chip_line in self.chip_lines:
			chip_line.opacity = max(0.0, 1.0 - self.phase_seconds / self.pet_drop_seconds)

	def _pet_drop_offset(self):
		if self.pet_drop_start_y is None:
			return 0.0
		return self.pet.world_center_point[1] - self.pet_drop_start_y

	def _start_pet_arrival(self):
		self._enter("pet_arrives")
		self.pet_sound.play()
		peddle_fraction_from_left, _ = self.chuck_peddle.center_screen_fractions
		self.chuck_peddle.glide_center_to(
			self.chuck_peddle.center_fractions_with_bottom_edge_on_screen_bottom(peddle_fraction_from_left),
			self.peddle_lower_seconds)
		_, pet_fraction_from_top = self.pet.center_fractions_with_bottom_edge_on_screen_bottom(0.0)
		self.pet.place_center_at(self.pet.center_fractions_just_beyond_left_edge(pet_fraction_from_top))
		self.pet.glide_center_to((self.pet_rest_fraction_from_left, pet_fraction_from_top), self.pet_enter_seconds,
		                         easing=ease_out_cubic)

	def _show_character_rom(self):
		self._enter("rom_sways")
		pet_right_edge = self.pet.center_screen_fractions[0] + self.pet.width_in_screen_widths / 2
		peddle_left_edge = self.chuck_peddle.center_screen_fractions[0] - self.chuck_peddle.width_in_screen_widths / 2
		self.character_rom.appear_at((pet_right_edge + peddle_left_edge) / 2, self.rom_fraction_from_top,
		                             self.rom_appear_seconds)

	def _clear_stage(self):
		self._enter("clear_stage")
		_, pet_fraction_from_top = self.pet.center_screen_fractions
		self.pet.glide_center_to(self.pet.center_fractions_with_left_edge_on_screen_left(pet_fraction_from_top),
		                         self.clear_stage_seconds)
		self.chuck_peddle.glide_center_to(self.chuck_peddle.center_fractions_just_below_bottom_edge(),
		                                  self.clear_stage_seconds, easing=ease_in_cubic)

	def _destroy_peddle(self):
		self.chuck_peddle.destroy()
		self.chuck_peddle = None
		self.peddle_destroyed = True

	def _advance_typing(self):
		label = self.labels[self.typing_index]
		label.update()
		if not label.finished:
			return
		chip_line = self.chip_lines[self.typing_index - 1] if self.typing_index > 0 else None
		if chip_line is not None and not chip_line.started:
			chip_line.start()
		if chip_line is not None and not chip_line.finished:
			return
		if self.typing_index + 1 < len(self.labels):
			self.typing_index += 1
		else:
			self._enter("hold")

	def draw_pet(self):
		if self.pet_visible:
			self.pet.draw()

	def draw_overlay(self):
		glPushAttrib(GL_ENABLE_BIT | GL_CURRENT_BIT | GL_COLOR_BUFFER_BIT | GL_LINE_BIT)
		glDisable(GL_LIGHTING)
		glDisable(GL_DEPTH_TEST)
		glDisable(GL_TEXTURE_2D)
		glMatrixMode(GL_MODELVIEW)
		glPushMatrix()
		glLoadIdentity()
		for chip_line in self.chip_lines:
			chip_line.draw()
		self._draw_labels()
		glPopMatrix()
		glPopAttrib()

	def _draw_labels(self):
		line_step = self.text_line_height + self.text_line_gap
		top_centre_y = line_step * (len(self.labels) - 1) / 2 + self._pet_drop_offset()
		depth = -self.screen_plane.camera_distance
		for index, label in enumerate(self.labels):
			label.draw((0.0, top_centre_y - index * line_step, depth), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0))

	def destroy(self):
		self.pet_sound.stop()
		self.pet_picture.destroy()
		for label in self.labels:
			label.destroy()
		if self.chuck_peddle is not None:
			self._destroy_peddle()
