"""Lyric timing for MarchOnWithIBM.mp3.

Each entry is (start_second, line): the second at which that line starts being
sung. Timestamps were supplied by ear, so nudge them against the recording if a
line drifts.
"""


class MarchOnWithIBM:

	TUNE = "MarchOnWithIBM.mp3"

	LINES = [
		(4, "The fame of IBM"),
		(9, "spreads across the seven seas."),
		(12, "Our standards fly aloft"),
		(16, "proudly waving in the breeze."),
		(21, "With T.J. Watson guiding us"),
		(25, "we lead throughout the world."),
		(29, "For peace and trade our"),
		(32, "banners are unfurled, unfurled"),
		(38, "March on with IBM"),
		(42, "We lead the way"),
		(46, "Onward we'll ever go"),
		(50, "in strong array."),
		(54, "Our flags on every shore"),
		(59, "We march with them"),
		(63, "On high forevermore"),
		(67, "for IBM !!!"),
	]

	@classmethod
	def line_at(cls, seconds):
		if seconds > 70:
			return ""
		current = None
		for start, text in cls.LINES:
			if seconds < start:
				break
			current = text
		return current
