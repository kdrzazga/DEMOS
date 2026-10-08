"""3D model of a stapled magazine whose sheets turn like paper.

Local frame (centimetres): x to the right, y up, z toward the user; the
magazine lies flat on y = 0 with its spine along the z axis at x = 0, the page
tops at -z. Closed, every sheet lies on the right (x > 0) with the cover on
top; turning a sheet swings it over the spine onto the left stack.

page_count pages are printed on page_count / 2 sheets: sheet i carries page
2i + 1 on its front (a right-hand page) and page 2i + 2 on its back (the
left-hand page once it is turned). A sheet is drawn as a strip of columns
hinged at the spine; while it turns, the angle along the strip grows from the
spine angle to the free-edge angle, so the paper bends in an arc, the free edge
leading as if it were lifted by a finger.

Pages are pygame surfaces from page_surfaces(); this class paints plain
numbered pages, a subclass supplies the real ones.
"""

import math
import os

import pygame
from OpenGL.GL import *

from demos.c64.geometry import upload_texture

C64_RESOURCES = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "resources")
MAGAZINE_RESOURCES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources")


def smoothstep(value):
	value = max(0.0, min(1.0, value))
	return value * value * (3.0 - 2.0 * value)


def page_file_name(number):
	return f"page_{number:02d}.jpg"


def convert_pdf_pages(pdf_path, pages_dir, render_width=1024, jpeg_quality=90):
	import pymupdf

	os.makedirs(pages_dir, exist_ok=True)
	with pymupdf.open(pdf_path) as document:
		for index, page in enumerate(document):
			zoom = render_width / page.rect.width
			pixmap = page.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom), alpha=False)
			pixmap.save(os.path.join(pages_dir, page_file_name(index + 1)), jpg_quality=jpeg_quality)
		return document.page_count


