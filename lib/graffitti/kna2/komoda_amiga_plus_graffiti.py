from lib.graffitti.graffiti_canvas import GraffitiCanvas
from lib.graffitti.graffiti_piece import GraffitiPiece
from lib.graffitti.keyframes import Keyframes
from lib.graffitti.kna2.dithered_frame import DitheredFrame
from lib.graffitti.kna2.gradient_fill import GradientFill
from lib.graffitti.kna2.letter_outline import LetterOutline
from lib.graffitti.kna2.letter_painter import LetterPainter
from lib.graffitti.kna2.letter_strokes import LETTER_STROKES, SOURCE_SIZE
from lib.graffitti.spray_texture import SprayTexture


class KomodaAmigaPlusGraffiti:

	def __init__(self):
		self.canvas_pixel_width = 2048
		self.frame_clear_border = 50
		self.frame_dither_width = 160
		self.frame_spray_seconds = 1.2
		self.frame_seed = 31
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
		self.gradient_changes_before_blackout = 7
		self.blackout_seconds = 6.0
		self.painter = LetterPainter()
		self.margin = self.frame_clear_border + self.frame_dither_width + self.painter.line_width
		self.outlines = [LetterOutline(name, strokes) for name, strokes in LETTER_STROKES.items()]
		self.painted_letters = {outline.name: self.painter.paint(outline, outline.name not in self.unfilled_caption_names)
		                        for outline in self.outlines}
		self.artwork_size = (round(SOURCE_SIZE[0] * self.painter.scale), round(SOURCE_SIZE[1] * self.painter.scale))
		self.canvas = GraffitiCanvas(self.artwork_size[0] + 2 * self.margin, self.artwork_size[1] + 2 * self.margin,
		                             self.canvas_pixel_width)
		self.dithered_frame = self._dithered_frame()
		self.frame = self._frame_piece()
		self.blackout = self._blackout_piece()
		self.fills = {name: self._letter_fill(painted_letter)
		              for name, painted_letter in self.painted_letters.items() if painted_letter.fill_glyphs}
		self.letters = {name: self._letter_piece(painted_letter)
		                for name, painted_letter in self.painted_letters.items()}
		for name, fill in self.fills.items():
			fill.blink_together_with(self.letters[name])
		self.canvas.add(self.frame, *self.fills.values(), *self.letters.values(), self.blackout)
		self.finale_start_seconds = self._schedule_frame(self._schedule()) + self.finale_pause_seconds
		self.drawn_seconds = self._schedule_finale_blinks()
		self.duration_seconds = self._schedule_blackout(self._schedule_gradient_cycling())

	@property
	def texture(self):
		return self.canvas.texture

	@property
	def frame_color(self):
		return self.painter.line_color

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

	def _dithered_frame(self):
		canvas_size = (self.canvas.logical_width, self.canvas.logical_height)
		canvas_outlines = [outline.transformed(self.painter.scale, self.margin, self.margin)
		                   for outline in self.outlines]
		return DitheredFrame(canvas_size, canvas_outlines, self.painter.line_width, self.frame_clear_border,
		                     self.frame_dither_width, self.painter.line_color)

	def _frame_piece(self):
		return GraffitiPiece(SprayTexture(self.dithered_frame.paint(), self.frame_seed), Keyframes(self._canvas_middle()))

	def _blackout_piece(self):
		spray_texture = SprayTexture(self.dithered_frame.paint_blackout(), self.frame_seed,
		                             self.dithered_frame.blackout_order_map())
		return GraffitiPiece(spray_texture, Keyframes(self._canvas_middle()))

	def _canvas_middle(self):
		return self.canvas.logical_width / 2, self.canvas.logical_height / 2

	def _schedule_blackout(self, blackout_start_seconds):
		self.blackout_start_seconds = blackout_start_seconds
		self.blackout.spray(blackout_start_seconds, self.blackout_seconds)
		return blackout_start_seconds + self.blackout_seconds

	def _schedule_frame(self, letters_end_seconds):
		self.frame.spray(letters_end_seconds, self.frame_spray_seconds)
		self.frame_done_seconds = letters_end_seconds + self.frame_spray_seconds
		return self.frame_done_seconds

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
			cycling_end = cycling_start + self.gradient_changes_before_blackout * fill.cycle.step_seconds
			self.gradient_cycle_seconds = fill.cycle.full_cycle_seconds
		return cycling_end
