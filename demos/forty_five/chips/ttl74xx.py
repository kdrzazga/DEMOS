from demos.forty_five.c64breadbox.dil_package import DilPackage
from demos.forty_five.chips.dil_chip import DilChip


class TTL74xx(DilChip):

	def __init__(self, label, pin_count, date_code="8425"):
		self.label = label
		self.date_code = date_code
		super().__init__(DilPackage.narrow(pin_count), self._lines())

	def set_label(self, label):
		self.label = label
		self.set_label_lines(self._lines())

	def _lines(self):
		return self.label, self.date_code
