from lib.graffitti.graffiti_canvas import GraffitiCanvas
from lib.graffitti.graffiti_piece import GraffitiPiece
from lib.graffitti.keyframes import Keyframes
from lib.graffitti.kna2.gradient_fill import GradientFill
from lib.graffitti.kna2.letter_outline import LetterOutline
from lib.graffitti.kna2.letter_painter import LetterPainter
from lib.graffitti.kna2.letter_strokes import LETTER_STROKES, SOURCE_SIZE
from lib.graffitti.spray_texture import SprayTexture


class KomodaAmigaPlusGraffiti:

	def __init__(self):
		self.canvas_pixel_width = 2048
		self.margin = 60
		self.pen_speed = 1800.0
		self.start_seconds = 0.3
		self.letter_pause_seconds = 0.12
		self.fill_start_share = 0.5
		self.fill_spray_seconds = 0.7
		self.fill_seed = 23
		self.finale_pause_seconds = 0.4
		self.finale_wave_stagger_seconds = 0.08
		self.gradient_wave_stagger_seconds = 0.15
		self.unfilled_caption_names = ("AND", "PLUS")
		self.painter = LetterPainter()
		self.outlines = [LetterOutline(name, strokes) for name, strokes in LETTER_STROKES.items()]
		self.painted_letters = {outline.name: self.painter.paint(outline, outline.name not in self.unfilled_caption_names)
		                        for outline in self.outlines}
		self.canvas = GraffitiCanvas(SOURCE_SIZE[0] * self.painter.scale + 2 * self.margin,
		                             SOURCE_SIZE[1] * self.painter.scale + 2 * self.margin,
		                             self.canvas_pixel_width)
		self.fills = {name: self._letter_fill(painted_letter)
		              for name, painted_letter in self.painted_letters.items() if painted_letter.fill_glyphs}
		self.letters = {name: self._letter_piece(painted_letter)
		                for name, painted_letter in self.painted_letters.items()}
		self.canvas.add(*self.fills.values(), *self.letters.values())
		self.finale_start_seconds = self._schedule() + self.finale_pause_seconds
		self.drawn_seconds = self._schedule_finale_blinks()
		self.duration_seconds = self._schedule_gradient_cycling()

	@property
	def texture(self):
		return self.canvas.texture

	@property
	def aspect_ratio(self):
		return self.canvas.aspect_ratio

	def render(self, seconds):
		self.canvas.render(seconds)

	def blink_outline(self, letter_name, start_seconds, speed=1.0):
		self.letters[letter_name].blink_outline(start_seconds, speed)

	def blink_all_outlines(self, start_seconds, stagger_seconds=0.0, speed=1.0):
		for index, letter in enumerate(self.letters.values()):
			letter.blink_outline(start_seconds + index * stagger_seconds, speed)
		return start_seconds + (len(self.letters) - 1) * stagger_seconds + self._blink_duration(speed)

	def reset_outline_blinks(self):
		for letter in self.letters.values():
			letter.outline_blink.clear()
		self._schedule_finale_blinks()

	def _blink_duration(self, speed):
		return next(iter(self.letters.values())).outline_blink.duration_seconds(speed)

	def _canvas_center(self, painted_letter):
		center_x, center_y = painted_letter.center
		return center_x + self.margin, center_y + self.margin

	def _letter_piece(self, painted_letter):
		spray_texture = SprayTexture(painted_letter.line_glyph, 0, painted_letter.order_map)
		return GraffitiPiece(spray_texture, Keyframes(self._canvas_center(painted_letter)))

	def _letter_fill(self, painted_letter):
		return GradientFill(painted_letter.fill_glyphs, self._canvas_center(painted_letter), self.fill_seed)

	def _schedule(self):
		letter_start = self.start_seconds
		fill_end = letter_start
		for name, letter in self.letters.items():
			drawing_seconds = self.painted_letters[name].total_length / self.pen_speed
			letter.spray(letter_start, drawing_seconds)
			if name in self.fills:
				fill_start = letter_start + drawing_seconds * self.fill_start_share
				self.fills[name].spray(fill_start, self.fill_spray_seconds)
				fill_end = fill_start + self.fill_spray_seconds
			letter_start += drawing_seconds + self.letter_pause_seconds
		return max(letter_start - self.letter_pause_seconds, fill_end)

	def _schedule_finale_blinks(self):
		return self.blink_all_outlines(self.finale_start_seconds, self.finale_wave_stagger_seconds)

	def _schedule_gradient_cycling(self):
		cycling_end = self.drawn_seconds
		for index, fill in enumerate(self.fills.values()):
			cycling_start = self.drawn_seconds + index * self.gradient_wave_stagger_seconds
			fill.cycle_gradients_from(cycling_start)
			cycling_end = cycling_start + fill.cycle.full_cycle_seconds
		return cycling_end
