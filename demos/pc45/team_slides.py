import os

import pygame
from OpenGL.GL import *

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TeamSlides:

	FONT = os.path.join(_ROOT, "lib", "resources", "Mx437_IBM_MDA.ttf")

	def __init__(self, res_path, win_w, win_h, seconds, screens, travel_image=None, travel_slides=()):
		self.win_w = win_w
		self.win_h = win_h
		self.seconds = seconds
		self.text_color = (87, 255, 163)
		self.header_color = (255, 255, 255)
		self.margin = 40
		self.top = 70
		self.font = pygame.font.Font(self.FONT, 22)
		self.line_h = int(self.font.get_linesize() * 1.1)
		self.photo_col = int(win_w * 0.25)
		self.text_x = self.photo_col + self.margin
		self.text_w = win_w - self.text_x - self.margin
		self.text_tex = self._new_texture()
		self.slides = []
		for photo, lines, hold in screens:
			rows = []
			header_done = False
			for line in lines:
				wrapped = self._wrap(line)
				if wrapped == ['']:
					continue
				if rows:
					rows.append(('', False))
				for row in wrapped:
					rows.append((row, not header_done))
				header_done = True
			chars = sum(len(text) for text, _ in rows)
			photo_tex = self._load_photo(res_path, photo) if photo else None
			self.slides.append([photo_tex, rows, chars, 0.0, 0.0, hold])
		self.total_chars = max(1, sum(slide[2] for slide in self.slides))
		typing_seconds = max(1.0, seconds - sum(slide[5] for slide in self.slides))
		self.typing_rate = self.total_chars / typing_seconds
		start = 0.0
		for slide in self.slides:
			slide[3] = slide[2] / self.typing_rate
			slide[4] = start
			start += slide[3] + slide[5]
		self.travel_slides = travel_slides
		self.isa_tex = None
		if travel_image:
			tex, aspect = self._load_photo(res_path, travel_image)
			self.isa_tex = tex
			self.isa_h = int(win_h * 0.22)
			self.isa_w = int(self.isa_h * aspect)
			self.isa_bottom = win_h // 2 - self.isa_h

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
		elapsed = max(0.0, elapsed)
		for photo_tex, rows, chars, type_dur, start, hold in self.slides:
			if elapsed < start + type_dur + hold:
				local_t = elapsed - start
				if local_t < type_dur:
					return photo_tex, rows, min(chars, int(local_t * self.typing_rate))
				return photo_tex, rows, chars
		last = self.slides[-1]
		return last[0], last[1], last[2]

	def _isa_x(self, elapsed):
		n = len(self.travel_slides)
		for order, idx in enumerate(self.travel_slides):
			start = self.slides[idx][4]
			end = start + self.slides[idx][3] + self.slides[idx][5]
			if start <= elapsed < end:
				local = (elapsed - start) / (end - start) if end > start else 1.0
				return (order + local) / n * self.win_w
		return None

	def _text_surface(self, rows, local):
		imgs = []
		remaining = local
		for text, is_header in rows:
			if remaining <= 0:
				break
			if len(text) <= remaining:
				shown = text
				remaining -= len(text)
			else:
				shown = text[:remaining]
				remaining = 0
			color = self.header_color if is_header else self.text_color
			imgs.append(self.font.render(shown, True, color) if shown else None)
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
		if self.isa_tex is not None:
			x = self._isa_x(elapsed)
			if x is not None:
				glBindTexture(GL_TEXTURE_2D, self.isa_tex)
				self._quad(x, self.isa_bottom, self.isa_w, self.isa_h)
		glMatrixMode(GL_MODELVIEW)
		glPopMatrix()
		glMatrixMode(GL_PROJECTION)
		glPopMatrix()
		glMatrixMode(GL_MODELVIEW)
		glEnable(GL_DEPTH_TEST)
		glDisable(GL_BLEND)

	def destroy(self):
		glDeleteTextures([self.text_tex])
		for slide in self.slides:
			if slide[0] is not None:
				glDeleteTextures([slide[0][0]])
		if self.isa_tex is not None:
			glDeleteTextures([self.isa_tex])
