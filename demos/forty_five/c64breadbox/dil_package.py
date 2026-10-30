from dataclasses import dataclass

PIN_PITCH_CM = 0.254
NARROW_ROW_SPACING_CM = 0.762
WIDE_ROW_SPACING_CM = 1.524


@dataclass(frozen=True)
class DilPackage:
	pin_count: int
	row_spacing_cm: float
	pitch_cm: float = PIN_PITCH_CM

	@classmethod
	def narrow(cls, pin_count):
		return cls(pin_count, NARROW_ROW_SPACING_CM)

	@classmethod
	def wide(cls, pin_count):
		return cls(pin_count, WIDE_ROW_SPACING_CM)

	@property
	def pins_per_side(self):
		return self.pin_count // 2

	@property
	def pin_span_cm(self):
		return (self.pins_per_side - 1) * self.pitch_cm

	def pin_position(self, pin_number):
		index = pin_number - 1
		half_span = self.pin_span_cm / 2
		half_spacing = self.row_spacing_cm / 2
		if index < self.pins_per_side:
			return -half_spacing, -half_span + index * self.pitch_cm
		return half_spacing, half_span - (index - self.pins_per_side) * self.pitch_cm

	def pin_positions(self):
		return tuple(self.pin_position(pin_number) for pin_number in range(1, self.pin_count + 1))
