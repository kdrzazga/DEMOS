import numpy
from OpenGL.GL import (
    GL_BLEND,
    GL_COLOR_BUFFER_BIT,
    GL_DEPTH_BUFFER_BIT,
    GL_ENABLE_BIT,
    GL_FALSE,
    GL_FLOAT,
    GL_LIGHTING,
    GL_LINES,
    GL_ONE_MINUS_SRC_ALPHA,
    GL_SRC_ALPHA,
    GL_TEXTURE_2D,
    GL_VERTEX_ARRAY,
    glBlendFunc,
    glColor4f,
    glDepthMask,
    glDisable,
    glDisableClientState,
    glDrawArrays,
    glEnable,
    glEnableClientState,
    glPopAttrib,
    glPushAttrib,
    glVertexPointer,
)


class Rain:

    def __init__(self, drop_count, low_corner, high_corner, randomness):
        generator = numpy.random.default_rng(randomness.randrange(1 << 30))
        self.low = numpy.array(tuple(low_corner), dtype=numpy.float32)
        self.high = numpy.array(tuple(high_corner), dtype=numpy.float32)
        self.drops = generator.uniform(self.low, self.high, (drop_count, 3)).astype(numpy.float32)
        self.velocity = numpy.array((-1.2, -24.0, 0.8), dtype=numpy.float32)
        self.streak_seconds = 0.035
        self.color = (0.65, 0.8, 0.75, 0.22)
        self.enabled = True
        self.segments = numpy.zeros((2 * drop_count, 3), dtype=numpy.float32)

    def toggle(self):
        self.enabled = not self.enabled

    def update(self, seconds):
        self.drops += self.velocity * seconds
        span = self.high - self.low
        self.drops = self.low + numpy.mod(self.drops - self.low, span)

    def draw(self):
        if not self.enabled:
            return
        self.segments[0::2] = self.drops
        self.segments[1::2] = self.drops - self.velocity * self.streak_seconds
        glPushAttrib(GL_ENABLE_BIT | GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glDisable(GL_LIGHTING)
        glDisable(GL_TEXTURE_2D)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glDepthMask(GL_FALSE)
        glColor4f(*self.color)
        glEnableClientState(GL_VERTEX_ARRAY)
        glVertexPointer(3, GL_FLOAT, 0, self.segments)
        glDrawArrays(GL_LINES, 0, len(self.segments))
        glDisableClientState(GL_VERTEX_ARRAY)
        glPopAttrib()
