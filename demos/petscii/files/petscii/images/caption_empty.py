from lib.petscii_image import PetsciiImage


class CaptionEmpty(PetsciiImage):

    chars = (
        tuple(tuple(32 for _ in range(40)) for _ in range(10))
    )

    reversed = (
        tuple(tuple(0 for _ in range(40)) for _ in range(10))
    )

    colors = (
        tuple(tuple(0 for _ in range(40)) for _ in range(10))
    )
