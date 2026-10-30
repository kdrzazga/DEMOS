from demos.forty_five.c64breadbox.dil_package import DilPackage
from demos.forty_five.chips.dil_chip import DilChip


class MOS901xxx(DilChip):

	def __init__(self, label="901226-01", date_code="0384", maker="MOS", **chip_options):
		self.label = label
		self.date_code = date_code
		self.maker = maker
		super().__init__(DilPackage.wide(24), self._lines(), **chip_options)

	def set_label(self, label):
		self.label = label
		self.set_label_lines(self._lines())

	def _lines(self):
		return self.maker, self.label, self.date_code
