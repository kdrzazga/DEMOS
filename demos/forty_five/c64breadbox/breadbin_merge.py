from lib.flying_logo import ease_out_cubic


class BreadbinMergeStep:

	def __init__(self, start_second, seconds, start_offset, apply_offset):
		self.start_second = start_second
		self.seconds = seconds
		self.start_offset = start_offset
		self.apply_offset = apply_offset

	@property
	def end_second(self):
		return self.start_second + self.seconds

	def apply(self, elapsed_seconds):
		progress = min(1.0, max(0.0, (elapsed_seconds - self.start_second) / self.seconds))
		remaining = 1.0 - ease_out_cubic(progress)
		self.apply_offset(tuple(coordinate * remaining for coordinate in self.start_offset))


class BreadbinMerge:

	def __init__(self, breadbin, board_drops_in):
		self.breadbin = breadbin
		self.base_rise_seconds = 1.5
		self.board_drop_seconds = 1.5
		self.keyboard_drop_seconds = 1.5
		self.top_drop_seconds = 2.0
		self.pause_seconds_between_parts = 0.3
		self.base_start_offset = (0.0, -25.0, 0.0)
		self.board_start_offset = (0.0, 20.0, 0.0)
		self.keyboard_start_offset = (0.0, 20.0, 0.0)
		self.top_start_offset = (0.0, 30.0, 0.0)
		board_step = ((self.board_drop_seconds, self.board_start_offset, self._set_board_offset),) if board_drops_in else ()
		self.steps = self._steps_one_after_another(
			((self.base_rise_seconds, self.base_start_offset, self._set_base_offset),)
			+ board_step
			+ ((self.keyboard_drop_seconds, self.keyboard_start_offset, self._set_keyboard_offset),
			   (self.top_drop_seconds, self.top_start_offset, self._set_top_offset)))
		self.elapsed_seconds = 0.0
		self.restart()

	def _steps_one_after_another(self, step_settings):
		steps = []
		start_second = 0.0
		for seconds, start_offset, apply_offset in step_settings:
			steps.append(BreadbinMergeStep(start_second, seconds, start_offset, apply_offset))
			start_second += seconds + self.pause_seconds_between_parts
		return tuple(steps)

	def _set_base_offset(self, offset):
		self.breadbin.base_offset = offset

	def _set_board_offset(self, offset):
		self.breadbin.board_assembly_offset = offset

	def _set_top_offset(self, offset):
		self.breadbin.top_offset = offset

	def _set_keyboard_offset(self, offset):
		self.breadbin.keyboard_offset = offset

	@property
	def done(self):
		return self.elapsed_seconds >= max(step.end_second for step in self.steps)

	def restart(self):
		self.elapsed_seconds = 0.0
		self._apply()

	def update(self, seconds):
		self.elapsed_seconds += seconds
		self._apply()

	def _apply(self):
		for step in self.steps:
			step.apply(self.elapsed_seconds)
