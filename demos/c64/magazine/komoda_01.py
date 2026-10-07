"""Komoda issue 1 - the 16-page Polish games magazine in resources/Komoda_01.pdf.

The pages are rendered from the PDF to JPEGs once, by convert_pdf_pages(), into
magazine/resources/komoda_01/page_01.jpg ... page_16.jpg; the model only loads
those pictures, so PyMuPDF is needed just for that conversion. Running this
module converts (or re-converts) them:

    python -m demos.c64.magazine.komoda_01
"""

import os
import sys

import pygame

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from demos.c64.magazine.magazine import Magazine

C64_RESOURCES = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "resources")
MAGAZINE_RESOURCES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources")


def page_file_name(number):
	return f"page_{number:02d}.jpg"


def convert_pdf_pages(pdf_path, pages_dir, render_width=1024, jpeg_quality=90):
	"""Render every PDF page to pages_dir/page_NN.jpg, render_width pixels wide.
	Returns the number of pages written."""
	import pymupdf

	os.makedirs(pages_dir, exist_ok=True)
	with pymupdf.open(pdf_path) as document:
		for index, page in enumerate(document):
			zoom = render_width / page.rect.width
			pixmap = page.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom), alpha=False)
			pixmap.save(os.path.join(pages_dir, page_file_name(index + 1)), jpg_quality=jpeg_quality)
		return document.page_count


class Komoda_01(Magazine):

	def __init__(self, pdf_path=os.path.join(C64_RESOURCES, "Komoda_01.pdf"),
	             pages_dir=os.path.join(MAGAZINE_RESOURCES, "komoda_01"), page_count=16, **magazine_options):
		super().__init__(page_count, **magazine_options)
		self.pdf_path = pdf_path
		self.pages_dir = pages_dir

	def page_paths(self):
		return [os.path.join(self.pages_dir, page_file_name(number)) for number in range(1, self.page_count + 1)]

	def ensure_pages(self):
		"""Convert the PDF if any page picture is missing."""
		if not all(os.path.exists(path) for path in self.page_paths()):
			convert_pdf_pages(self.pdf_path, self.pages_dir)

	def page_surfaces(self):
		self.ensure_pages()
		return [pygame.image.load(path) for path in self.page_paths()]


if __name__ == "__main__":
	magazine = Komoda_01()
	written = convert_pdf_pages(magazine.pdf_path, magazine.pages_dir)
	print(f"{written} pages written to {magazine.pages_dir}")
