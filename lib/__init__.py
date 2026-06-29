from datetime import datetime


class Globals:
	start_time = datetime.now()

	@classmethod
	def get_duration(cls):
		current_time = datetime.now()
		return current_time - Globals.start_time
