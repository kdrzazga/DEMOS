import os
from collections import deque
from functools import lru_cache

import numpy as np
import pygame
from OpenGL.GL import *

WHITE = (1.0, 1.0, 1.0)
SILHOUETTE_SHEET = os.path.join(os.path.dirname(os.path.abspath(__file__)), "silhouettes.png")
FIGURES_IN_ROW = 14


def _label_regions(mask):
    labels = np.zeros(mask.shape, dtype=np.int32)
    rows, columns = mask.shape
    region_count = 0
    for start_row, start_column in zip(*np.nonzero(mask)):
        if labels[start_row, start_column]:
            continue
        region_count += 1
        labels[start_row, start_column] = region_count
        pending = deque(((start_row, start_column),))
        while pending:
            row, column = pending.popleft()
            for next_row, next_column in ((row - 1, column), (row + 1, column), (row, column - 1), (row, column + 1)):
                if (0 <= next_row < rows and 0 <= next_column < columns
                        and mask[next_row, next_column] and not labels[next_row, next_column]):
                    labels[next_row, next_column] = region_count
                    pending.append((next_row, next_column))
    return labels, region_count


def _solid_figure_mask(path, darkness_threshold):
    sheet = pygame.image.load(path)
    rgb = pygame.surfarray.array3d(sheet).transpose(1, 0, 2).astype(np.float32) / 255.0
    alpha = pygame.surfarray.array_alpha(sheet).transpose(1, 0)
    luminance = rgb @ np.array((0.299, 0.587, 0.114), dtype=np.float32)
    dark = (luminance < darkness_threshold) & (alpha >= 128)

    background_labels, _ = _label_regions(~dark)
    border_labels = np.unique(np.concatenate((background_labels[0, :], background_labels[-1, :],
                                              background_labels[:, 0], background_labels[:, -1])))
    outside = np.isin(background_labels, border_labels[border_labels > 0])
    return ~outside


@lru_cache(maxsize=None)
def load_figure_masks(path=SILHOUETTE_SHEET, darkness_threshold=0.5):
    """Returns the 14 source figures, left to right.
    Each mask is a bool array indexed [row, column] with row 0 at the top."""
    figure_mask = _solid_figure_mask(path, darkness_threshold)
    labels, region_count = _label_regions(figure_mask)
    sizes = np.bincount(labels.ravel(), minlength=region_count + 1)
    sizes[0] = 0
    largest = np.argsort(sizes)[::-1][:FIGURES_IN_ROW]
    if len(largest) < FIGURES_IN_ROW or sizes[largest[-1]] == 0:
        raise ValueError(f"expected {FIGURES_IN_ROW} silhouettes in {path}, found {np.count_nonzero(sizes)}")

    originals = []
    for label in sorted(largest, key=lambda region: np.nonzero(labels == region)[1].mean()):
        figure_rows, figure_columns = np.nonzero(labels == label)
        crop = labels[figure_rows.min():figure_rows.max() + 1, figure_columns.min():figure_columns.max() + 1]
        originals.append(crop == label)
    return tuple(originals)


class Silhouette:
    def __init__(self, number, color=WHITE, thick=4, switch_interval=0.5):
        masks = load_figure_masks()
        if not 0 <= number < len(masks):
            raise IndexError(f"silhouette number must be in 0..{len(masks) - 1}, got {number}")
        self.number = number
        self.color = color
        self.thick = thick
        self.switch_interval = switch_interval
        self.switch_timer = 0.0
        self.unit_scale = 1.0 / max(mask.shape[0] for mask in masks)
        upper_stage = masks[number]
        bottom_stage = np.fliplr(upper_stage)
        self.bottom_stage_drop = 2 * (number - 6) if number >= 7 else 0
        self.stage_display_lists = (self._compile(upper_stage), self._compile(bottom_stage, self.bottom_stage_drop))
        self.stage = 0

    def _cell_bounds(self, mask, row, column):
        rows, columns = mask.shape
        left = column - columns / 2.0
        bottom = rows - 1 - row
        return left, left + 1.0, bottom, bottom + 1.0

    def _filled(self, mask, row, column):
        rows, columns = mask.shape
        return 0 <= row < rows and 0 <= column < columns and mask[row, column]

    def _row_runs(self, mask, row):
        columns = mask.shape[1]
        run_start = None
        for column in range(columns + 1):
            inside = column < columns and mask[row, column]
            if inside and run_start is None:
                run_start = column
            elif not inside and run_start is not None:
                yield run_start, column
                run_start = None

    def _draw_caps(self, mask):
        front = self.thick / 2.0
        back = -front
        for row in range(mask.shape[0]):
            for run_start, run_end in self._row_runs(mask, row):
                left, _, bottom, top = self._cell_bounds(mask, row, run_start)
                right = self._cell_bounds(mask, row, run_end - 1)[1]
                glNormal3f(0.0, 0.0, 1.0)
                glVertex3f(left, bottom, front)
                glVertex3f(right, bottom, front)
                glVertex3f(right, top, front)
                glVertex3f(left, top, front)
                glNormal3f(0.0, 0.0, -1.0)
                glVertex3f(left, bottom, back)
                glVertex3f(left, top, back)
                glVertex3f(right, top, back)
                glVertex3f(right, bottom, back)

    def _draw_side_walls(self, mask):
        front = self.thick / 2.0
        back = -front
        for row, column in zip(*np.nonzero(mask)):
            left, right, bottom, top = self._cell_bounds(mask, row, column)
            if not self._filled(mask, row, column - 1):
                glNormal3f(-1.0, 0.0, 0.0)
                glVertex3f(left, bottom, back)
                glVertex3f(left, bottom, front)
                glVertex3f(left, top, front)
                glVertex3f(left, top, back)
            if not self._filled(mask, row, column + 1):
                glNormal3f(1.0, 0.0, 0.0)
                glVertex3f(right, bottom, front)
                glVertex3f(right, bottom, back)
                glVertex3f(right, top, back)
                glVertex3f(right, top, front)
            if not self._filled(mask, row - 1, column):
                glNormal3f(0.0, 1.0, 0.0)
                glVertex3f(left, top, front)
                glVertex3f(right, top, front)
                glVertex3f(right, top, back)
                glVertex3f(left, top, back)
            if not self._filled(mask, row + 1, column):
                glNormal3f(0.0, -1.0, 0.0)
                glVertex3f(left, bottom, back)
                glVertex3f(right, bottom, back)
                glVertex3f(right, bottom, front)
                glVertex3f(left, bottom, front)

    def _compile(self, mask, drop=0):
        display_list = glGenLists(1)
        glNewList(display_list, GL_COMPILE)
        glPushMatrix()
        glScalef(self.unit_scale, self.unit_scale, self.unit_scale)
        glTranslatef(0.0, -drop, 0.0)
        glColor3f(*self.color)
        glBegin(GL_QUADS)
        self._draw_caps(mask)
        self._draw_side_walls(mask)
        glEnd()
        glPopMatrix()
        glEndList()
        return display_list

    def update(self, delta_seconds):
        self.switch_timer += delta_seconds
        while self.switch_timer >= self.switch_interval:
            self.switch_timer -= self.switch_interval
            self.stage = 1 - self.stage

    def draw(self):
        glCallList(self.stage_display_lists[self.stage])
