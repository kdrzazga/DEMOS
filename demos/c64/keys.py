"""Commodore 64 key caps - one class per physical key.

Every key shares the same cap geometry and legend painting (the ``Key`` base
class); the subclasses only say what is printed on the cap, how wide it is and
which PC keys press it in the viewer.

Cap frame: x to the right, y up (away from the keyboard plate), z toward the
front of the machine. The origin is the centre of the cap's footprint on the
plate. Lengths are in centimetres.
"""

import pygame
from OpenGL.GL import *

try:
	from geometry import color, quad, text_texture, textured_quad
except ModuleNotFoundError:
	from demos.c64.geometry import color, quad, text_texture, textured_quad

KEYCAP_BEIGE = (226, 216, 188)
FUNCTION_KEY_TAN = (164, 146, 116)
LEGEND_INK = (58, 46, 34)


class Key:

	def __init__(self, legend, shifted="", subtitle="", width=1.0, pygame_keys=(),
	             cap_color=KEYCAP_BEIGE, ink=LEGEND_INK, legend_top_left=False,
	             petscii_graphics=False):
		self.legend = legend
		self.shifted = shifted
		self.subtitle = subtitle
		self.width = width
		self.pygame_keys = pygame_keys
		self.cap_color = cap_color
		self.ink = ink
		self.legend_top_left = legend_top_left
		self.petscii_graphics = petscii_graphics
		self.legend_inset_px = 12
		self.legend_line_px = 34

		self.letter_font_px = 60
		self.letter_centre_y = 0.32
		self.graphic_scale = 0.68
		self.graphic_cap_height = 0.72
		self.graphic_centres = ((0.32, 0.74), (0.68, 0.74))
		self.graphic_line_px = 3

		self.footprint_gap = 0.14
		self.side_taper = 0.22
		self.front_taper = 0.38
		self.back_taper = 0.14
		self.texture_px_per_unit = 128

		self.press_depth = 0.35
		self.press_rate = 0.6
		self.release_rate = 0.3

		self.column = 0.0
		self.row = 0

		self.pressed = False
		self.travel = 0.0
		self._display_list = None
		self._texture = None

	def handles(self, pygame_key):
		return pygame_key in self.pygame_keys

	def on_pc_key(self, is_down):
		"""A mapped PC key went down or up; an ordinary key is held while it is."""
		self.pressed = is_down

	def build(self, pitch, cap_height):
		"""Create the legend texture and compile the cap. Needs a GL context."""
		if self.legend or self.shifted:
			self._texture = text_texture(int(self.texture_px_per_unit * self.width), self.texture_px_per_unit,
			                             self.cap_color, self._legend_lines(), self._graphic_squares())
		self._display_list = glGenLists(1)
		glNewList(self._display_list, GL_COMPILE)
		self._draw_cap(pitch, cap_height)
		glEndList()

	def _has_graphics(self):
		return self.petscii_graphics or (len(self.legend) == 1 and self.legend.isalpha())

	def _graphic_squares(self):
		if not self._has_graphics():
			return ()
		side_px = round(self.letter_font_px * self.graphic_cap_height * self.graphic_scale)
		return tuple((side_px, self.graphic_line_px, self.ink, centre) for centre in self.graphic_centres)

	def _legend_lines(self):
		if self._has_graphics():
			return ((self.legend, self.letter_font_px, self.ink, (0.5, self.letter_centre_y)),)
		if self.legend_top_left:
			inset_x = self.legend_inset_px / (self.texture_px_per_unit * self.width)
			inset_y = self.legend_inset_px / self.texture_px_per_unit
			line_height = self.legend_line_px / self.texture_px_per_unit
			return tuple((row, 30, self.ink, (inset_x, inset_y + index * line_height), "topleft")
			             for index, row in enumerate(self.legend.split("\n")))
		lines = []
		legend_rows = self.legend.split("\n")
		if self.shifted:
			lines.append((self.shifted, 40, self.ink, (0.5, 0.24)))
		if len(legend_rows) > 1:
			lines.append((legend_rows[0], 30, self.ink, (0.5, 0.36)))
			lines.append((legend_rows[1], 30, self.ink, (0.5, 0.66)))
		elif self.legend:
			font_px = 60 if len(self.legend) <= 2 else 30
			if self.shifted:
				font_px = min(font_px, 46)
			centre_y = 0.6 if self.shifted else (0.42 if self.subtitle else 0.5)
			lines.append((self.legend, font_px, self.ink, (0.5, centre_y)))
		if self.subtitle:
			lines.append((self.subtitle, 22, self.ink, (0.5, 0.86)))
		return lines

	def _draw_cap(self, pitch, cap_height):
		half_base_w = (self.width * pitch - self.footprint_gap) / 2
		half_base_d = (pitch - self.footprint_gap) / 2
		half_top_w = half_base_w - self.side_taper
		top_front = half_base_d - self.front_taper
		top_back = -half_base_d + self.back_taper

		base_front_left = (-half_base_w, 0.0, half_base_d)
		base_front_right = (half_base_w, 0.0, half_base_d)
		base_back_right = (half_base_w, 0.0, -half_base_d)
		base_back_left = (-half_base_w, 0.0, -half_base_d)
		top_front_left = (-half_top_w, cap_height, top_front)
		top_front_right = (half_top_w, cap_height, top_front)
		top_back_right = (half_top_w, cap_height, top_back)
		top_back_left = (-half_top_w, cap_height, top_back)

		color(self.cap_color, 0.9)
		glBegin(GL_QUADS)
		quad(base_front_left, base_front_right, top_front_right, top_front_left)
		quad(base_front_right, base_back_right, top_back_right, top_front_right)
		quad(base_back_right, base_back_left, top_back_left, top_back_right)
		quad(base_back_left, base_front_left, top_front_left, top_back_left)
		glEnd()

		if self._texture:
			glColor3f(1.0, 1.0, 1.0)
			textured_quad(self._texture, top_front_left, top_front_right, top_back_right, top_back_left)
		else:
			color(self.cap_color)
			glBegin(GL_QUADS)
			quad(top_front_left, top_front_right, top_back_right, top_back_left)
			glEnd()

	def update(self):
		target = self.press_depth if self.pressed else 0.0
		rate = self.press_rate if self.pressed else self.release_rate
		self.travel += (target - self.travel) * rate
		if abs(self.travel - target) < 0.001:
			self.travel = target

	def draw(self):
		glPushMatrix()
		glTranslatef(0.0, -self.travel, 0.0)
		glCallList(self._display_list)
		glPopMatrix()

	def destroy(self):
		if self._display_list:
			glDeleteLists(self._display_list, 1)
		if self._texture:
			glDeleteTextures([self._texture])


