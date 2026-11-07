import bisect


class OutlineBlink:

	def __init__(self):
		self.grey_steps = 4
		self.step_seconds = 0.06
		self.hold_seconds = 0.3
		self.blinks = []

	@property
	def fade_seconds(self):
		return self.grey_steps * self.step_seconds

	def duration_seconds(self, speed=1.0):
		return (2 * self.fade_seconds + self.hold_seconds) / speed

	def trigger(self, start_seconds, speed=1.0):
		bisect.insort(self.blinks, (start_seconds, speed))

	def clear(self):
		self.blinks.clear()

	def brightness(self, seconds):
		latest_index = bisect.bisect_right(self.blinks, (seconds, float("inf"))) - 1
		if latest_index < 0:
			return 0.0
		start_seconds, speed = self.blinks[latest_index]
		elapsed_seconds = (seconds - start_seconds) * speed
		if elapsed_seconds < self.fade_seconds:
			return elapsed_seconds / self.fade_seconds
		if elapsed_seconds < self.fade_seconds + self.hold_seconds:
			return 1.0
		if elapsed_seconds < self.duration_seconds():
			return 1.0 - (elapsed_seconds - self.fade_seconds - self.hold_seconds) / self.fade_seconds
		return 0.0
