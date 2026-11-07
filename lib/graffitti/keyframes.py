def linear(progress):
	return progress


def ease_in_out(progress):
	return progress * progress * (3.0 - 2.0 * progress)


def blend(origin, target, amount):
	if isinstance(origin, tuple):
		return tuple(start + (end - start) * amount for start, end in zip(origin, target))
	return origin + (target - origin) * amount


class Keyframes:

	def __init__(self, initial_value):
		self.initial_value = initial_value
		self.segments = []

	@property
	def final_value(self):
		return self.segments[-1][3] if self.segments else self.initial_value

	def animate(self, start_seconds, duration_seconds, target_value, easing=ease_in_out):
		self.segments.append((start_seconds, duration_seconds, self.final_value, target_value, easing))
		return self

	def jump(self, start_seconds, target_value):
		return self.animate(start_seconds, 0.0, target_value)

	def value(self, seconds):
		current_value = self.initial_value
		for start_seconds, duration_seconds, origin_value, target_value, easing in self.segments:
			if seconds < start_seconds:
				break
			if duration_seconds <= 0.0 or seconds >= start_seconds + duration_seconds:
				current_value = target_value
				continue
			return blend(origin_value, target_value, easing((seconds - start_seconds) / duration_seconds))
		return current_value


class OffsetTrack:

	def __init__(self, base_track, offset_track):
		self.base_track = base_track
		self.offset_track = offset_track

	def value(self, seconds):
		base_point = self.base_track.value(seconds)
		offset_point = self.offset_track.value(seconds)
		return tuple(base + offset for base, offset in zip(base_point, offset_point))