class FunctionKey(Key):
	"""The darker, 1.5-unit-wide keys in the separate column on the right."""

	def __init__(self, legend, subtitle, pygame_keys):
		super().__init__(legend, subtitle=subtitle, width=1.5, pygame_keys=pygame_keys,
		                 cap_color=FUNCTION_KEY_TAN)

	def _legend_lines(self):
		return ((self.legend, 46, self.ink, (0.27, 0.3)),
		        (self.subtitle, 46, self.ink, (0.73, 0.7)))


class KeyArrowLeft(Key):
	def __init__(self):
		super().__init__("←", pygame_keys=(pygame.K_BACKQUOTE,))


class Key1(Key):
	def __init__(self):
		super().__init__("1", shifted="!", subtitle="BLK", pygame_keys=(pygame.K_1,))


class Key2(Key):
	def __init__(self):
		super().__init__("2", shifted="\"", subtitle="WHT", pygame_keys=(pygame.K_2,))


class Key3(Key):
	def __init__(self):
		super().__init__("3", shifted="#", subtitle="RED", pygame_keys=(pygame.K_3,))


class Key4(Key):
	def __init__(self):
		super().__init__("4", shifted="$", subtitle="CYN", pygame_keys=(pygame.K_4,))


class Key5(Key):
	def __init__(self):
		super().__init__("5", shifted="%", subtitle="PUR", pygame_keys=(pygame.K_5,))


class Key6(Key):
	def __init__(self):
		super().__init__("6", shifted="&", subtitle="GRN", pygame_keys=(pygame.K_6,))


