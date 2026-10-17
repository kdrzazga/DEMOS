"""Stronghold morph: shows, step by step, how a scanned hand drawing is
cleaned, analysed and bent from a flat picture into a 3D model.

Keys: ESC quits, RIGHT skips to the next stage.
"""
import math
import os
import sys

import pygame
from pygame.locals import DOUBLEBUF, FULLSCREEN, K_ESCAPE, K_RIGHT, KEYDOWN, MOUSEBUTTONDOWN, OPENGL, QUIT

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from lib.base_demo import BaseDemo
from demos.morph.drawing import Drawing
from demos.morph.model import StrongholdModel
from demos.morph.pieces import stronghold_pieces, stronghold_rock_zone
from demos.morph.scene import Scene

SCAN_PATH = os.path.join(os.path.dirname(__file__), "res", "stronghold_scan.png")


def smooth(fraction):
    fraction = min(1.0, max(0.0, fraction))
    return fraction * fraction * (3.0 - 2.0 * fraction)


class Stage:

    def __init__(self, key, seconds, title="", detail=""):
        self.key = key
        self.seconds = seconds
        self.title = title
        self.detail = detail


class MorphDemo(BaseDemo):

    def __init__(self, width, height, title, fps=60, windowed=False, triggered=False, scan_path=SCAN_PATH,
                 orbit_yaw=40.0, orbit_pitch=12.0, pivot_depth=0.4, caption_fade=0.4):
        super().__init__(windowed=windowed, triggered=triggered)
        self.width = width
        self.height = height
        self.title = title
        self.fps = fps
        self.clock = pygame.time.Clock()
        self.longest_frame = 0.1
        self.orbit_yaw = orbit_yaw
        self.orbit_pitch = orbit_pitch
        self.pivot_depth = pivot_depth
        self.caption_fade = caption_fade

        pygame.init()
        pygame.mouse.set_visible(False)
        self._init_display()
        self.model = StrongholdModel(Drawing(scan_path), stronghold_pieces(), stronghold_rock_zone())
        self.scene = Scene(self.width, self.height, self.model)
        self.probe_sweep = (min(p.probe_x.min() for p in self.model.pieces) - 30,
                            max(p.probe_x.max() for p in self.model.pieces) + 30)
        self.stages = (
            Stage("scan", 3.0, "1. the scan", "a hand drawing on squared paper"),
            Stage("clean", 4.0, "2. removing the grid",
                  "the mesh is light grey, the ink is black: keep only pixels darker than the ink threshold"),
            Stage("probe", 4.5, "3. finding the crowns",
                  "every pixel column is probed from above until it hits ink - that traces the battlements"),
            Stage("outline", 3.5, "4. tracing the shapes",
                  "red: towers -> cylinders     blue: walls -> blocks     dashed: tower axis"),
            Stage("morph", 6.0, "5. bending into 3D",
                  "each pixel keeps its x and gains depth  z = r cos(asin(2s - 1));  the drawing is the texture"),
            Stage("rocks", 6.0, "6. raising the rocks",
                  "distance to the nearest ink line becomes height: every outlined stone swells into a block"),
            Stage("fix", 4.0, "7. small fix", "the keep steps back, the left tower and wall step forward, the walls reach into the towers"),
            Stage("orbit", 12.0, "8. Stronghold in 3D", ""),
            Stage("unmorph", 4.0, "9. back to paper", ""),
            Stage("restore", 2.0),
        )
        self.stage_index = 0
        self.stage_time = 0.0

    def _init_display(self):
        pygame.display.gl_set_attribute(pygame.GL_MULTISAMPLEBUFFERS, 1)
        pygame.display.gl_set_attribute(pygame.GL_MULTISAMPLESAMPLES, 4)
        flags = DOUBLEBUF | OPENGL
        if self.windowed:
            pygame.display.set_mode((self.width, self.height), flags)
        else:
            pygame.display.set_mode((0, 0), flags | FULLSCREEN)
        self.width, self.height = pygame.display.get_surface().get_size()
        pygame.display.set_caption(self.title)

    @property
    def stage(self):
        return self.stages[self.stage_index]

    def next_stage(self):
        self.stage_index = (self.stage_index + 1) % len(self.stages)
        self.stage_time = 0.0

    def step(self, delta_seconds):
        self.stage_time += min(self.longest_frame, delta_seconds)
        if self.stage_time >= self.stage.seconds:
            self.next_stage()
        stage = self.stage
        progress = self.stage_time / stage.seconds
        self.scene.clear()
        self.scene.look()
        getattr(self, "_render_" + stage.key)(progress)
        caption_alpha = min(1.0, self.stage_time / self.caption_fade,
                            (stage.seconds - self.stage_time) / self.caption_fade)
        self.scene.draw_caption(stage.title, stage.detail, caption_alpha)

    # ------------------------------------------------------------- stages

    def _render_scan(self, progress):
        self.scene.draw_image(self.scene.scan_texture, paper_tinted=False)

    def _render_clean(self, progress):
        sweep = smooth(progress) * self.model.drawing.width
        self.scene.draw_image(self.scene.clean_texture, 0, sweep)
        self.scene.draw_image(self.scene.scan_texture, sweep, None, paper_tinted=False)
        self.scene.draw_scan_line(sweep, alpha=min(1.0, 4 * (1.0 - progress)))

    def _render_probe(self, progress):
        start, end = self.probe_sweep
        sweep = start + (end - start) * min(1.0, progress / 0.85)
        self.scene.draw_image(self.scene.clean_texture)
        self.scene.draw_probes(sweep)
        self.scene.draw_scan_line(sweep, alpha=min(1.0, 8 * (1.0 - progress)))

    def _render_outline(self, progress):
        self.scene.draw_model(0.0, highlight=0.3 * smooth(progress * 2.0 - 1.0))
        self.scene.draw_probes(self.probe_sweep[1], alpha=1.0 - smooth(progress * 2.0))
        self.scene.draw_outlines(smooth(progress / 0.7))

    def _render_morph(self, progress):
        morph = smooth(progress)
        self._look_morphed(morph, self.orbit_yaw * morph, self.orbit_pitch * morph)
        self.scene.draw_model(morph, highlight=0.3 * (1.0 - smooth(progress * 3.0)))
        self.scene.draw_outlines(1.0, alpha=1.0 - smooth(progress * 5.0))

    def _render_rocks(self, progress):
        self._look_morphed(1.0, self.orbit_yaw, self.orbit_pitch)
        height_map_shown = smooth(progress / 0.3) * (1.0 - smooth((progress - 0.65) / 0.35))
        self.scene.draw_model(1.0, lift=smooth((progress - 0.25) / 0.6), swell_tint=0.6 * height_map_shown)

    def _render_fix(self, progress):
        self._look_morphed(1.0, self.orbit_yaw, self.orbit_pitch)
        self.scene.draw_model(1.0, lift=1.0, fix=smooth(progress))

    def _render_orbit(self, progress):
        angle = 2 * math.pi * progress
        self._look_morphed(1.0, self.orbit_yaw * math.cos(angle), self.orbit_pitch * (1.0 + 0.8 * math.sin(angle)))
        self.scene.draw_model(1.0, lift=1.0, fix=1.0)

    def _render_unmorph(self, progress):
        morph = 1.0 - smooth(progress)
        self._look_morphed(morph, self.orbit_yaw * morph, self.orbit_pitch * morph)
        self.scene.draw_model(morph, lift=morph, fix=1.0)

    def _render_restore(self, progress):
        self.scene.draw_image(self.scene.clean_texture)
        self.scene.draw_image(self.scene.scan_texture, alpha=smooth(progress), paper_tinted=False)

    def _look_morphed(self, morph, yaw, pitch):
        self.scene.look(yaw, pitch, self.pivot_depth * morph)

    # ------------------------------------------------------------- loop

    def run(self):
        running = True
        while running:
            delta_seconds = self.clock.tick(self.fps) / 1000.0
            for event in pygame.event.get():
                if event.type == QUIT:
                    running = False
                elif event.type == KEYDOWN and event.key == K_ESCAPE:
                    running = False
                elif event.type == KEYDOWN and event.key == K_RIGHT:
                    self.next_stage()
                elif event.type == MOUSEBUTTONDOWN:
                    self.trigger()
            if self.paused:
                self.scene.clear()
            else:
                self.step(delta_seconds)
            pygame.display.flip()
        pygame.quit()


if __name__ == "__main__":
    MorphDemo(1280, 720, "Stronghold morph", windowed=True).run()
