import math

import numpy as np
from OpenGL.GL import *

from demos.WinterDemo26.silhouette import Silhouette


class SittingSilhouette(Silhouette):
    """A seated person built like the dancing silhouettes: pixel masks extruded into blocks.

    The side profile is rasterised from capsules instead of read from silhouettes.png, and
    each body part is extruded to its own width (narrow head, wide torso, two legs, two arms).
    Local frame: feet on y=0, the person's back at x=0, facing +x; body width runs along z.
    Like the dancers, two poses (a typing bob) alternate every switch_interval seconds.
    """

    def __init__(self, color=(0.12, 0.10, 0.16), cell_size=0.02, switch_interval=0.3, phase=0.0):
        self.color = color
        self.cell_size = cell_size
        self.switch_interval = switch_interval
        self.switch_timer = phase % switch_interval
        self.figure_height = 1.28
        self.figure_depth = 0.78
        self.part_layout = {
            "head": (0.18, (0.0,)),
            "torso": (0.36, (0.0,)),
            "leg": (0.15, (-0.10, 0.10)),
            "arm": (0.08, (-0.21, 0.21)),
        }
        poses = (self._pose(hand=(0.68, 0.80), head=(0.24, 1.14)),
                 self._pose(hand=(0.70, 0.815), head=(0.25, 1.13)))
        self.stage_display_lists = tuple(self._compile_pose(pose) for pose in poses)
        self.stage = 0

    def _pose(self, hand, head):
        """Side profile as capsules (start, end, radius) per body part, in metres."""
        shoulder = (0.22, 0.93)
        elbow = (0.40, 0.72)
        neck_base = (0.21, 0.98)
        return {
            "head": ((head, head, 0.105),
                     (neck_base, (head[0] - 0.01, head[1] - 0.06), 0.05)),
            "torso": (((0.13, 0.55), (0.20, 0.95), 0.12),),
            "leg": (((0.12, 0.53), (0.45, 0.53), 0.075),
                    ((0.47, 0.50), (0.47, 0.08), 0.055),
                    ((0.44, 0.04), (0.58, 0.04), 0.04)),
            "arm": ((shoulder, elbow, 0.045),
                    (elbow, hand, 0.04)),
        }

    def _capsule_distance(self, forward, height, start, end):
        segment_forward = end[0] - start[0]
        segment_height = end[1] - start[1]
        segment_length_squared = segment_forward * segment_forward + segment_height * segment_height
        if segment_length_squared == 0.0:
            along = np.zeros_like(forward)
        else:
            along = ((forward - start[0]) * segment_forward + (height - start[1]) * segment_height) / segment_length_squared
            along = np.clip(along, 0.0, 1.0)
        return np.hypot(forward - (start[0] + along * segment_forward), height - (start[1] + along * segment_height))

    def _rasterize(self, capsules):
        """Bool mask indexed [row, column] with row 0 at the top, like the sheet masks."""
        rows = math.ceil(self.figure_height / self.cell_size)
        columns = math.ceil(self.figure_depth / self.cell_size)
        forward_centers = (np.arange(columns) + 0.5) * self.cell_size
        height_centers = (rows - 1 - np.arange(rows) + 0.5) * self.cell_size
        forward, height = np.meshgrid(forward_centers, height_centers)
        mask = np.zeros((rows, columns), dtype=bool)
        for start, end, radius in capsules:
            mask |= self._capsule_distance(forward, height, start, end) <= radius
        return mask

    def _compile_pose(self, pose):
        display_list = glGenLists(1)
        glNewList(display_list, GL_COMPILE)
        glColor3f(*self.color)
        for part, capsules in pose.items():
            mask = self._rasterize(capsules)
            width, offsets = self.part_layout[part]
            for offset in offsets:
                glPushMatrix()
                glTranslatef(0.0, 0.0, offset)
                glScalef(self.cell_size, self.cell_size, self.cell_size)
                glTranslatef(mask.shape[1] / 2.0, 0.0, 0.0)
                glBegin(GL_QUADS)
                self._draw_caps(mask, width / self.cell_size)
                self._draw_side_walls(mask, width / self.cell_size)
                glEnd()
                glPopMatrix()
        glEndList()
        return display_list
