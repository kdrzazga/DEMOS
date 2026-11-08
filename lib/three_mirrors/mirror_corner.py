from lib.three_mirrors.mirror import Mirror
from lib.three_mirrors.mirror_renderer import MirrorRenderer


class FramedScene:

    def __init__(self, scene, mirrors):
        self.scene = scene
        self.mirrors = mirrors

    def illuminate(self):
        self.scene.illuminate()

    def draw(self):
        self.scene.draw()
        for mirror in self.mirrors:
            mirror.draw_frame()


class MirrorCorner:

    def __init__(self, size):
        self.size = size
        self.mirrors = [
            Mirror.spanning((0.0, 0.0, 0.0), (0.0, size, 0.0), (0.0, 0.0, size)),
            Mirror.spanning((0.0, 0.0, 0.0), (0.0, 0.0, size), (size, 0.0, 0.0)),
            Mirror.spanning((0.0, 0.0, 0.0), (size, 0.0, 0.0), (0.0, size, 0.0)),
        ]
        self.renderer = MirrorRenderer(max_reflections=3, reflection_limit=5)

    @property
    def max_reflections(self):
        return self.renderer.max_reflections

    def change_reflections(self, step):
        self.renderer.change_reflections(step)

    def render(self, scene, eye):
        self.renderer.render(self.mirrors, FramedScene(scene, self.mirrors), eye)