class Key7(Key):
	def __init__(self):
		super().__init__("7", shifted="'", subtitle="BLU", pygame_keys=(pygame.K_7,))


class Key8(Key):
	def __init__(self):
		super().__init__("8", shifted="(", subtitle="YEL", pygame_keys=(pygame.K_8,))


class Key9(Key):
	def __init__(self):
		super().__init__("9", shifted=")", subtitle="RVS ON", pygame_keys=(pygame.K_9,))


class Key0(Key):
	def __init__(self):
		super().__init__("0", subtitle="RVS OFF", pygame_keys=(pygame.K_0,))


class KeyPlus(Key):
	def __init__(self):
		super().__init__("+", petscii_graphics=True, pygame_keys=(pygame.K_MINUS,))


class KeyMinus(Key):
	def __init__(self):
		super().__init__("-", petscii_graphics=True, pygame_keys=(pygame.K_EQUALS,))


class KeyPound(Key):
	def __init__(self):
		super().__init__("£", petscii_graphics=True, pygame_keys=(pygame.K_INSERT,))


class KeyClrHome(Key):
	def __init__(self):
		super().__init__("CLR\nHOME", legend_top_left=True, pygame_keys=(pygame.K_HOME,))


class KeyInstDel(Key):
	def __init__(self):
		super().__init__("INST\nDEL", legend_top_left=True, pygame_keys=(pygame.K_BACKSPACE,))


class KeyControl(Key):
	def __init__(self):
		super().__init__("CONTROL", width=1.5, legend_top_left=True, pygame_keys=(pygame.K_TAB,))


class KeyQ(Key):
	def __init__(self):
		super().__init__("Q", pygame_keys=(pygame.K_q,))


class KeyW(Key):
	def __init__(self):
		super().__init__("W", pygame_keys=(pygame.K_w,))


class KeyE(Key):
	def __init__(self):
		super().__init__("E", pygame_keys=(pygame.K_e,))


class KeyR(Key):
	def __init__(self):
		super().__init__("R", pygame_keys=(pygame.K_r,))


class KeyT(Key):
	def __init__(self):
		super().__init__("T", pygame_keys=(pygame.K_t,))


class KeyY(Key):
	def __init__(self):
		super().__init__("Y", pygame_keys=(pygame.K_y,))


class KeyU(Key):
	def __init__(self):
		super().__init__("U", pygame_keys=(pygame.K_u,))


class KeyI(Key):
	def __init__(self):
		super().__init__("I", pygame_keys=(pygame.K_i,))


class KeyO(Key):
	def __init__(self):
		super().__init__("O", pygame_keys=(pygame.K_o,))


class KeyP(Key):
	def __init__(self):
		super().__init__("P", pygame_keys=(pygame.K_p,))


class KeyAt(Key):
	def __init__(self):
		super().__init__("@", pygame_keys=(pygame.K_LEFTBRACKET,))


class KeyAsterisk(Key):
	def __init__(self):
		super().__init__("*", pygame_keys=(pygame.K_RIGHTBRACKET,))


class KeyArrowUp(Key):
	def __init__(self):
		super().__init__("↑", shifted="π", pygame_keys=(pygame.K_DELETE,))


class KeyRestore(Key):
	def __init__(self):
		super().__init__("RESTORE", width=1.5, legend_top_left=True, pygame_keys=(pygame.K_PAGEUP,))


class KeyRunStop(Key):
	def __init__(self):
		super().__init__("RUN\nSTOP", pygame_keys=(pygame.K_LALT,))


class KeyShiftLock(Key):
	def __init__(self):
		super().__init__("SHIFT\nLOCK", pygame_keys=(pygame.K_CAPSLOCK,))

	def on_pc_key(self, is_down):
		if is_down:
			self.pressed = not self.pressed


class KeyA(Key):
	def __init__(self):
		super().__init__("A", pygame_keys=(pygame.K_a,))


class KeyS(Key):
	def __init__(self):
		super().__init__("S", pygame_keys=(pygame.K_s,))


class KeyD(Key):
	def __init__(self):
		super().__init__("D", pygame_keys=(pygame.K_d,))


class KeyF(Key):
	def __init__(self):
		super().__init__("F", pygame_keys=(pygame.K_f,))


