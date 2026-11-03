from lib.c64_screen import C64Screen
from lib.typing_effect.c64_typer import C64Typer


class C64Animation:

	def __init__(self):
		self.c64screen = C64Screen()
		self.instant_speed = 1000.0
		self.row = 6
		self.time = 2.5
		self.final_pause = 2.0
		self.typers = []
		self.type_command('LOAD"$",8')
		self.skip_line()
		self.print_line("SEARCHING FOR $")
		self.pause(1.0)
		self.print_line("LOADING")
		self.pause(2.0)
		self.print_prompt()
		self.pause(1.0)
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
		self.pause(6.0)
		self.type_command('OPEN 15,8,15,"CD:KOALAGFX" : CLOSE15')
		self.skip_line()
		self.print_prompt()
		self.pause(1.0)
		self.type_command('LOAD"$",8')
		self.c64screen.set_typers(self.typers)

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

	def skip_line(self):
		self.row += 1

	def pause(self, seconds):
		self.time += seconds
