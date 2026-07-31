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
import random

import pygame
from pygame.locals import DOUBLEBUF, OPENGL, QUIT, KEYDOWN, K_ESCAPE
from OpenGL.GL import (
	glGenTextures, glBindTexture, glTexParameteri, glTexImage2D, glEnable, glDisable,
	glDeleteTextures, glBlendFunc, glClearColor, glClear, glLoadIdentity, glMatrixMode,
	glPushMatrix, glPopMatrix, glTranslatef, glRotatef, glColor3f, glColor4f,
	glBegin, glEnd, glTexCoord2f, glVertex3f,
	GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_TEXTURE_MAG_FILTER, GL_LINEAR,
	GL_TEXTURE_WRAP_S, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE, GL_RGBA,
	GL_UNSIGNED_BYTE, GL_COLOR_BUFFER_BIT, GL_DEPTH_BUFFER_BIT, GL_DEPTH_TEST,
	GL_PROJECTION, GL_MODELVIEW, GL_QUADS, GL_BLEND, GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA,
)
from OpenGL.GLU import gluPerspective

try:
	from boot_surface import BootScreen              # when launched as a script from this folder
except ModuleNotFoundError:
	from demos.pc45.boot_surface import BootScreen   # when launched as a package from the root

try:
	from effects.fireworks import Firework
except ModuleNotFoundError:
	from demos.pc45.effects.fireworks import Firework

try:
	from effects.portrait import ExtrudedPhoto
except ModuleNotFoundError:
	from demos.pc45.effects.portrait import ExtrudedPhoto

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class AudioController:
	"""Plays the boot soundtrack, fades it during the zoom-out, and cues HB.mp3 once."""

	BOOT_TUNE = "pc-boot.mp3"
	HB_TUNE = "HB.mp3"
	DECAY = 0.99

	def __init__(self, res_path):
		self.res_path = res_path
		self.volume = 1.0
		self.hb_played = False

	def start(self):
		self.volume = 1.0
		self.hb_played = False
		try:
			pygame.mixer.music.load(os.path.join(self.res_path, self.BOOT_TUNE))
			pygame.mixer.music.set_volume(self.volume)
			pygame.mixer.music.play()
		except pygame.error as exc:
			print("audio unavailable:", exc)

	def update(self, fading, hb_cue):
		if self.hb_played:
			return
		if hb_cue:
			pygame.mixer.music.load(os.path.join(self.res_path, self.HB_TUNE))
			self.volume = 1.0
			pygame.mixer.music.set_volume(self.volume)
			pygame.mixer.music.play()
			self.hb_played = True
			return
		if fading:
			self.volume *= self.DECAY
			pygame.mixer.music.set_volume(self.volume)

	def fade_out(self, step):
		self.volume = max(0.0, self.volume - step)
		pygame.mixer.music.set_volume(self.volume)


