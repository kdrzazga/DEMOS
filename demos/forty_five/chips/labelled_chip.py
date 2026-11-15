from demos.forty_five.c64breadbox.dil_package import DilPackage
from demos.forty_five.chips.dil_chip import DilChip


class LabelledDilChip(DilChip):

	def __init__(self, package, label, date_code, maker=None):
		self.label = label
		self.date_code = date_code
		self.maker = maker
		super().__init__(package, self._lines())

	def set_label(self, label):
		self.label = label
		self.set_label_lines(self._lines())

	def _lines(self):
		if self.maker is None:
			return self.label, self.date_code
		return self.maker, self.label, self.date_code


class ChipFactory:

	@staticmethod
	def create_mos_40_pin_chip(label):
		return LabelledDilChip(DilPackage.wide(40), label, "3184", "MOS")

	@staticmethod
	def create_sid():
		return LabelledDilChip(DilPackage.wide(28), "6581", "3184", "MOS")

	@staticmethod
	def create_pla():
		return LabelledDilChip(DilPackage.wide(28), "906114-01", "3184", "MOS")

	@staticmethod
	def create_rom(label):
		return LabelledDilChip(DilPackage.wide(24), label, "0384", "MOS")

	@staticmethod
	def create_ram():
		return LabelledDilChip(DilPackage.narrow(16), "TMS4164-15NL", "8431")

	@staticmethod
	def create_ttl(label, pin_count):
		return LabelledDilChip(DilPackage.narrow(pin_count), label, "8425")
