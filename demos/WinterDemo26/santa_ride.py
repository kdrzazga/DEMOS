import math
import os
import sys
import random
from OpenGL.GL import *
from OpenGL.GLU import *

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from demos.WinterDemo26.sleigh import Sleigh
from demos.WinterDemo26.santa_claus import SantaClaus
from demos.WinterDemo26.reindeer import Reindeer


class SantaRide:
    def __init__(self, x, y, z, size=1.0, facing=0.0, pitch=0.0, bob=True, seed=0):
        self.x = x
        self.y = y
        self.z = z
        self.size = size
        self.facing = facing
        self.pitch = pitch
        self.bob = bob
        self.random_generator = random.Random(seed)
        self.time = 0.0
        self.bob_phase = self.random_generator.uniform(0.0, math.tau)
        self.bob_lift = 0.10
        self.bob_tilt = 2.5

        self.rein_color = (0.28, 0.17, 0.10)
        self.rein_anchor = (1.05, 0.75)
        self.rein_spread = 0.30
        self.rein_sag = 0.16

        self.quadric = gluNewQuadric()
        gluQuadricNormals(self.quadric, GLU_SMOOTH)

        self.sleigh = Sleigh(0.0, 0.0, 0.0, size=1.0, seed=seed + 1)
        seat = self.sleigh.seat_position()
        self.santa = SantaClaus(seat[0], seat[1], seat[2], size=0.8, wave=True, seed=seed + 2)
        self.reindeer = Reindeer(0.0, -0.40, 2.75, size=1.0, gallop=True, seed=seed + 3)

    def update(self, dt):
        self.time += dt
        self.santa.update(dt)
        self.reindeer.update(dt)

    def _rein_path(self, start, end, steps=12):
        path = []
        for step in range(steps + 1):
            fraction = step / steps
            drop = math.sin(math.pi * fraction) * self.rein_sag
            path.append((start[0] + (end[0] - start[0]) * fraction - drop,
                         start[1] + (end[1] - start[1]) * fraction))
        return path

    def _sweep_tube(self, path, radius, sides):
        count = len(path)
        frames = []
        for index in range(count):
            previous = path[max(0, index - 1)]
            following = path[min(count - 1, index + 1)]
            tangent_y = following[0] - previous[0]
            tangent_z = following[1] - previous[1]
            length = math.hypot(tangent_y, tangent_z)
            if length == 0.0:
                tangent_y, tangent_z, length = 0.0, 1.0, 1.0
            frames.append((path[index][0], path[index][1], -tangent_z / length, tangent_y / length))
        for index in range(count - 1):
            glBegin(GL_QUAD_STRIP)
            for step in range(sides + 1):
                angle = math.tau * step / sides
                across = math.cos(angle)
                along = math.sin(angle)
                for center_y, center_z, normal_y, normal_z in (frames[index + 1], frames[index]):
                    glNormal3f(across, along * normal_y, along * normal_z)
                    glVertex3f(across * radius,
                               center_y + along * normal_y * radius,
                               center_z + along * normal_z * radius)
            glEnd()

    def _draw_reins(self):
        harness = self.reindeer.harness_position()
        glColor3f(*self.rein_color)
        for side in (-1.0, 1.0):
            glPushMatrix()
            glTranslatef(side * self.rein_spread, 0.0, 0.0)
            self._sweep_tube(self._rein_path(self.rein_anchor, (harness[1], harness[2])), 0.028, 7)
            glPopMatrix()

    def _flight_sway(self):
        if not self.bob:
            return 0.0, 0.0
        return (math.sin(self.time * 1.4 + self.bob_phase) * self.bob_lift,
                math.sin(self.time * 1.1 + self.bob_phase * 0.7) * self.bob_tilt)

    def draw(self):
        lift, tilt = self._flight_sway()
        glPushMatrix()
        glTranslatef(self.x, self.y + lift, self.z)
        glRotatef(self.facing, 0.0, 1.0, 0.0)
        glRotatef(self.pitch + tilt, 1.0, 0.0, 0.0)
        glScalef(self.size, self.size, self.size)
        self.sleigh.draw()
        self.santa.draw()
        self.reindeer.draw()
        self._draw_reins()
        glPopMatrix()
