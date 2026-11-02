class MusicFadeOut:

	def __init__(self):
		self.start_frame = 14600+300
		self.frames_per_volume_step = 30
		self.volume_step = 0.01
		self.frame = 0

	def advance(self):
		self.frame += 1

	@property
	def volume_factor(self):
		if self.frame < self.start_frame:
			return 1.0
		steps_taken = (self.frame - self.start_frame) // self.frames_per_volume_step + 1
		return max(0.2, 1.0 - steps_taken * self.volume_step)
