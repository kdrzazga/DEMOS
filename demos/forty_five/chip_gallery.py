from demos.forty_five.anims.chip_animation import ChipAnimation
from demos.forty_five.chips.labelled_chip import ChipFactory


class ChipGallery:

	def __init__(self, photo_stage):
		self.gap_close_seconds = 1.2
		self.processor_6502 = ChipAnimation(ChipFactory.create_mos_40_pin_chip("6502"), photo_stage)
		self.pia_6520 = ChipAnimation(ChipFactory.create_mos_40_pin_chip("6520"), photo_stage)
		self.via_6522 = ChipAnimation(ChipFactory.create_mos_40_pin_chip("6522"), photo_stage)
		self.basic_rom_901226 = ChipAnimation(ChipFactory.create_rom("901226"), photo_stage)
		self.character_rom_901225 = ChipAnimation(ChipFactory.create_rom("901225"), photo_stage)
		self.kernal_rom_901xxx = ChipAnimation(ChipFactory.create_rom("901xxx"), photo_stage)
		self.vic_chip_6560 = ChipAnimation(ChipFactory.create_mos_40_pin_chip("6560"), photo_stage)
		self.processor_6510 = ChipAnimation(ChipFactory.create_mos_40_pin_chip("6510"), photo_stage)
		self.vic_ii_6567 = ChipAnimation(ChipFactory.create_mos_40_pin_chip("6567"), photo_stage)
		self.cia_6526 = ChipAnimation(ChipFactory.create_mos_40_pin_chip("6526"), photo_stage)
		self.sid_6581 = ChipAnimation(ChipFactory.create_sid(), photo_stage)
		self.second_cia_6526 = ChipAnimation(ChipFactory.create_mos_40_pin_chip("6526"), photo_stage)
		self.gap_left_by_pia_is_closing = False

	@property
	def processor_with_pia_and_via(self):
		return self.processor_6502, self.pia_6520, self.via_6522

	@property
	def first_generation_row(self):
		return self.processor_with_pia_and_via + (self.basic_rom_901226, self.character_rom_901225,
		                                          self.kernal_rom_901xxx, self.vic_chip_6560)

	@property
	def newcomers(self):
		return self.processor_6510, self.vic_ii_6567, self.cia_6526, self.sid_6581, self.second_cia_6526

	@property
	def row_before_assembly(self):
		return (self.processor_6510, self.vic_ii_6567, self.sid_6581, self.cia_6526, self.basic_rom_901226,
		        self.character_rom_901225, self.kernal_rom_901xxx)

	@property
	def chips_listed_for_pet(self):
		return (self.processor_6502, self.pia_6520, self.via_6522, self.basic_rom_901226, self.character_rom_901225,
		        self.kernal_rom_901xxx)

	@property
	def chips_listed_for_vic20(self):
		return (self.processor_6502, self.via_6522, self.basic_rom_901226, self.character_rom_901225,
		        self.kernal_rom_901xxx, self.vic_chip_6560)

	def restart_first_generation(self):
		for chip_animation in self.first_generation_row:
			chip_animation.restart()

	def update(self, seconds):
		for chip_animation in self.first_generation_row + self.newcomers:
			chip_animation.update(seconds)

	def update_processor_with_pia_and_via(self, seconds):
		for chip_animation in self.processor_with_pia_and_via:
			chip_animation.update(seconds)

	def draw_processor_with_pia_and_via(self):
		for chip_animation in self.processor_with_pia_and_via:
			chip_animation.draw()

	def draw_first_generation_row(self):
		for chip_animation in self.first_generation_row:
			chip_animation.draw()

	def draw_with_newcomers(self):
		for chip_animation in self.first_generation_row + self.newcomers:
			chip_animation.draw()

	def line_up_pia_and_via_next_to_processor(self, travel_seconds):
		self.pia_6520.rise_next_to(self.processor_6502, travel_seconds)
		self.via_6522.rise_next_to(self.pia_6520, travel_seconds)

	def close_gap_left_by_pia(self):
		self.gap_left_by_pia_is_closing = True
		chips_right_of_pia = (self.via_6522, self.basic_rom_901226, self.character_rom_901225, self.kernal_rom_901xxx,
		                      self.vic_chip_6560)
		left_neighbour = self.processor_6502
		for chip_animation in chips_right_of_pia:
			chip_animation.rise_next_to(left_neighbour, self.gap_close_seconds)
			left_neighbour = chip_animation

	@property
	def gap_left_by_pia_is_closed(self):
		return self.gap_left_by_pia_is_closing and not any(
			chip_animation.is_gliding for chip_animation in self.first_generation_row)
