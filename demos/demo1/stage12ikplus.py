import math

import arcade
from arcade import Rect, Sprite, Text
from arcade.color import WHITE, BLACK
from arcade.types import Color

from demos.demo1 import Globals, Constants
from demos.demo1.base import Demo1Base
from demos.demo1.stage11team import Stage11
from lib.animated_sprite import AnimatedSprite
from lib.tunnel import IsometricSineTunnel


class Stage12(Demo1Base):
	START_FRAME = Stage11.START_FRAME + 350

	def __init__(self):
		super().__init__()
		self.bkg_color = Color.from_hex_string("000000")
		self.kurwes = []
		for i in range(254):
			g = abs(int(252 * math.sin(i / 20)) + 2)
			b = abs(i - 128)
			sine = IsometricSineTunnel(Color(255, g, b), angle_deg=int(370 * i / 255))
			self.kurwes.append(sine)

		self.amplitude = 15
		self.frequency = 0.05
		self.speed = 160
		self.horizon_x = self.width * 0.01

		self.grandpa_speech = GameListSpeech(self.width, self.height)

		self.ground = Sprite("demos/demo1/resources/ik/ground.png", center_x=Constants.WIDTH//2, center_y=-205
		                     ,scale=1.33)
		self.tree = Sprite("demos/demo1/resources/ik/tree.png", center_x=Constants.WIDTH*1.3, center_y=305
		                     ,scale=2.5)
		self.grandpa = Sprite("demos/demo1/resources/ik/ik-grandpa.png", center_x=Constants.WIDTH * 0.6, center_y=-205
		                     ,scale=0.6)
		self.tori = Sprite("demos/demo1/resources/ik/tori.png", center_x=Constants.WIDTH * 0.25, center_y=305
		                     ,scale=2.5)
		self.left_flying_kick = AnimatedSprite("demos/demo1/resources/ik/lfkick.png"
		                                       , position_x=Constants.WIDTH*1.3, position_y=200
		                                       ,frame_width=60, frame_height=40, frame_delay=0.1, num_frames=3)
		self.left_flying_kick.sprite.scale = (2.5, 2.5)

		self.diskette = Sprite("demos/demo1/resources/ik/disketteSmall.png", center_x=Constants.WIDTH // 2
		                       , center_y=Constants.HEIGHT//2)

		self.balls = [Ball() for _ in range(20)]

	def on_update(self, frame, klass):
		self.left_flying_kick.update(0.16)
		realtive_frame = frame - Stage12.START_FRAME
		if realtive_frame == 1:
			print(self.__class__.__name__ + " ", Globals.get_duration(), "[frame", str(frame) + "]")

		for sine in self.kurwes:
			sine.update(0.16, self.speed)

		if realtive_frame > 40:
			self.ground.center_y = min(102.0, self.ground.center_y + 3)
			if realtive_frame > 70:
				self.tree.center_x = max(685.0, self.tree.center_x - 3)
				r = self.bkg_color.r
				#print(r, end=' ')
				if realtive_frame % 3 == 0:
					r = min(200, r + 3)

				r_hex = f"{r:02x}"
				#print(r_hex)
				self.bkg_color = Color.from_hex_string(r_hex + "0000")

				if realtive_frame == 130:
					self.speed = -self.speed

				elif realtive_frame > 150:
					self.speed += 1
					self.grandpa.center_y = min(330.0, self.grandpa.center_y + 3)
					self.left_flying_kick.sprite.center_x -= 33

				if self.grandpa.center_y == 330:
					self.grandpa_speech.play()

	def on_draw(self, frame):
		relative_frame = frame - Stage12.START_FRAME

		diskette_show_base = 97
		if (diskette_show_base < relative_frame < diskette_show_base+15
			or diskette_show_base + 20 < relative_frame < diskette_show_base + 35
			or diskette_show_base + 40 < relative_frame < diskette_show_base + 60):
			self.draw_diskette()
		else:
			self.standard_draw(frame)

		if self.grandpa.center_y == 330:
			self.grandpa_speech.draw(relative_frame)

		if relative_frame > 520:
			self.fullscreen()
			rect = self.create_bkg_rect()
			frames_since_521 = relative_frame - 520
			even_frames_passed = frames_since_521*3.6
			transparency = min(255, even_frames_passed)

			color = (0, 0, 0, transparency)
			arcade.draw_rect_filled(rect, color=color)
			self.draw_cover_arcade_color(color)


	def draw_diskette(self):
		super().clear_screen(BLACK)
		arcade.draw_sprite(self.diskette)

	def standard_draw(self, frame):
		super().clear_screen(self.bkg_color)
		relative_frame = frame - Stage12.START_FRAME

		for sine in self.kurwes:
			sine.draw(
				surface_width=Constants.WIDTH * 2,
				surface_height=Constants.HEIGHT * 2 - 0 * 200,
				amplitude=self.amplitude,
				frequency=self.frequency,
				horizon_x=self.horizon_x
			)
		self.blink_write(0.9*Constants.HEIGHT - 4*12, "READY.", start_frame=Stage12.START_FRAME, frame=frame)
		self.blink_cursor(frame, color=WHITE)

		for sprite in (self.grandpa, self.ground, self.tree):
			arcade.draw_sprite(sprite)

		if relative_frame > 150:
			arcade.draw_sprite(self.tori)
			arcade.draw_sprite(self.left_flying_kick.sprite)

		if relative_frame > 150:
			self.speed += 1
			# print(len(self.balls))
			for ball in self.balls:
				ball.move()
				ball.draw()
				# print(ball.x, ball.y, end=' | ')
				# print()




class Ball:

	COUNT = 0
	GROUND_ZERO = 0.1 * Constants.HEIGHT
	SIZE = 15

	def __init__(self):
		Ball.COUNT += 1

		colors = (Constants.BLACK, Constants.CYAN, Constants.WHITE, Constants.YELLOW, Constants.GREEN, Constants.LIGHT_BLUE)
		self.color = Color.from_hex_string(colors[Ball.COUNT % len(colors)])

		self.x = - 10 * Ball.COUNT * Ball.SIZE
		self.y = Ball.GROUND_ZERO

		self.speed = 11 + (Ball.COUNT % 3)*3

		self.magnitude = 30 + (15+5*Ball.COUNT)*math.sin(2*math.pi / Ball.COUNT)

	def move(self):
		self.y = Ball.GROUND_ZERO + self.magnitude * abs(math.sin(self.x * 3.141 / (Constants.HEIGHT // 2)))
		self.x += self.speed

		if self.x > 1.2 * Constants.WIDTH:
			self.x = - Ball.COUNT * Ball.SIZE

	def draw(self):
		arcade.draw_circle_filled(self.x, self.y, Ball.SIZE, self.color)


class GameListSpeech:

	def __init__(self, screen_width, screen_height):
		self.screen_width = screen_width
		self.scroll_position = screen_height + 40
		self.speech = arcade.load_sound(Constants.RES_PATH + "/ik/ka-games/published-games.mp3")
		self.spoken = False

		self.magnitude = 65.5

		y = 290
		self.gravity_duck = Sprite(Constants.RES_PATH + "/ik/ka-games/gravity-duck.png", center_x=Constants.WIDTH * 0.25, center_y=y)
		self.fizz = Sprite(Constants.RES_PATH + "/ik/ka-games/fizz.png", center_x=Constants.WIDTH * 0.25, center_y=y)
		self.rise = Sprite(Constants.RES_PATH + "/ik/ka-games/riseofbab.png", center_x=Constants.WIDTH * 0.25, center_y=y)
		self.flood = Sprite(Constants.RES_PATH + "/ik/ka-games/deathflood.png", center_x=Constants.WIDTH * 0.25, center_y=y)
		self.farm = Sprite(Constants.RES_PATH + "/ik/ka-games/farmiga.png", center_x=Constants.WIDTH * 0.25, center_y=y)
		self.santa = Sprite(Constants.RES_PATH + "/ik/ka-games/santastic.png", center_x=Constants.WIDTH * 0.25, center_y=y)

		for spr in (self.gravity_duck, self.fizz, self.rise, self.flood, self.farm, self.santa):
			spr.scale = (0.15, 0.15)

	def play(self):
		if not self.spoken:
			self.speech.play()
			self.spoken = True
			print("KOMODA AND AMIGA PLUS ALSO RELEASED A COUPLE GAMES: GRAVITY DUCK, FIZZ,RISE OF BABYLON"
		      ", DEATH FLOOD, FARMIGA AND SANTASTIC.")

	def draw(self, frame):
		#print(frame)

		games_list = "GRAVITY DUCK     FIZZ    RISE OF BABYLON     DEATH FLOOD     FARMIGA      SANTASTIC"

		if frame > 380:
			arcade.draw_sprite(self.gravity_duck)
			games = Text(games_list, self.screen_width + 13*(380 - frame), 20, font_size=12, font_name="C64 Pro Mono")
			games.draw()
		if frame > 400:
			arcade.draw_sprite(self.fizz)
			self.move(self.gravity_duck)
		if frame > 430:
			arcade.draw_sprite(self.rise)
			self.move(self.fizz)
		if frame > 453:
			arcade.draw_sprite(self.flood)
			self.move(self.rise)
		if frame > 468:
			arcade.draw_sprite(self.farm)
			self.move(self.flood)
		if frame > 468 + 9:
			arcade.draw_sprite(self.santa)
			self.move(self.farm)
		if frame > 468 + 18:
			self.move(self.santa)

	def move(self, sprite: Sprite):
		sprite.center_x += 22.75
		y = sprite.center_y - 0.6*math.log2(sprite.center_x)
		sprite.center_y = max(y, Ball.GROUND_ZERO + self.magnitude)