class Magazine:

	def __init__(self, page_count, page_width=21.0, page_height=29.7, sheet_gap=0.03, turn_seconds=1.2,
	             turn_columns=32, edge_lead=0.7, paper_color=(246, 244, 236)):
		if page_count < 2 or page_count % 2:
			raise ValueError(f"page_count must be an even number of at least 2, got {page_count}")
		self.page_count = page_count
		self.sheet_count = page_count // 2
		self.page_width = page_width
		self.page_height = page_height
		self.sheet_gap = sheet_gap
		self.turn_seconds = turn_seconds
		self.turn_columns = turn_columns
		self.edge_lead = edge_lead
		self.paper_color = paper_color

		# per sheet: where it should end up (0 = right stack, 1 = left stack), how
		# far its spine has turned and how far its free edge has (both 0..1)
		self._targets = [0] * self.sheet_count
		self._spine_progress = [0.0] * self.sheet_count
		self._edge_progress = [0.0] * self.sheet_count
		self._front_textures = []
		self._back_textures = []

	@property
	def turned_count(self):
		"""Sheets turned, or on their way, onto the left stack."""
		return sum(self._targets)

	@property
	def turning(self):
		return any(progress != target for progress, target in zip(self._spine_progress, self._targets))

	def turn_page(self):
		"""Send the next sheet still bound for the right stack over to the left one -
		even while earlier sheets are in the air. Returns False at the back cover."""
		if self.turned_count == self.sheet_count:
			return False
		self._targets[self.turned_count] = 1
		return True

	def turn_back(self):
		"""Send the last sheet bound for the left stack back to the right one; a sheet
		still in the air just reverses. Returns False at the front cover."""
		if self.turned_count == 0:
			return False
		self._targets[self.turned_count - 1] = 0
		return True

	def update(self, seconds):
		"""Move every sheet toward its stack by `seconds` of animation. The free edge
		moves 1 / edge_lead times faster than the spine, so it leads either way."""
		spine_step = seconds / self.turn_seconds
		edge_step = spine_step / self.edge_lead
		for sheet, target in enumerate(self._targets):
			self._spine_progress[sheet] = self._approach(self._spine_progress[sheet], target, spine_step)
			self._edge_progress[sheet] = self._approach(self._edge_progress[sheet], target, edge_step)

	@staticmethod
	def _approach(value, target, step):
		return min(target, value + step) if value < target else max(target, value - step)

	def visible_pages(self):
		"""Page numbers (1-based) lying open on the left and right, None where there is no page."""
		left = 2 * self.turned_count if self.turned_count > 0 else None
		right = 2 * self.turned_count + 1 if self.turned_count < self.sheet_count else None
		return left, right

	def centre_x(self):
		"""x of the middle of what is showing: the cover alone (closed), an open
		spread, or the back cover alone - for a camera that keeps the magazine centred."""
		position = sum(smoothstep(progress) for progress in self._spine_progress)
		if position < 1.0:
			return self.page_width / 2 * (1.0 - position)
		last_spread = self.sheet_count - 1
		if position > last_spread:
			return -self.page_width / 2 * (position - last_spread)
		return 0.0

	def page_surfaces(self):
		"""One pygame surface per page, in reading order. Plain numbered paper here."""
		font = pygame.font.SysFont("arial", 160, bold=True)
		surfaces = []
		for number in range(1, self.page_count + 1):
			surface = pygame.Surface((512, int(512 * self.page_height / self.page_width)))
			surface.fill(self.paper_color)
			label = font.render(str(number), True, (60, 60, 60))
			surface.blit(label, label.get_rect(center=surface.get_rect().center))
			surfaces.append(surface)
		return surfaces

	def build(self):
		"""Upload the page textures. Needs a GL context."""
		textures = [upload_texture(surface) for surface in self.page_surfaces()]
		if len(textures) != self.page_count:
			glDeleteTextures(textures)
			raise ValueError(f"expected {self.page_count} page images, got {len(textures)}")
		self._front_textures = textures[0::2]
		self._back_textures = textures[1::2]

	def _right_stack_height(self, sheet):
		return (self.sheet_count - 1 - sheet) * self.sheet_gap

	def _left_stack_height(self, sheet):
		return sheet * self.sheet_gap

	def _strip(self, spine_height, spine_angle, edge_angle, columns):
		"""Points along the sheet from spine to free edge as (distance along the
		sheet, x, y, angle). The angle grows linearly along the sheet, so the
		strip is a circular arc (a straight line when the two angles match)."""
		width = self.page_width
		curvature = (edge_angle - spine_angle) / width
		points = []
		for column in range(columns + 1):
			along = width * column / columns
			angle = spine_angle + curvature * along
			if abs(curvature) < 1e-6:
				x, y = along * math.cos(spine_angle), along * math.sin(spine_angle)
			else:
				x = (math.sin(angle) - math.sin(spine_angle)) / curvature
				y = (math.cos(spine_angle) - math.cos(angle)) / curvature
			points.append((along, x, spine_height + y, angle))
		return points

	def _draw_sheet(self, sheet, points):
		"""Both sides of one sheet. Back faces are culled, so the front page shows
		from above while the sheet lies right and the back page once it is turned."""
		top_z, bottom_z = -self.page_height / 2, self.page_height / 2
		width = self.page_width
		glColor3ub(255, 255, 255)
		for texture, is_front in ((self._front_textures[sheet], True), (self._back_textures[sheet], False)):
			glBindTexture(GL_TEXTURE_2D, texture)
			glBegin(GL_QUADS)
			for (along0, x0, y0, angle0), (along1, x1, y1, angle1) in zip(points, points[1:]):
				# the front page's left edge is at the spine; the back page's right edge is
				corners = ((along0, x0, y0, angle0, top_z, 1.0), (along0, x0, y0, angle0, bottom_z, 0.0),
				           (along1, x1, y1, angle1, bottom_z, 0.0), (along1, x1, y1, angle1, top_z, 1.0))
				for along, x, y, angle, z, texture_t in (corners if is_front else corners[::-1]):
					side = 1.0 if is_front else -1.0
					glNormal3f(-math.sin(angle) * side, math.cos(angle) * side, 0.0)
					glTexCoord2f(along / width if is_front else 1.0 - along / width, texture_t)
					glVertex3f(x, y, z)
			glEnd()

	def draw(self):
		glPushAttrib(GL_ENABLE_BIT | GL_POLYGON_BIT | GL_CURRENT_BIT)
		glEnable(GL_CULL_FACE)
		glCullFace(GL_BACK)
		glFrontFace(GL_CCW)
		glEnable(GL_TEXTURE_2D)
		for sheet in range(self.sheet_count):
			spine_progress, edge_progress = self._spine_progress[sheet], self._edge_progress[sheet]
			right, left = self._right_stack_height(sheet), self._left_stack_height(sheet)
			spine_height = right + (left - right) * smoothstep(spine_progress)
			spine_angle, edge_angle = math.pi * smoothstep(spine_progress), math.pi * smoothstep(edge_progress)
			columns = 1 if spine_progress == edge_progress else self.turn_columns
			self._draw_sheet(sheet, self._strip(spine_height, spine_angle, edge_angle, columns))
		glPopAttrib()

	def destroy(self):
		textures = self._front_textures + self._back_textures
		if textures:
			glDeleteTextures(textures)
		self._front_textures = []
		self._back_textures = []


class PdfMagazine(Magazine):
	"""A magazine whose pages are rendered from a PDF into pages_dir/page_NN.jpg.
	The pictures are made once by convert(), or on build() if any is missing;
	after that only they are loaded, so PyMuPDF is needed just for converting."""

	def __init__(self, pdf_path, pages_dir, page_count, **magazine_options):
		super().__init__(page_count, **magazine_options)
		self.pdf_path = pdf_path
		self.pages_dir = pages_dir

	def page_paths(self):
		return [os.path.join(self.pages_dir, page_file_name(number)) for number in range(1, self.page_count + 1)]

	def convert(self):
		"""Render (or re-render) every PDF page; returns the number of pages written."""
		return convert_pdf_pages(self.pdf_path, self.pages_dir)

	def ensure_pages(self):
		"""Convert the PDF if any page picture is missing."""
		if not all(os.path.exists(path) for path in self.page_paths()):
			self.convert()

	def page_surfaces(self):
		self.ensure_pages()
		return [pygame.image.load(path) for path in self.page_paths()]
