from demos.forty_five.c64breadbox.dil_package import DilPackage
from demos.forty_five.chips.dil_chip import DilChip


class MOS6581(DilChip):

	def __init__(self, label="6581", date_code="3184", maker="MOS"):
		self.label = label
		self.date_code = date_code
		self.maker = maker
		super().__init__(DilPackage.wide(28), self._lines())

	def set_label(self, label):
		self.label = label
		self.set_label_lines(self._lines())

	def _lines(self):
		return self.maker, self.label, self.date_code
