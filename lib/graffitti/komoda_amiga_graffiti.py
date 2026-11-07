from lib.graffitti.caption_row import CaptionRow
from lib.graffitti.eye_painter import EyePainter, EyesSheet
from lib.graffitti.graffiti_canvas import GraffitiCanvas
from lib.graffitti.graffiti_eye import GraffitiEye
from lib.graffitti.graffiti_piece import GraffitiPiece
from lib.graffitti.graffiti_sheet import GraffitiGlyph, GraffitiSheet
from lib.graffitti.keyframes import Keyframes
from lib.graffitti.spray_texture import SprayTexture


class KomodaAmigaGraffiti:

	def __init__(self, sheet=None, canvas_pixel_width=2048):
		self.sheet = sheet or GraffitiSheet()
		self.margin = 110
		self.row_gap = 34
		self.ampersand_scale = 1.5
		self.mouth_scale = 1.7
		self.komoda_offsets = {2: (-131, 75), 3: (-90, 75), 4: (-200, 155), 5: (-352, 50)}
		self.amiga_offsets = {0: (25, 90), 1: (20, 27), 2: (0, -73), 4: (-90, 150), 5: (-90, 150)}
		self.mouth_drop = 260
		self.letter_spray_seconds = 1.1
		self.letter_interval_seconds = 0.8
		self.seed = 7
		self.amiga_letter_names = ("A2", "M2", "I", "G", "A3", "PLUS")

		eyes_sheet = EyesSheet()
		self.left_eye = GraffitiEye(self._eye_painter(eyes_sheet.left_eye, "K", "M1"), (0.0, 0.0), self._next_seed())
		self.right_eye = GraffitiEye(self._eye_painter(eyes_sheet.right_eye, "M1", "D"), (0.0, 0.0), self._next_seed())
		self.komoda_row = CaptionRow([self.sheet["K"], self.left_eye.letter_glyph, self.sheet["M1"],
		                              self.right_eye.letter_glyph, self.sheet["D"], self.sheet["A1"]],
		                             offsets=self.komoda_offsets)
		self.amiga_row = CaptionRow([self.sheet[name] for name in self.amiga_letter_names],
		                            offsets=self.amiga_offsets)
		ampersand_height = self.sheet["AMPERSAND"].size[1] * self.ampersand_scale

		content_width = max(self.komoda_row.width, self.amiga_row.width) + 2 * self.margin
		content_height = (2 * self.margin + self.komoda_row.height + ampersand_height + self.amiga_row.height
		                  + 2 * self.row_gap)
		content_center_x = content_width / 2
		komoda_top = self.margin
		ampersand_center_y = komoda_top + self.komoda_row.height + self.row_gap + ampersand_height / 2
		amiga_top = ampersand_center_y + ampersand_height / 2 + self.row_gap
		komoda_centers = self.komoda_row.centers(content_center_x, komoda_top)
		amiga_centers = self.amiga_row.centers(content_center_x, amiga_top)

		eyes_middle_x = (komoda_centers[1][0] + komoda_centers[3][0]) / 2
		eyes_bottom_y = max(komoda_centers[index][1] + self.komoda_row.glyphs[index].size[1] / 2 for index in (1, 3))
		shift_x = max(0.0, content_width - 2 * eyes_middle_x)
		shift_y = max(0.0, content_height - 2 * eyes_bottom_y)
		canvas_width = 2 * (eyes_middle_x + shift_x)
		canvas_height = 2 * (eyes_bottom_y + shift_y)
		self.canvas = GraffitiCanvas(canvas_width, canvas_height, canvas_pixel_width)

		self.komoda_centers = [(x + shift_x, y + shift_y) for x, y in komoda_centers]
		self.amiga_centers = [(x + shift_x, y + shift_y) for x, y in amiga_centers]
		self.ampersand_center = (content_center_x + shift_x, ampersand_center_y + shift_y)
		left_eye_center, right_eye_center = self.komoda_centers[1], self.komoda_centers[3]
		self.mouth_center = ((left_eye_center[0] + right_eye_center[0]) / 2,
		                     max(left_eye_center[1], right_eye_center[1]) + self.mouth_drop)

		self.komoda_pieces = {name: self._letter_piece(name, center)
		                      for name, center in zip(("K", "M1", "D", "A1"), self._komoda_letter_centers())}
		self.amiga_pieces = [self._letter_piece(name, center)
		                     for name, center in zip(self.amiga_letter_names, self.amiga_centers)]
		self.mouth = GraffitiPiece(SprayTexture(GraffitiGlyph.from_resource("MOUTH", "mouth.png"), self._next_seed()),
		                           Keyframes(self.mouth_center), self.mouth_scale)
		self.ampersand = GraffitiPiece(SprayTexture(self.sheet["AMPERSAND"], self._next_seed()),
		                               Keyframes(self.ampersand_center), self.ampersand_scale)

		self.canvas.add(*self.left_eye.pieces, *self.right_eye.pieces, self.mouth, self.ampersand,
		                *self.komoda_pieces.values(), *self.amiga_pieces)
		self.duration_seconds = self._schedule()

	@property
	def texture(self):
		return self.canvas.texture

	@property
	def aspect_ratio(self):
		return self.canvas.aspect_ratio

	def render(self, seconds):
		self.canvas.render(seconds)

	def _next_seed(self):
		self.seed += 1
		return self.seed

	def _eye_painter(self, eye_surface, left_letter, right_letter):
		return EyePainter(eye_surface, self.sheet[left_letter].average_fill_color,
		                  self.sheet[right_letter].average_fill_color)

	def _komoda_letter_centers(self):
		return [self.komoda_centers[index] for index in (0, 2, 4, 5)]

	def _letter_piece(self, name, center):
		return GraffitiPiece(SprayTexture(self.sheet[name], self._next_seed()), Keyframes(center))

	def _schedule(self):
		self.left_eye.position.jump(0.0, self.komoda_centers[1])
		self.right_eye.position.jump(0.0, self.komoda_centers[3])
		self.left_eye.spray(0.3, 1.4)
		self.right_eye.spray(0.9, 1.4)
		self.mouth.spray(2.6, 1.6)

		for eye in (self.left_eye, self.right_eye):
			eye.look_towards(4.4, 0.35, -1.0, 0.2)
			eye.look_towards(5.2, 0.45, 1.0, 0.2)
			eye.look_towards(6.0, 0.35, 0.0, -0.6)
			eye.look_towards(6.8, 0.3, 0.0, 0.0)

		self.mouth.unspray(7.2, 1.2)

		self.left_eye.become_letter_o(8.6, 1.2)
		self.right_eye.become_letter_o(8.6, 1.2)

		letter_start = 9.8
		for index, name in enumerate(("K", "M1", "D", "A1")):
			self.komoda_pieces[name].spray(letter_start + index * self.letter_interval_seconds,
			                               self.letter_spray_seconds)

		ampersand_start = letter_start + 4 * self.letter_interval_seconds + 0.8
		self.ampersand.spray(ampersand_start, 1.2)

		amiga_start = ampersand_start + 1.6
		for index, piece in enumerate(self.amiga_pieces):
			piece.spray(amiga_start + index * self.letter_interval_seconds, self.letter_spray_seconds)
		return amiga_start + (len(self.amiga_pieces) - 1) * self.letter_interval_seconds + self.letter_spray_seconds
