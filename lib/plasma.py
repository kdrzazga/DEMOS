import math

import numpy


class PlasmaField:

    def __init__(self, columns, rows):
        self.columns = columns
        self.rows = rows
        self.channel_phase_shifts = (0.0, 2.1, 4.2)
        self.across, self.up = numpy.meshgrid(numpy.linspace(0.0, 1.0, columns, dtype=numpy.float32),
                                              numpy.linspace(0.0, 1.0, rows, dtype=numpy.float32))
        self.from_center = numpy.hypot(self.across - 0.5, self.up - 0.5)
        self.colors = numpy.zeros((rows, columns, 3), dtype=numpy.float32)

    def colors_at(self, moment):
        wave = (numpy.sin(self.across * 7.0 + moment)
                + numpy.sin(self.up * 5.0 - moment * 1.3)
                + numpy.sin((self.across + self.up) * 6.0 + moment * 0.7)
                + numpy.sin(self.from_center * 12.0 - moment * 1.7)) / 4.0
        for channel, phase_shift in enumerate(self.channel_phase_shifts):
            self.colors[:, :, channel] = 0.5 + 0.5 * numpy.sin(math.pi * wave + phase_shift)
        return self.colors
