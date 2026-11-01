from demos.forty_five.c64breadbox.dil_package import DilPackage
from demos.forty_five.chips.dil_chip import DilChip


class TMS4164(DilChip):

	def __init__(self, label="TMS4164-15NL", date_code="8431"):
		self.label = label
		self.date_code = date_code
		super().__init__(DilPackage.narrow(16), self._lines())

	def set_label(self, label):
		self.label = label
		self.set_label_lines(self._lines())

	def _lines(self):
		return self.label, self.date_code
