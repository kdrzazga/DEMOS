from OpenGL.GL import *

import demos.forty_five.c64c.keys as k
from demos.forty_five.c64breadbox.primitives import Box


class Keyboard:

	def __init__(self):
		self.key_pitch = 1.95
		self.cap_height = 1.15
		self.keyboard_left = -19.45
		self.function_column = 17.1
		self.space_column = 2.6
		self.plate_margin = 0.6
		self.plate_thickness = 0.15
		self.plate_rgb = (34, 32, 30)
		self.cap_rgb = (58, 46, 34)
		self.legend_rgb = (255, 255, 255)
		self.keyboard_rows = k.c64_keyboard_rows()
		self.function_keys = k.c64_function_keys()
		self.space_bar = k.KeySpace()
		self.main_keys = tuple(key for row in self.keyboard_rows for key in row) + (self.space_bar,)
		self.keys = self.main_keys + self.function_keys
		for key in self.main_keys:
			key.cap_color = self.cap_rgb
			key.ink = self.legend_rgb
			key.shows_graphic_squares = False
		self.legend_replacements = ((k.KeyControl, "CTRL"),)
		for key in self.main_keys:
			for key_class, legend in self.legend_replacements:
				if isinstance(key, key_class):
					key.legend = legend
		self.centred_legend_font_px = 60
		self.centred_legend_key_classes = (k.KeyLeftShift, k.KeyRightShift, k.KeyControl, k.KeyReturn, k.KeyRestore)
		for key in self.main_keys:
			if isinstance(key, self.centred_legend_key_classes):
				key.legend_top_left = False
				key.legend_font_px = self.centred_legend_font_px
		self.number_key_classes = (k.Key1, k.Key2, k.Key3, k.Key4, k.Key5, k.Key6, k.Key7, k.Key8, k.Key9, k.Key0)
		self.number_font_px = 60
		self.number_symbol_font_px = 48
		self.number_symbol_centre_y = 0.27
		self.number_below_symbol_centre_y = 0.7
		for key in self.main_keys:
			if isinstance(key, self.number_key_classes):
				key.subtitle = ""
				key.legend_font_px = self.number_font_px
				key.shifted_font_px = self.number_symbol_font_px
				key.shifted_centre_y = self.number_symbol_centre_y
				key.legend_below_shifted_centre_y = self.number_below_symbol_centre_y
		self.function_key_captions = ("F1", "F3", "F5", "F7")
		for key, caption in zip(self.function_keys, self.function_key_captions):
			key.centred_caption = caption
		self._place_keys()
		self._display_list = None

	def _place_keys(self):
		for row_index, row in enumerate(self.keyboard_rows):
			column = 0.0
			for key in row:
				key.row, key.column = row_index, column
				column += key.width
		for row_index, key in enumerate(self.function_keys):
			key.row, key.column = row_index, self.function_column
		self.space_bar.row, self.space_bar.column = len(self.keyboard_rows), self.space_column
		self.key_positions = tuple((key, self._key_centre(key)) for key in self.keys)

	def _key_centre(self, key):
		return (self.keyboard_left + (key.column + key.width / 2) * self.key_pitch, 0.0,
		        (key.row + 0.5) * self.key_pitch)

	@property
	def main_width(self):
		return sum(key.width for key in self.keyboard_rows[0])

	def key_areas(self):
		pitch, left = self.key_pitch, self.keyboard_left
		row_count = len(self.keyboard_rows)
		function_width = self.function_keys[0].width
		return (
			(left, left + self.main_width * pitch, 0.0, row_count * pitch),
			(left + self.space_column * pitch, left + (self.space_column + self.space_bar.width) * pitch,
			 row_count * pitch, (row_count + 1) * pitch),
			(left + self.function_column * pitch, left + (self.function_column + function_width) * pitch,
			 0.0, len(self.function_keys) * pitch),
		)

	def _plate_box(self):
		areas = self.key_areas()
		margin = self.plate_margin
		return Box((min(area[0] for area in areas) - margin, -self.plate_thickness, min(area[2] for area in areas) - margin),
		           (max(area[1] for area in areas) + margin, 0.0, max(area[3] for area in areas) + margin))

	def build(self):
		for key in self.keys:
			key.build(self.key_pitch, self.cap_height)
		self._display_list = glGenLists(1)
		glNewList(self._display_list, GL_COMPILE)
		self._plate_box().draw(self.plate_rgb)
		glEndList()

	def press(self, pygame_key, is_down):
		for key in self.keys:
			if key.handles(pygame_key):
				key.on_pc_key(is_down)

	def update(self):
		for key in self.keys:
			key.update()

	def draw(self):
		glCallList(self._display_list)
		for key, (x, y, z) in self.key_positions:
			glPushMatrix()
			glTranslatef(x, y, z)
			key.draw()
			glPopMatrix()

	def destroy(self):
		for key in self.keys:
			key.destroy()
		if self._display_list:
			glDeleteLists(self._display_list, 1)
			self._display_list = None
