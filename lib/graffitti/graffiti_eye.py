from lib.graffitti.graffiti_piece import GraffitiPiece
from lib.graffitti.keyframes import Keyframes, OffsetTrack
from lib.graffitti.spray_texture import SprayTexture


class GraffitiEye:

	def __init__(self, painter, position, seed):
		self.painter = painter
		self.letter_glyph = painter.paint_outline()
		self.position = Keyframes(position)
		self.look = Keyframes((0.0, 0.0))
		self.sclera = GraffitiPiece(SprayTexture(painter.paint_sclera(), seed), self.position)
		self.pupil = GraffitiPiece(SprayTexture(painter.paint_pupil(), seed + 1), OffsetTrack(self.position, self.look))
		self.letter_fill = GraffitiPiece(SprayTexture(painter.paint_letter_fill(), seed + 2), self.position)
		self.outline = GraffitiPiece(SprayTexture(self.letter_glyph, seed + 3), self.position)

	@property
	def pieces(self):
		return [self.sclera, self.pupil, self.letter_fill, self.outline]

	def spray(self, start_seconds, duration_seconds):
		self.outline.spray(start_seconds, duration_seconds * 0.6)
		self.sclera.spray(start_seconds + duration_seconds * 0.3, duration_seconds * 0.7)
		self.pupil.spray(start_seconds + duration_seconds, duration_seconds * 0.35)
		return self

	def blink_outline(self, start_seconds, speed=1.0):
		self.outline.blink_outline(start_seconds, speed)
		self.letter_fill.blink_outline(start_seconds, speed)
		return self

	def look_towards(self, start_seconds, duration_seconds, direction_x, direction_y):
		travel_x, travel_y = self.painter.pupil_travel
		self.look.animate(start_seconds, duration_seconds, (direction_x * travel_x, direction_y * travel_y))
		return self

	def become_letter_o(self, start_seconds, duration_seconds):
		self.pupil.fade_out(start_seconds, duration_seconds * 0.4)
		self.letter_fill.spray(start_seconds, duration_seconds)
		self.sclera.fade_out(start_seconds + duration_seconds * 0.5, duration_seconds * 0.5)
		return self
