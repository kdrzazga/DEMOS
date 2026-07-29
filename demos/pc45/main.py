"""IBM PC 45th-anniversary demo - pygame + OpenGL front-end.

Run from the DEMOS project root so the relative resource paths resolve:

    python -m demos.pc45.main

The 2D DOS boot animation is painted onto an offscreen pygame Surface
(see boot_surface.BootScreen) and mapped onto the CRT rectangle of a photo of a
real IBM PC (ibmpc.png). The camera starts zoomed into just that screen - so it
looks like a plain 2D boot animation, the machine off-frame - then, two seconds
after the "Version 1.00 ..." banner, zooms and pans out to reveal the whole PC.
ESC / window-close quits.
"""

import math
import os

import pygame
from pygame.locals import DOUBLEBUF, OPENGL, QUIT, KEYDOWN, K_ESCAPE
from OpenGL.GL import (
	glGenTextures, glBindTexture, glTexParameteri, glTexImage2D, glEnable,
	glBlendFunc, glClearColor, glClear, glLoadIdentity, glMatrixMode,
	glTranslatef, glRotatef, glColor3f, glBegin, glEnd, glTexCoord2f, glVertex3f,
	GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_TEXTURE_MAG_FILTER, GL_LINEAR,
	GL_TEXTURE_WRAP_S, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE, GL_RGBA,
	GL_UNSIGNED_BYTE, GL_COLOR_BUFFER_BIT, GL_PROJECTION, GL_MODELVIEW,
	GL_QUADS, GL_BLEND, GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA,
)
from OpenGL.GLU import gluPerspective

try:
	from boot_surface import BootScreen              # when launched as a script from this folder
except ModuleNotFoundError:
	from demos.pc45.boot_surface import BootScreen   # when launched as a package from the root

