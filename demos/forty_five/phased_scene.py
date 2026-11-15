class PhasedScene:

	def __init__(self):
		self.phase = "idle"
		self.phase_seconds = 0.0

	def _enter(self, phase):
		self.phase = phase
		self.phase_seconds = 0.0
