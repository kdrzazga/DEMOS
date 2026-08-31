from lib.petscii_image import PetsciiImage


class Cequals(PetsciiImage):

    chars = (
        (169, 160, 160, 32),
        (160, 32, 163, 169),
        (160, 32, 163, 127),
        (127, 163, 163, 32),
    )

    reversed = (
        (1, 1, 1, 0),
        (1, 0, 1, 0),
        (1, 0, 1, 1),
        (0, 1, 1, 0),
    )

    colors = (
        (1, 1, 1, 1),
        (1, 1, 1, 1),
        (1, 14, 1, 1),
        (1, 1, 1, 1),
    )
