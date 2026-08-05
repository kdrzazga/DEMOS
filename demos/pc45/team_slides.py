import os

import pygame
from OpenGL.GL import *

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TeamSlides:

	FONT = os.path.join(_ROOT, "lib", "resources", "Mx437_IBM_MDA.ttf")

	def __init__(self, res_path, win_w, win_h, seconds, screens):
		self.win_w = win_w
		self.win_h = win_h
		self.seconds = seconds
		self.text_color = (87, 255, 163)
		self.margin = 40
		self.top = 70
		self.font = pygame.font.Font(self.FONT, 22)
		self.line_h = int(self.font.get_linesize() * 1.1)
		self.photo_col = int(win_w * 0.25)
		self.text_x = self.photo_col + self.margin
		self.text_w = win_w - self.text_x - self.margin
		self.text_tex = self._new_texture()
		self.slides = []
		for photo, lines in screens:
			rows = []
			for line in lines:
				rows.extend(self._wrap(line))
			chars = sum(len(row) for row in rows)
			photo_tex = self._load_photo(res_path, photo) if photo else None
			self.slides.append((photo_tex, rows, chars))
		self.total_chars = max(1, sum(chars for _, _, chars in self.slides))

	def _new_texture(self):
		tex = glGenTextures(1)
		glBindTexture(GL_TEXTURE_2D, tex)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
		return tex

	def _wrap(self, text):
		if not text:
			return ['']
		rows = []
		current = ''
		for word in text.split(' '):
			trial = word if not current else current + ' ' + word
			if self.font.size(trial)[0] <= self.text_w:
				current = trial
			else:
				rows.append(current)
				current = word
		rows.append(current)
		return rows

	def _load_photo(self, res_path, photo):
		surface = pygame.image.load(os.path.join(res_path, photo))
		w, h = surface.get_size()
		tex = self._new_texture()
		glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, w, h, 0, GL_RGBA, GL_UNSIGNED_BYTE,
		             pygame.image.tostring(surface, "RGBA", True))
		return tex, w / h

	def _current(self, elapsed):
		revealed = int(min(1.0, max(0.0, elapsed) / self.seconds) * self.total_chars)
		acc = 0
		for idx, (photo_tex, rows, chars) in enumerate(self.slides):
			if revealed < acc + chars or idx == len(self.slides) - 1:
				return photo_tex, rows, revealed - acc
			acc += chars
		return None, [], 0

	def _text_surface(self, rows, local):
		imgs = []
		remaining = local
		for row in rows:
			if remaining <= 0:
				break
			if len(row) <= remaining:
				shown = row
				remaining -= len(row)
			else:
				shown = row[:remaining]
				remaining = 0
			imgs.append(self.font.render(shown, True, self.text_color) if shown else None)
		height = max(1, len(imgs) * self.line_h)
		surface = pygame.Surface((self.text_w, height), pygame.SRCALPHA)
		y = 0
		for img in imgs:
			if img is not None:
				surface.blit(img, (0, y))
			y += self.line_h
		return surface

	def _quad(self, x, y, w, h):
		glBegin(GL_QUADS)
		glTexCoord2f(0.0, 0.0); glVertex2f(x, y)
		glTexCoord2f(1.0, 0.0); glVertex2f(x + w, y)
		glTexCoord2f(1.0, 1.0); glVertex2f(x + w, y + h)
		glTexCoord2f(0.0, 1.0); glVertex2f(x, y + h)
		glEnd()

	def draw(self, elapsed):
		photo_tex, rows, local = self._current(elapsed)
		glDisable(GL_DEPTH_TEST)
		glEnable(GL_BLEND)
		glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
		glEnable(GL_TEXTURE_2D)
		glColor4f(1.0, 1.0, 1.0, 1.0)
		glMatrixMode(GL_PROJECTION)
		glPushMatrix()
		glLoadIdentity()
		glOrtho(0.0, self.win_w, 0.0, self.win_h, -1.0, 1.0)
		glMatrixMode(GL_MODELVIEW)
		glPushMatrix()
		glLoadIdentity()
		top_y = self.win_h - self.top
		if photo_tex is not None:
			tex, aspect = photo_tex
			pw = self.photo_col - 2 * self.margin
			ph = pw / aspect
			glBindTexture(GL_TEXTURE_2D, tex)
			self._quad(self.margin, top_y - ph, pw, ph)
		surface = self._text_surface(rows, local)
		tw, th = surface.get_size()
		glBindTexture(GL_TEXTURE_2D, self.text_tex)
		glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, tw, th, 0, GL_RGBA, GL_UNSIGNED_BYTE,
		             pygame.image.tostring(surface, "RGBA", True))
		self._quad(self.text_x, top_y - th, tw, th)
		glMatrixMode(GL_MODELVIEW)
		glPopMatrix()
		glMatrixMode(GL_PROJECTION)
		glPopMatrix()
		glMatrixMode(GL_MODELVIEW)
		glEnable(GL_DEPTH_TEST)
		glDisable(GL_BLEND)

	def destroy(self):
		glDeleteTextures([self.text_tex])
		for photo_tex, rows, chars in self.slides:
			if photo_tex is not None:
				glDeleteTextures([photo_tex[0]])
