from lib.pointed_name_label import OutlinedTextTexture, ScreenSpaceProjector


class CaptionSequence:

	def __init__(self, captions, seconds_per_caption=0.75, pause_seconds_between_captions=0.25,
	             text_color=(230, 40, 40), envelope_color=(0, 0, 0), screen_scale=1.0, font_pixel_size=40,
	             margin_from_top_left_pixels=(24.0, 20.0)):
		self.captions = captions
		self.seconds_per_caption = seconds_per_caption
		self.pause_seconds_between_captions = pause_seconds_between_captions
		self.margin_from_top_left_pixels = (margin_from_top_left_pixels[0] * screen_scale,
		                                    margin_from_top_left_pixels[1] * screen_scale)
		self.caption_textures = [OutlinedTextTexture(caption, max(10, round(font_pixel_size * screen_scale)),
		                                             text_color=text_color, envelope_color=envelope_color)
		                         for caption in captions]
		self.reset()

	def reset(self):
		self.elapsed_seconds = None

	def start(self):
		self.elapsed_seconds = 0.0

	@property
	def started(self):
		return self.elapsed_seconds is not None

	@property
	def seconds_from_one_caption_start_to_the_next(self):
		return self.seconds_per_caption + self.pause_seconds_between_captions

	@property
	def total_seconds(self):
		return self.seconds_from_one_caption_start_to_the_next * len(self.captions) - self.pause_seconds_between_captions

	@property
	def finished(self):
		return self.started and self.elapsed_seconds >= self.total_seconds

	def update(self, seconds):
		if self.started:
			self.elapsed_seconds += seconds

	def _currently_shown_caption_texture(self):
		if not self.started or self.finished:
			return None
		caption_index = int(self.elapsed_seconds // self.seconds_from_one_caption_start_to_the_next)
		seconds_into_caption = self.elapsed_seconds - caption_index * self.seconds_from_one_caption_start_to_the_next
		if seconds_into_caption >= self.seconds_per_caption:
			return None
		return self.caption_textures[caption_index]

	def draw(self):
		caption_texture = self._currently_shown_caption_texture()
		if caption_texture is None:
			return
		projector = ScreenSpaceProjector()
		projector.begin_pixel_overlay()
		caption_texture.draw_with_top_left_at(*self.margin_from_top_left_pixels, 1.0)
		projector.end_pixel_overlay()

	def destroy(self):
		for caption_texture in self.caption_textures:
			caption_texture.destroy()
		self.caption_textures = []
