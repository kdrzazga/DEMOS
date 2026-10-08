"""Komoda issue 1 - the 16-page Polish games magazine in resources/Komoda_01.pdf.

The pages are rendered from the PDF to JPEGs once into
magazine/resources/komoda_01/page_01.jpg ... page_16.jpg (see PdfMagazine).
Running this module converts (or re-converts) them:

    python -m demos.c64.magazine.komoda_01
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from demos.c64.magazine.magazine import C64_RESOURCES, MAGAZINE_RESOURCES, PdfMagazine


class Komoda_01(PdfMagazine):

	def __init__(self, pdf_path=os.path.join(C64_RESOURCES, "Komoda_01.pdf"),
	             pages_dir=os.path.join(MAGAZINE_RESOURCES, "komoda_01"), page_count=16, **magazine_options):
		super().__init__(pdf_path, pages_dir, page_count, **magazine_options)


if __name__ == "__main__":
	magazine = Komoda_01()
	print(f"{magazine.convert()} pages written to {magazine.pages_dir}")
