from lib.graffitti.graffiti_piece import GraffitiPiece
from lib.graffitti.keyframes import Keyframes, linear
from lib.graffitti.spray_texture import SprayOrderMap, SprayTexture


class GradientCycle:

	def __init__(self, gradient_count):
		self.gradient_count = gradient_count
		self.start_seconds = float("inf")
		self.hold_seconds = 2.2
		self.fade_seconds = 0.8

	@property
	def step_seconds(self):
		return self.hold_seconds + self.fade_seconds

	@property
	def full_cycle_seconds(self):
		return self.gradient_count * self.step_seconds

	def _step_and_fade(self, seconds):
		elapsed_seconds = max(0.0, seconds - self.start_seconds)
		step = int(elapsed_seconds // self.step_seconds)
		seconds_into_step = elapsed_seconds - step * self.step_seconds
		fade = min(1.0, max(0.0, (seconds_into_step - self.hold_seconds) / self.fade_seconds))
		return step, fade

	def draw_order(self, seconds):
		step, _ = self._step_and_fade(seconds)
		return [step % self.gradient_count, (step + 1) % self.gradient_count]

	def opacity(self, gradient_index, seconds):
		step, fade = self._step_and_fade(seconds)
		if gradient_index == step % self.gradient_count:
			return 1.0
		if gradient_index == (step + 1) % self.gradient_count:
			return fade
		return 0.0


class LayerOpacity:

	def __init__(self, cycle, gradient_index):
		self.cycle = cycle
		self.gradient_index = gradient_index

	def value(self, seconds):
		return self.cycle.opacity(self.gradient_index, seconds)


class GradientFill:

	def __init__(self, fill_glyphs, center, seed):
		self.cycle = GradientCycle(len(fill_glyphs))
		self.position = Keyframes(center)
		self.progress = Keyframes(0.0)
		self.layers = [self._layer(glyph, gradient_index, seed) for gradient_index, glyph in enumerate(fill_glyphs)]

	def _layer(self, glyph, gradient_index, seed):
		layer = GraffitiPiece(SprayTexture(glyph, seed, self._order_map_ignoring_dark_colors(seed)), self.position)
		layer.progress = self.progress
		layer.opacity = LayerOpacity(self.cycle, gradient_index)
		return layer

	@staticmethod
	def _order_map_ignoring_dark_colors(seed):
		order_map = SprayOrderMap(seed)
		order_map.outline_brightness_limit = 0
		return order_map

	def spray(self, start_seconds, duration_seconds):
		self.progress.animate(start_seconds, duration_seconds, 1.0, linear)
		return self

	def blink_together_with(self, outline_piece):
		for layer in self.layers:
			layer.outline_blink = outline_piece.outline_blink
		return self

	def cycle_gradients_from(self, start_seconds):
		self.cycle.start_seconds = start_seconds
		return self

	def draw(self, seconds, shader):
		for gradient_index in self.cycle.draw_order(seconds):
			self.layers[gradient_index].draw(seconds, shader)