# resolve resources against the project root (DEMOS/) so the demo runs no matter
# what the working directory is or how it is launched
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class GlDemo:
	"""Boot screen mapped onto a photo of an IBM PC, revealed by a zoom-out."""

	WIN_W, WIN_H = 1280, 800
	RES_PATH = os.path.join(_ROOT, "demos", "pc45", "resources")

	FOV = 45.0                             # vertical field of view (degrees)
	PC_IMAGE = "ibmpc.png"
	# the CRT's black rectangle inside ibmpc.png: (left, top, right, bottom) in px
	SCREEN_RECT = (474, 118, 963, 428)

	# The view starts framed on just the screen (machine off-frame), then over
	# PULLBACK_FRAMES zooms + pans out to frame the whole photo.
	PULLBACK_FRAMES = 300                  # 5 s at 60 fps
	COVER_OVERSCAN = 0.99                  # <1 zooms in a hair so no bezel peeks at the start
	VOLUME_DECAY = 0.99                    # multiply music volume by this each frame while zooming out

	# a few degrees of gentle sway that eases in as the zoom-out begins and then
	# keeps going for the rest of the demo
	SWAY_YAW = 9.0                         # degrees, horizontal
	SWAY_PITCH = 1.5                       # degrees, vertical
	SWAY_SPEED = 0.6                       # sine rate (per second); ~10 s period

	DATE_ZOOM_FRAMES = 120
	YEAR_STEP_FRAMES = 8
	CAPTION_HALF_HEIGHT = 0.28
	YEARS = list(range(81, 100)) + list(range(0, 27))

	def __init__(self):
		pygame.init()
		pygame.mixer.init()
		pygame.display.set_mode((self.WIN_W, self.WIN_H), DOUBLEBUF | OPENGL)
		pygame.display.set_caption("IBM PC 45 - MDA boot (pygame / OpenGL)")

		self._init_gl()
		self.boot = BootScreen()
		self.tex = self._make_texture()            # dynamic: the boot screen
		self.pc_tex = self._load_pc_texture()      # static: the IBM PC photo
		self.caption_tex = self._make_texture()
		self._setup_geometry()
		self._start_audio()

		self.clock = pygame.time.Clock()
		self.frame = 0
		self.running = False

	# --- setup -------------------------------------------------------------
	def _init_gl(self):
		glEnable(GL_TEXTURE_2D)
		glEnable(GL_BLEND)
		glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)   # honour the photo's transparency
		glClearColor(0.0, 0.0, 0.0, 1.0)
		glMatrixMode(GL_PROJECTION)
		gluPerspective(self.FOV, self.WIN_W / self.WIN_H, 0.1, 100.0)
		glMatrixMode(GL_MODELVIEW)

	def _make_texture(self):
		tex = glGenTextures(1)
		glBindTexture(GL_TEXTURE_2D, tex)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
		return tex

	def _load_pc_texture(self):
		surface = pygame.image.load(os.path.join(self.RES_PATH, self.PC_IMAGE))
		self.pc_w, self.pc_h = surface.get_size()
		data = pygame.image.tostring(surface, "RGBA", True)
		tex = self._make_texture()
		glBindTexture(GL_TEXTURE_2D, tex)
		glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, self.pc_w, self.pc_h, 0,
		             GL_RGBA, GL_UNSIGNED_BYTE, data)
		return tex

	def _setup_geometry(self):
		# Map photo pixels to world space: the whole photo is a quad centred on the
		# origin, half-height 1, half-width = photo aspect. y is flipped (image is
		# top-down, world is y-up).
		aspect = self.pc_w / self.pc_h
		self.pc_hw, self.pc_hh = aspect, 1.0

		def wx(px):
			return (px / self.pc_w - 0.5) * 2.0 * aspect

		def wy(py):
			return (0.5 - py / self.pc_h) * 2.0

		left, top, right, bottom = self.SCREEN_RECT
		self.scr_l, self.scr_r = wx(left), wx(right)
		self.scr_t, self.scr_b = wy(top), wy(bottom)

		screen_cx = (self.scr_l + self.scr_r) / 2.0
		screen_cy = (self.scr_t + self.scr_b) / 2.0
		screen_hw = (self.scr_r - self.scr_l) / 2.0
		screen_hh = (self.scr_t - self.scr_b) / 2.0
		win_aspect = self.WIN_W / self.WIN_H

		# view at t=0: cover the screen rect (fills viewport, machine off-frame)
		self.view_c0 = (screen_cx, screen_cy)
		self.vh0 = min(screen_hh, screen_hw / win_aspect) * self.COVER_OVERSCAN
		# view at t=1: contain the whole photo, centred
		self.view_c1 = (0.0, 0.0)
		self.vh1 = max(self.pc_hh, self.pc_hw / win_aspect)

		# begin the pull-back 2 s after the "Version 1.00 ..." banner (BANNER2) shows
		self.pullback_start = self.boot.BOOT_START + self.boot.D_BANNER2 + 2 * self.boot.FPS
		self.date_zoom_start = self.pullback_start + self.PULLBACK_FRAMES
		self.year_start = self.date_zoom_start + self.DATE_ZOOM_FRAMES

		date_x, date_y, date_w, date_h = self.boot.date_pixel_rect()

		def bx(px):
			return self.scr_l + (px / self.boot.WIDTH) * (self.scr_r - self.scr_l)

		def by(py):
			return self.scr_t + (py / self.boot.HEIGHT) * (self.scr_b - self.scr_t)

		self.date_rect0 = (bx(date_x), bx(date_x + date_w), by(date_y + date_h), by(date_y))
		aspect0 = (self.date_rect0[1] - self.date_rect0[0]) / (self.date_rect0[3] - self.date_rect0[2])
		cap_hw = self.CAPTION_HALF_HEIGHT * aspect0
		self.date_rect1 = (-cap_hw, cap_hw, -self.CAPTION_HALF_HEIGHT, self.CAPTION_HALF_HEIGHT)

	def _start_audio(self):
		self.volume = 1.0
		try:
			pygame.mixer.music.load(os.path.join(self.RES_PATH, "pc-boot.mp3"))
			pygame.mixer.music.set_volume(self.volume)
			pygame.mixer.music.play()
		except pygame.error as exc:
			print("audio unavailable:", exc)

	# --- per-frame ---------------------------------------------------------
	def _process_events(self):
		for event in pygame.event.get():
			if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
				self.running = False

	def _upload_boot_texture(self):
		surface = self.boot.render(self.frame)
		w, h = surface.get_size()
		# flip vertically so the Surface's top row maps to the top of the quad
		data = pygame.image.tostring(surface, "RGBA", True)
		glBindTexture(GL_TEXTURE_2D, self.tex)
		glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, w, h, 0, GL_RGBA, GL_UNSIGNED_BYTE, data)

	def _update_audio(self):
		"""Once the zoom-out starts, fade the mp3 by 1% of its current level each frame."""
		if self.frame >= self.pullback_start:
			self.volume *= self.VOLUME_DECAY
			pygame.mixer.music.set_volume(self.volume)

	def _update_boot(self):
		self.boot.date_on_screen = self.frame < self.date_zoom_start
		if self.frame >= self.year_start:
			i = min(len(self.YEARS) - 1, (self.frame - self.year_start) // self.YEAR_STEP_FRAMES)
			self.boot.year = self.YEARS[i]

	def _camera(self):
		"""Interpolate the view from the screen sub-rect (t=0) to the whole photo (t=1)."""
		if self.frame <= self.pullback_start:
			t = 0.0
		else:
			t = min(1.0, (self.frame - self.pullback_start) / self.PULLBACK_FRAMES)
		cx = self.view_c0[0] + (self.view_c1[0] - self.view_c0[0]) * t
		cy = self.view_c0[1] + (self.view_c1[1] - self.view_c0[1]) * t
		vh = self.vh0 + (self.vh1 - self.vh0) * t
		dist = vh / math.tan(math.radians(self.FOV / 2.0))
		return cx, cy, dist

	def _sway(self):
		"""A few degrees of gentle sway, growing from zero once the zoom-out begins
		and continuing after it settles."""
		if self.frame < self.pullback_start:
			return 0.0, 0.0
		st = (self.frame - self.pullback_start) / self.boot.FPS
		yaw = self.SWAY_YAW * math.sin(st * self.SWAY_SPEED)
		pitch = self.SWAY_PITCH * math.sin(st * self.SWAY_SPEED * 0.7)
		return yaw, pitch

	@staticmethod
	def _draw_quad_rect(left, right, bottom, top):
		glBegin(GL_QUADS)
		glTexCoord2f(0.0, 0.0); glVertex3f(left, bottom, 0.0)
		glTexCoord2f(1.0, 0.0); glVertex3f(right, bottom, 0.0)
		glTexCoord2f(1.0, 1.0); glVertex3f(right, top, 0.0)
		glTexCoord2f(0.0, 1.0); glVertex3f(left, top, 0.0)
		glEnd()

	def _draw_frame(self):
		glClear(GL_COLOR_BUFFER_BIT)
		glLoadIdentity()
		cx, cy, dist = self._camera()
		yaw, pitch = self._sway()
		# pull back, then sway about the framed centre (cx, cy)
		glTranslatef(0.0, 0.0, -dist)
		glRotatef(yaw, 0.0, 1.0, 0.0)
		glRotatef(pitch, 1.0, 0.0, 0.0)
		glTranslatef(-cx, -cy, 0.0)
		glColor3f(1.0, 1.0, 1.0)
		# the IBM PC photo ...
		glBindTexture(GL_TEXTURE_2D, self.pc_tex)
		self._draw_quad_rect(-self.pc_hw, self.pc_hw, -self.pc_hh, self.pc_hh)
		# ... with the live boot screen laid over its CRT rectangle
		glBindTexture(GL_TEXTURE_2D, self.tex)
		self._draw_quad_rect(self.scr_l, self.scr_r, self.scr_b, self.scr_t)
		self._draw_caption()

	def _draw_caption(self):
		if self.frame < self.date_zoom_start:
			return
		surface = self.boot.render_date_caption()
		w, h = surface.get_size()
		data = pygame.image.tostring(surface, "RGBA", True)
		glBindTexture(GL_TEXTURE_2D, self.caption_tex)
		glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, w, h, 0, GL_RGBA, GL_UNSIGNED_BYTE, data)
		dz = min(1.0, (self.frame - self.date_zoom_start) / self.DATE_ZOOM_FRAMES)
		l0, r0, b0, t0 = self.date_rect0
		l1, r1, b1, t1 = self.date_rect1
		left = l0 + (l1 - l0) * dz
		right = r0 + (r1 - r0) * dz
		bottom = b0 + (b1 - b0) * dz
		top = t0 + (t1 - t0) * dz
		self._draw_quad_rect(left, right, bottom, top)

	# --- main loop ---------------------------------------------------------
	def run(self):
		self.running = True
		while self.running:
			self._process_events()
			self._update_audio()
			self._update_boot()
			self._upload_boot_texture()
			self._draw_frame()
			pygame.display.flip()
			self.clock.tick(self.boot.FPS)
			self.frame += 1
		pygame.quit()


if __name__ == "__main__":
	GlDemo().run()
