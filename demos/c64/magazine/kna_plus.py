"""K&A Plus issue 1 (English edition) - the 72-page magazine in resources/K&A_Plus_01_EN.pdf.

The pages are rendered from the PDF to JPEGs once into
magazine/resources/kna_plus_01/page_01.jpg ... page_72.jpg (see PdfMagazine).
Running this module converts (or re-converts) them:

    python -m demos.c64.magazine.kna_plus
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from demos.c64.magazine.magazine import C64_RESOURCES, MAGAZINE_RESOURCES, PdfMagazine


class KnA_Plus(PdfMagazine):

	def __init__(self, pdf_path=os.path.join(C64_RESOURCES, "K&A_Plus_01_EN.pdf"),
	             pages_dir=os.path.join(MAGAZINE_RESOURCES, "kna_plus_01"), page_count=72, sheet_gap=0.012,
	             **magazine_options):
		super().__init__(pdf_path, pages_dir, page_count, sheet_gap=sheet_gap, **magazine_options)


if __name__ == "__main__":
	magazine = KnA_Plus()
	print(f"{magazine.convert()} pages written to {magazine.pages_dir}")
