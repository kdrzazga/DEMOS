from demos.petscii.files.petscii.bruce_lee import BruceLee


class BruceSprite(BruceLee):
    """A single Bruce Lee pose used as a free-standing, movable sprite -- as opposed
    to the full-screen BruceLee stages. Defaults to the jump pose, the one that
    falls into and stands on a screen face."""

    def __init__(self, char_size):
        super().__init__(char_size)
        self.jump()
