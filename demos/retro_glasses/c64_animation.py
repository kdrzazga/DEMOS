import os

from lib.c64_screen import C64Screen
from lib.animated_sprite import PygameAnimatedSprite
from lib.specialFX.stripes import StripeEffects
from lib.specialFX.unsynced import UnsyncedPicture
from lib.typing_effect.c64_typer import C64Typer


class C64Animation:

	def __init__(self):
		self.c64screen = C64Screen()
		self.instant_speed = 2500.0
		self.row = 6
		self.time = 2.5
		self.final_pause = 2.0
		self.picture_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources", "koalagfx.png")
		self.picture_frame_count = 29
		self.picture_frames_per_second = 10.0
		self.picture_duration = 6.0
		self.picture_start = 0.0
		self.typers = []
		border = self.c64screen.border
		screen_width = self.c64screen.width - 2 * border
		screen_height = self.c64screen.height - 2 * border
		band_in_area = (0.1, 0.25)
		whole_area = (1.0, 1.0)
		area_shares_band_shares_and_lines = [(0.2, 0.6, band_in_area, 80), (0.05, 0.9, whole_area, 120),
											 (0.35, 0.3, band_in_area, 80), (0.0, 0.45, band_in_area, 80),
											 (0.0, 1.0, whole_area, 170)]
		self.blue_interference_areas = [
			(border, border + round(screen_height * top_share), screen_width, round(screen_height * height_share),
			 lines, 0.7, band_share)
			for top_share, height_share, band_share, lines in area_shares_band_shares_and_lines
		]
		self.blue_interference_duration = 0.4
		self.blue_interference_moments = []
		self.blue_interferences = []
		for index, area in enumerate(self.blue_interference_areas):
			stripe_effects = StripeEffects(seed=index + 1)
			stripe_effects.blue_height_share = area[6]
			stripe_effects.blue_blink_period = self.blue_interference_duration
			stripe_effects.blue_blink_duration = self.blue_interference_duration
			stripe_effects.blue_travel_period = 2.0 * self.blue_interference_duration
			self.blue_interferences.append(stripe_effects)
		self.unsynced_picture = UnsyncedPicture()
		self.typing_unsync_count = 6
		self.picture_unsync_count = 1
		self.unsync_moments = []
		self.type_command('LOAD"$",8')
		self.skip_line()
		self.print_line("SEARCHING FOR $")
		self.pause(0.5)
		self.print_line("LOADING")
		self.pause(1.0)
		self.print_prompt()
		self.pause(0.5)
		self.type_command("LIST")
		self.skip_line()
		self.print_directory_header("0 ", '"VAMOS, KURWA!      "      3D')
		self.print_line('120  "KOALAGFX"              CBM')
		self.print_line('20   "BOCA-JRS"              PRG')
		self.print_line('23   "RIVERPLT"              PRG')
		self.print_line('21   "SLORENZO"              PRG')
		self.print_line('120  "PORN"                  CBM')
		self.print_line("2856 BLOCKS FREE.")
		self.print_prompt()
		self.pause(1.0)
		self.type_command('OPEN 15,8,15,"CD:KOALAGFX" : CLOSE15')
		self.skip_line()
		self.print_prompt()
		self.pause(0.3)
		self.type_command('LOAD"$",8')
		self.skip_line()
		self.print_line("SEARCHING FOR $")
		self.pause(0.3)
		self.print_line("LOADING")
		self.pause(1.1)
		self.print_prompt()
		self.pause(0.4)
		self.type_command("LIST")
		self.skip_line()
		self.print_directory_header("0 ", '"VAMOS, KURWA!      "      3D')
		self.print_line('38   "MARADONA.PRG"          PRG')
		self.print_line('36   "FRANCIS1"              PRG')
		self.print_line('40   "HEAD"                  PRG')
		self.print_line("2 BLOCKS FREE.")
		self.print_prompt()
		self.pause(1.0)
		self.type_command('LOAD"HEAD",8,1')
		self.skip_line()
		self.print_line("SEARCHING FOR HEAD")
		self.pause(0.3)
		self.print_line("LOADING")
		self.pause(0.4)
		self.print_prompt()
		self.type_command("RUN")
		self.pause(0.1)
		self.show_picture()
		self.c64screen.set_typers(self.typers)
		self.spread_blue_interferences()
		self.spread_unsyncs()

	@property
	def duration(self):
		return self.time + self.final_pause

	def add_typer(self, text, column, instant):
		typer = C64Typer(self.c64screen.frame, self.row, column, text, self.time)
		if instant:
			typer.set_speed(self.instant_speed)
			typer.shows_cursor = False
		self.typers.append(typer)
		self.time = typer.finish_time
		return typer

	def type_command(self, text):
		self.add_typer(text, 0, False)
		self.row += 1

	def print_line(self, text):
		self.add_typer(text, 0, True)
		self.row += 1

	def print_prompt(self):
		self.add_typer("READY.", 0, True).shows_cursor = True
		self.row += 1

	def print_directory_header(self, number, title):
		self.add_typer(number, 0, True)
		self.add_typer(title, len(number), True).reverse_color = True
		self.row += 1

	def show_picture(self):
		frame_width = self.c64screen.frame.columns * self.c64screen.frame.cell_width
		frame_height = self.c64screen.frame.rows * self.c64screen.frame.cell_height
		center_x, center_y = self.c64screen.center
		sprite = PygameAnimatedSprite(self.picture_path, center_x, center_y, frame_width, frame_height,
									  self.picture_frame_count, 1.0 / self.picture_frames_per_second)
		self.picture_start = self.time
		self.c64screen.show_picture(sprite, self.time)
		self.pause(self.picture_duration)

	def spread_blue_interferences(self):
		"""One short moment per interference, evenly spread before the animated picture shows."""
		count = len(self.blue_interferences)
		self.blue_interference_moments = [self.picture_start * (index + 1) / (count + 1) for index in range(count)]

	def draw_interference(self, corner, pixel_size):
		"""Draws the blue interference whose moment is running over the C64 screen whose top-left pixel is at corner."""
		c64_time = self.c64screen.startup_text.time
		for stripe_effects, area, moment in zip(self.blue_interferences, self.blue_interference_areas,
												self.blue_interference_moments):
			if not moment <= c64_time < moment + self.blue_interference_duration:
				continue
			x, y, width, height, stripes_count, transparency, _ = area
			stripe_effects.time = c64_time - moment
			stripe_effects.place_picture(corner, pixel_size)
			stripe_effects.blue_interference(x, y, width, height, stripes_count, transparency=transparency)

	def spread_unsyncs(self):
		typing_moments = [self.picture_start * (index + 1) / (self.typing_unsync_count + 1)
						  for index in range(self.typing_unsync_count)]
		picture_moments = [self.picture_start + self.picture_duration * (index + 1) / (self.picture_unsync_count + 1)
						   for index in range(self.picture_unsync_count)]
		self.unsync_moments = typing_moments + picture_moments

	@property
	def unsync_duration(self):
		unsynced = self.unsynced_picture
		return unsynced.jump_count * (unsynced.steady_duration + unsynced.flipped_duration)

	def draw_unsync(self):
		c64_time = self.c64screen.startup_text.time
		for moment in self.unsync_moments:
			if moment <= c64_time < moment + self.unsync_duration:
				self.unsynced_picture.time = c64_time - moment
				self.unsynced_picture.draw()
				return

	def skip_line(self):
		self.row += 1

	def pause(self, seconds):
		self.time += seconds