class Camera:
	"""Interpolates the view from framed-on-the-screen to the whole photo, with a gentle sway."""

	SWAY_YAW = 9.0
	SWAY_PITCH = 1.5
	SWAY_SPEED = 0.6

	def __init__(self, fov, pullback_start, pullback_frames, fps):
		self.fov = fov
		self.pullback_start = pullback_start
		self.pullback_frames = pullback_frames
		self.fps = fps
		self.view0 = (0.0, 0.0, 1.0)
		self.view1 = (0.0, 0.0, 1.0)

	def set_views(self, c0, vh0, c1, vh1):
		self.view0 = (c0[0], c0[1], vh0)
		self.view1 = (c1[0], c1[1], vh1)

	def _pose(self, frame):
		if frame <= self.pullback_start:
			t = 0.0
		else:
			t = min(1.0, (frame - self.pullback_start) / self.pullback_frames)
		cx = self.view0[0] + (self.view1[0] - self.view0[0]) * t
		cy = self.view0[1] + (self.view1[1] - self.view0[1]) * t
		vh = self.view0[2] + (self.view1[2] - self.view0[2]) * t
		dist = vh / math.tan(math.radians(self.fov / 2.0))
		return cx, cy, dist

	def _sway(self, frame):
		if frame < self.pullback_start:
			return 0.0, 0.0
		st = (frame - self.pullback_start) / self.fps
		yaw = self.SWAY_YAW * math.sin(st * self.SWAY_SPEED)
		pitch = self.SWAY_PITCH * math.sin(st * self.SWAY_SPEED * 0.7)
		return yaw, pitch

	def apply(self, frame):
		cx, cy, dist = self._pose(frame)
		yaw, pitch = self._sway(frame)
		glLoadIdentity()
		glTranslatef(0.0, 0.0, -dist)
		glRotatef(yaw, 0.0, 1.0, 0.0)
		glRotatef(pitch, 1.0, 0.0, 0.0)
		glTranslatef(-cx, -cy, 0.0)


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

	DATE_ZOOM_FRAMES = 120
	YEAR_STEP_FRAMES = 6
	CAPTION_HALF_HEIGHT = 0.28
	YEARS = list(range(81, 100)) + list(range(0, 27))

	FIREWORK_BURSTS_PER_SECOND = [1, 2, 1, 2, 1, 1, 2, 1, 2]
	FIREWORK_COLORS = [
		(1.0, 0.5, 0.1),
		(1.0, 0.85, 0.2),
		(1.0, 0.2, 0.15),
		(1.0, 1.0, 1.0),
		(1.0, 0.65, 0.05),
		(1.0, 0.35, 0.1),
		(0.55, 1.0, 0.4),
		(0.35, 0.9, 1.0),
		(1.0, 0.75, 0.15),
		(1.0, 0.4, 0.2),
		(1.0, 0.95, 0.7),
		(0.7, 1.0, 0.5),
		(0.4, 0.8, 1.0),
	]
	TITLE_HALF_HEIGHT = 0.286
	TITLE_GAP = 0.07
	TITLE_MAX_HALF_WIDTH = 1.45

	DIM_FRAMES = 120
	PORTRAIT_IMAGE = "team/DonEstridge.png"
	PORTRAIT_DEPTH_PX = 10
	PORTRAIT_HALF_HEIGHT = 0.9
	PORTRAIT_CAM_Z = -3.0
	PORTRAIT_YAW = 24.0
	PORTRAIT_YAW_SPEED = 0.5

	def __init__(self):
		pygame.init()
		pygame.mixer.init()
		pygame.display.set_mode((self.WIN_W, self.WIN_H), DOUBLEBUF | OPENGL)
		pygame.display.set_caption("45 years of IBM-PC")

		self._init_gl()
		self.boot = BootScreen()
		self.tex = self._make_texture()            # dynamic: the boot screen
		self.pc_tex = self._load_pc_texture()      # static: the IBM PC photo
		self.caption_tex = self._make_texture()
		self.title_tex = self._make_texture()
		self._setup_geometry()
		self.camera = Camera(self.FOV, self.pullback_start, self.PULLBACK_FRAMES, self.boot.FPS)
		self.camera.set_views(self.view_c0, self.vh0, self.view_c1, self.vh1)
		self._build_fireworks()
		self.audio = AudioController(self.RES_PATH)
		self.audio.start()

		self.clock = pygame.time.Clock()
		self.frame = 0
		self.running = False
		self.scene = "anniversary"

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
		self.year_end = self.year_start + (len(self.YEARS) - 1) * self.YEAR_STEP_FRAMES

		date_x, date_y, date_w, date_h = self.boot.date_pixel_rect()

		def bx(px):
			return self.scr_l + (px / self.boot.WIDTH) * (self.scr_r - self.scr_l)

		def by(py):
			return self.scr_t + (py / self.boot.HEIGHT) * (self.scr_b - self.scr_t)

		self.date_rect0 = (bx(date_x), bx(date_x + date_w), by(date_y + date_h), by(date_y))
		aspect0 = (self.date_rect0[1] - self.date_rect0[0]) / (self.date_rect0[3] - self.date_rect0[2])
		cap_hw = self.CAPTION_HALF_HEIGHT * aspect0
		self.date_rect1 = (-cap_hw, cap_hw, -self.CAPTION_HALF_HEIGHT, self.CAPTION_HALF_HEIGHT)

		title_surface = self.boot.render_title()
		tw, th = title_surface.get_size()
		title_aspect = tw / th
		title_hh = self.TITLE_HALF_HEIGHT
		title_hw = title_hh * title_aspect
		if title_hw > self.TITLE_MAX_HALF_WIDTH:
			title_hw = self.TITLE_MAX_HALF_WIDTH
			title_hh = title_hw / title_aspect
		title_cy = self.CAPTION_HALF_HEIGHT + self.TITLE_GAP + title_hh
		self.title_rect = (-title_hw, title_hw, title_cy - title_hh, title_cy + title_hh)
		title_data = pygame.image.tostring(title_surface, "RGBA", True)
		glBindTexture(GL_TEXTURE_2D, self.title_tex)
		glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, tw, th, 0, GL_RGBA, GL_UNSIGNED_BYTE, title_data)

	def _build_fireworks(self):
		self.fireworks_start = self.year_end
		self._fw_active = []
		self._fw_pending = []
		i = 0
		for second, count in enumerate(self.FIREWORK_BURSTS_PER_SECOND):
			for _ in range(count):
				launch = second * self.boot.FPS + random.randint(0, self.boot.FPS - 1)
				x, y, z, angle = self._firework_placement(i % 2 == 0)
				self._fw_pending.append((launch, x, y, z, angle, self.FIREWORK_COLORS[i]))
				i += 1
		self._fw_pending.sort(key=lambda spec: spec[0])
		self.last_firework_launch = self.fireworks_start + self._fw_pending[-1][0]
		self.dim_start = self.last_firework_launch
		self.scene_switch = self.dim_start + self.DIM_FRAMES

	def _firework_placement(self, left):
		side = -1.0 if left else 1.0
		x = side * (self.pc_hw + random.uniform(0.1, 0.6))
		y = random.uniform(-0.3, 0.9)
		z = random.uniform(-1.2, -0.7)
		angle = random.uniform(150.0, 170.0)
		if not left:
			angle = 180.0 - angle
		return x, y, z, angle

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
		self.audio.update(self.frame >= self.pullback_start, self.frame >= self.year_start)
		if self.frame >= self.dim_start:
			self.audio.fade_out(1.0 / self.DIM_FRAMES)

	def _update_boot(self):
		self.boot.date_on_screen = self.frame < self.date_zoom_start
		if self.frame >= self.year_start:
			i = min(len(self.YEARS) - 1, (self.frame - self.year_start) // self.YEAR_STEP_FRAMES)
			self.boot.year = self.YEARS[i]

	def animate_fireworks(self):
		if self.frame < self.fireworks_start:
			return
		rel = self.frame - self.fireworks_start
		while self._fw_pending and self._fw_pending[0][0] <= rel:
			_, x, y, z, angle, color = self._fw_pending.pop(0)
			self._fw_active.append(Firework(x, y, z, angle_deg=angle, color=color))
		for fw in self._fw_active:
			fw.update()
			fw.draw()
		self._fw_active = [fw for fw in self._fw_active if not fw.done]

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
		self.camera.apply(self.frame)
		self.animate_fireworks()
		glColor3f(1.0, 1.0, 1.0)
		# the IBM PC photo ...
		glBindTexture(GL_TEXTURE_2D, self.pc_tex)
		self._draw_quad_rect(-self.pc_hw, self.pc_hw, -self.pc_hh, self.pc_hh)
		# ... with the live boot screen laid over its CRT rectangle
		glBindTexture(GL_TEXTURE_2D, self.tex)
		self._draw_quad_rect(self.scr_l, self.scr_r, self.scr_b, self.scr_t)
		self._draw_caption()
		self._dim()
		self._draw_title()

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

	def _draw_title(self):
		if self.frame < self.year_end:
			return
		glColor3f(1.0, 1.0, 1.0)
		glBindTexture(GL_TEXTURE_2D, self.title_tex)
		self._draw_quad_rect(*self.title_rect)

	def _dim(self):
		if self.frame < self.dim_start:
			return
		alpha = min(1.0, (self.frame - self.dim_start) / self.DIM_FRAMES)
		glMatrixMode(GL_PROJECTION)
		glPushMatrix()
		glLoadIdentity()
		glMatrixMode(GL_MODELVIEW)
		glPushMatrix()
		glLoadIdentity()
		glDisable(GL_TEXTURE_2D)
		glColor4f(0.0, 0.0, 0.0, alpha)
		glBegin(GL_QUADS)
		glVertex3f(-1.0, -1.0, 0.0)
		glVertex3f(1.0, -1.0, 0.0)
		glVertex3f(1.0, 1.0, 0.0)
		glVertex3f(-1.0, 1.0, 0.0)
		glEnd()
		glEnable(GL_TEXTURE_2D)
		glPopMatrix()
		glMatrixMode(GL_PROJECTION)
		glPopMatrix()
		glMatrixMode(GL_MODELVIEW)

	def _enter_portrait(self):
		try:
			glDeleteTextures([self.pc_tex, self.tex, self.caption_tex, self.title_tex])
		except Exception:
			pass
		self._fw_active = []
		self._fw_pending = []
		pygame.mixer.music.stop()
		glDisable(GL_BLEND)
		glEnable(GL_DEPTH_TEST)
		self.portrait = ExtrudedPhoto(os.path.join(self.RES_PATH, self.PORTRAIT_IMAGE),
		                              self.PORTRAIT_HALF_HEIGHT, self.PORTRAIT_DEPTH_PX)
		self.portrait_frame = 0
		self.scene = "portrait"

	def _draw_portrait(self):
		glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
		glLoadIdentity()
		glTranslatef(0.0, 0.0, self.PORTRAIT_CAM_Z)
		angle = self.PORTRAIT_YAW * math.sin(self.portrait_frame / self.boot.FPS * self.PORTRAIT_YAW_SPEED)
		glRotatef(angle, 0.0, 1.0, 0.0)
		self.portrait.draw()
		self.portrait_frame += 1

	# --- main loop ---------------------------------------------------------
	def run(self):
		self.running = True
		while self.running:
			self._process_events()
			if self.scene == "anniversary":
				self._update_audio()
				self._update_boot()
				self._upload_boot_texture()
				self._draw_frame()
				if self.frame >= self.scene_switch:
					self._enter_portrait()
			else:
				self._draw_portrait()
			pygame.display.flip()
			self.clock.tick(self.boot.FPS)
			self.frame += 1
		pygame.quit()


if __name__ == "__main__":
	GlDemo().run()