class KeyG(Key):
	def __init__(self):
		super().__init__("G", pygame_keys=(pygame.K_g,))


class KeyH(Key):
	def __init__(self):
		super().__init__("H", pygame_keys=(pygame.K_h,))


class KeyJ(Key):
	def __init__(self):
		super().__init__("J", pygame_keys=(pygame.K_j,))


class KeyK(Key):
	def __init__(self):
		super().__init__("K", pygame_keys=(pygame.K_k,))


class KeyL(Key):
	def __init__(self):
		super().__init__("L", pygame_keys=(pygame.K_l,))


class KeyColon(Key):
	def __init__(self):
		super().__init__(":", shifted="[", pygame_keys=(pygame.K_SEMICOLON,))


class KeySemicolon(Key):
	def __init__(self):
		super().__init__(";", shifted="]", pygame_keys=(pygame.K_QUOTE,))


class KeyEquals(Key):
	def __init__(self):
		super().__init__("=", pygame_keys=(pygame.K_BACKSLASH,))


class KeyReturn(Key):
	def __init__(self):
		super().__init__("RETURN", width=2.0, legend_top_left=True, pygame_keys=(pygame.K_RETURN, pygame.K_KP_ENTER))


class KeyCommodore(Key):
	def __init__(self):
		super().__init__("C=", pygame_keys=(pygame.K_LCTRL,))


class KeyLeftShift(Key):
	def __init__(self):
		super().__init__("SHIFT", width=1.5, legend_top_left=True, pygame_keys=(pygame.K_LSHIFT,))


class KeyZ(Key):
	def __init__(self):
		super().__init__("Z", pygame_keys=(pygame.K_z,))


class KeyX(Key):
	def __init__(self):
		super().__init__("X", pygame_keys=(pygame.K_x,))


class KeyC(Key):
	def __init__(self):
		super().__init__("C", pygame_keys=(pygame.K_c,))


class KeyV(Key):
	def __init__(self):
		super().__init__("V", pygame_keys=(pygame.K_v,))


class KeyB(Key):
	def __init__(self):
		super().__init__("B", pygame_keys=(pygame.K_b,))


class KeyN(Key):
	def __init__(self):
		super().__init__("N", pygame_keys=(pygame.K_n,))


class KeyM(Key):
	def __init__(self):
		super().__init__("M", pygame_keys=(pygame.K_m,))


class KeyLessThan(Key):
	def __init__(self):
		super().__init__(",", shifted="<", pygame_keys=(pygame.K_COMMA,))


class KeyGreaterThan(Key):
	def __init__(self):
		super().__init__(".", shifted=">", pygame_keys=(pygame.K_PERIOD,))


class KeyQuestionMark(Key):
	def __init__(self):
		super().__init__("/", shifted="?", pygame_keys=(pygame.K_SLASH,))


class KeyRightShift(Key):
	def __init__(self):
		super().__init__("SHIFT", width=1.5, legend_top_left=True, pygame_keys=(pygame.K_RSHIFT,))


class KeyCursorUpDown(Key):
	def __init__(self):
		super().__init__("CRSR", shifted="↑", subtitle="↓", pygame_keys=(pygame.K_UP, pygame.K_DOWN))


class KeyCursorLeftRight(Key):
	def __init__(self):
		super().__init__("CRSR", shifted="←", subtitle="→", pygame_keys=(pygame.K_LEFT, pygame.K_RIGHT))


class KeyF1(FunctionKey):
	def __init__(self):
		super().__init__("f1", "f2", (pygame.K_F1, pygame.K_F2))


class KeyF3(FunctionKey):
	def __init__(self):
		super().__init__("f3", "f4", (pygame.K_F3, pygame.K_F4))


class KeyF5(FunctionKey):
	def __init__(self):
		super().__init__("f5", "f6", (pygame.K_F5, pygame.K_F6))


class KeyF7(FunctionKey):
	def __init__(self):
		super().__init__("f7", "f8", (pygame.K_F7, pygame.K_F8))


class KeySpace(Key):
	def __init__(self):
		super().__init__("", width=9.0, pygame_keys=(pygame.K_SPACE,))
