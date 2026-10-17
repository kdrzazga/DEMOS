"""OpenGL drawing of every stage: the flat images, the probing and tracing
overlays, the morphing 3D model and the captions."""
import math

import numpy as np
import pygame
from OpenGL.GL import *
from OpenGL.GLU import gluLookAt, gluPerspective

from demos.morph.pieces import Tower


def upload_texture(pixels):
    height, width, channels = pixels.shape
    pixel_format = GL_RGBA if channels == 4 else GL_RGB
    texture = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, texture)
    glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
    glTexImage2D(GL_TEXTURE_2D, 0, pixel_format, width, height, 0, pixel_format, GL_UNSIGNED_BYTE,
                 np.ascontiguousarray(pixels, np.uint8))
    glGenerateMipmap(GL_TEXTURE_2D)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
    return texture


class Scene:

    def __init__(self, screen_width, screen_height, model, paper_color=(0.96, 0.94, 0.89),
                 ink_color=(0.05, 0.05, 0.08), scan_line_color=(1.0, 0.55, 0.0), rock_color=(0.92, 0.48, 0.12),
                 field_of_view=30.0,
                 light_direction=(-0.45, 0.55, 0.70), font_name="consolas"):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.model = model
        self.paper_color = np.array(paper_color, np.float32)
        self.ink_color = ink_color
        self.scan_line_color = scan_line_color
        self.rock_color = np.array(rock_color, np.float32)
        self.field_of_view = field_of_view
        light = np.array(light_direction, np.float32)
        self.light_direction = light / np.linalg.norm(light)

        drawing = model.drawing
        self.scan_texture = upload_texture(drawing.scan_rgb)
        self.clean_texture = upload_texture(drawing.clean_rgb())
        sheet_pixels = np.full((drawing.height, drawing.width, 4), 255, np.uint8)
        sheet_pixels[:, :, 3] = (model.backdrop_ink * 255).astype(np.uint8)
        self.sheet_texture = upload_texture(sheet_pixels)

        world_width, world_height = model.world_size
        half_view = math.tan(math.radians(field_of_view) / 2)
        aspect = screen_width / screen_height
        self.fit_distance = 1.03 * max(world_height / 2 / half_view, world_width / 2 / (half_view * aspect))
        self.outlines = [self._world_polyline(np.vstack((p.footprint(), p.footprint()[:1]))) for p in model.pieces]

        self.title_font = pygame.font.SysFont(font_name, max(20, screen_height // 26), bold=True)
        self.detail_font = pygame.font.SysFont(font_name, max(14, screen_height // 44))
        self.caption_textures = {}

        glClearColor(*self.paper_color, 1.0)
        glDepthFunc(GL_LEQUAL)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glDisable(GL_CULL_FACE)
        glHint(GL_LINE_SMOOTH_HINT, GL_NICEST)

    def _world_polyline(self, pixel_points):
        x, y = self.model.to_world(pixel_points[:, 0], pixel_points[:, 1])
        points = np.column_stack((x, y))
        lengths = np.concatenate(([0.0], np.cumsum(np.linalg.norm(np.diff(points, axis=0), axis=1))))
        return points, lengths

    # ----------------------------------------------------------- camera

    def clear(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    def look(self, yaw_degrees=0.0, pitch_degrees=0.0, pivot_depth=0.0):
        """Orbit around a pivot pivot_depth behind the paper; (0, 0, 0) shows the drawing exactly."""
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(self.field_of_view, self.screen_width / self.screen_height, 0.1, 100.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        yaw, pitch = math.radians(yaw_degrees), math.radians(pitch_degrees)
        distance = self.fit_distance + pivot_depth
        gluLookAt(distance * math.sin(yaw) * math.cos(pitch),
                  distance * math.sin(pitch),
                  distance * math.cos(yaw) * math.cos(pitch) - pivot_depth,
                  0.0, 0.0, -pivot_depth,
                  0.0, 1.0, 0.0)

    # ----------------------------------------------------------- flat images

    def draw_image(self, texture, from_pixel_x=None, to_pixel_x=None, alpha=1.0, paper_tinted=True):
        drawing = self.model.drawing
        from_pixel_x = 0 if from_pixel_x is None else from_pixel_x
        to_pixel_x = drawing.width if to_pixel_x is None else to_pixel_x
        if to_pixel_x <= from_pixel_x:
            return
        left, top = self.model.to_world(from_pixel_x, 0)
        right, bottom = self.model.to_world(to_pixel_x, drawing.height)
        u_left, u_right = from_pixel_x / drawing.width, to_pixel_x / drawing.width
        glDisable(GL_DEPTH_TEST)
        glEnable(GL_BLEND)
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, texture)
        tint = self.paper_color if paper_tinted else (1.0, 1.0, 1.0)
        glColor4f(*tint, alpha)
        glBegin(GL_QUADS)
        glTexCoord2f(u_left, 0.0); glVertex3f(left, top, 0.0)
        glTexCoord2f(u_left, 1.0); glVertex3f(left, bottom, 0.0)
        glTexCoord2f(u_right, 1.0); glVertex3f(right, bottom, 0.0)
        glTexCoord2f(u_right, 0.0); glVertex3f(right, top, 0.0)
        glEnd()
        glDisable(GL_TEXTURE_2D)

    def draw_scan_line(self, pixel_x, alpha=1.0):
        x, top = self.model.to_world(pixel_x, 0)
        _, bottom = self.model.to_world(pixel_x, self.model.drawing.height)
        glow = 14 / self.model.pixels_per_unit
        glDisable(GL_DEPTH_TEST)
        glEnable(GL_BLEND)
        glBegin(GL_QUADS)
        glColor4f(*self.scan_line_color, 0.0); glVertex3f(x - glow, top, 0); glVertex3f(x - glow, bottom, 0)
        glColor4f(*self.scan_line_color, 0.35 * alpha); glVertex3f(x, bottom, 0); glVertex3f(x, top, 0)
        glColor4f(*self.scan_line_color, 0.35 * alpha); glVertex3f(x, top, 0); glVertex3f(x, bottom, 0)
        glColor4f(*self.scan_line_color, 0.0); glVertex3f(x + glow, bottom, 0); glVertex3f(x + glow, top, 0)
        glEnd()
        glLineWidth(2.0)
        glColor4f(*self.scan_line_color, alpha)
        glBegin(GL_LINES)
        glVertex3f(x, top, 0); glVertex3f(x, bottom, 0)
        glEnd()

    # ----------------------------------------------------------- detection overlays

    def draw_probes(self, sweep_pixel_x, alpha=1.0):
        """Each probe falls from the top of its search band to the first ink it meets."""
        glDisable(GL_DEPTH_TEST)
        glEnable(GL_BLEND)
        glEnable(GL_LINE_SMOOTH)
        glLineWidth(1.5)
        glBegin(GL_LINES)
        for piece in self.model.pieces:
            glColor4f(*piece.highlight, 0.45 * alpha)
            for x, start_y, crown_y in piece.probes():
                if x <= sweep_pixel_x:
                    glVertex3f(*self.model.to_world(x, start_y), 0.0)
                    glVertex3f(*self.model.to_world(x, crown_y), 0.0)
        glEnd()
        glPointSize(5.0)
        glBegin(GL_POINTS)
        for piece in self.model.pieces:
            glColor4f(*piece.highlight, alpha)
            for x, _, crown_y in piece.probes():
                if x <= sweep_pixel_x:
                    glVertex3f(*self.model.to_world(x, crown_y), 0.0)
        glEnd()
        glDisable(GL_LINE_SMOOTH)

    def draw_outlines(self, progress, alpha=1.0):
        """Trace every piece's outline up to ``progress``; towers then get a dashed axis."""
        if alpha <= 0.0:
            return
        glDisable(GL_DEPTH_TEST)
        glEnable(GL_BLEND)
        glEnable(GL_LINE_SMOOTH)
        glLineWidth(3.0)
        for piece, (points, lengths) in zip(self.model.pieces, self.outlines):
            reached = progress * lengths[-1]
            glColor4f(*piece.highlight, alpha)
            glBegin(GL_LINE_STRIP)
            for index, point in enumerate(points):
                if lengths[index] <= reached:
                    glVertex3f(point[0], point[1], 0.0)
                else:
                    segment = (reached - lengths[index - 1]) / (lengths[index] - lengths[index - 1])
                    tip = points[index - 1] + (point - points[index - 1]) * segment
                    glVertex3f(tip[0], tip[1], 0.0)
                    break
            glEnd()
        axis_alpha = alpha * min(1.0, max(0.0, progress * 2.0 - 1.0))
        glEnable(GL_LINE_STIPPLE)
        glLineStipple(4, 0x0F0F)
        glLineWidth(2.0)
        glBegin(GL_LINES)
        for piece in self.model.pieces:
            if isinstance(piece, Tower):
                glColor4f(*piece.highlight, axis_alpha)
                for pixel_point in piece.axis_line():
                    glVertex3f(*self.model.to_world(*pixel_point), 0.0)
        glEnd()
        glDisable(GL_LINE_STIPPLE)
        glDisable(GL_LINE_SMOOTH)

    # ----------------------------------------------------------- 3D model

    def draw_model(self, morph, highlight=0.0, lift=0.0, swell_tint=0.0, fix=0.0):
        """morph bends towers and walls (and tilts the backdrop), lift swells the rocks,
        swell_tint paints the rock height map in rock_color, fix applies the pieces' depth fixes."""
        solids = self.model.solids
        shade = solids.shading_at(morph, self.light_direction, fix)
        colors = (self.paper_color[None, :] * shade[:, None] * (1.0 - highlight)
                  + solids.highlight * highlight).astype(np.float32)
        positions = solids.positions_at(morph, fix)

        glEnable(GL_DEPTH_TEST)
        glDisable(GL_BLEND)
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, self.clean_texture)
        glEnableClientState(GL_VERTEX_ARRAY)
        glEnableClientState(GL_TEXTURE_COORD_ARRAY)
        glEnableClientState(GL_COLOR_ARRAY)
        glVertexPointer(3, GL_FLOAT, 0, positions)
        glTexCoordPointer(2, GL_FLOAT, 0, solids.uv)
        glColorPointer(3, GL_FLOAT, 0, colors)
        glDrawElements(GL_TRIANGLES, len(solids.triangles), GL_UNSIGNED_INT, solids.triangles)

        rocks = self.model.rocks
        rock_positions = rocks.positions_at(morph, lift)
        rock_shade = rocks.shading_at(morph, self.light_direction)
        tint = (rocks.swell * swell_tint)[:, None]
        rock_colors = (self.paper_color[None, :] * rock_shade[:, None] * (1.0 - tint)
                       + self.rock_color[None, :] * tint).astype(np.float32)
        glVertexPointer(3, GL_FLOAT, 0, rock_positions)
        glTexCoordPointer(2, GL_FLOAT, 0, rocks.uv)
        glColorPointer(3, GL_FLOAT, 0, rock_colors)
        glDrawElements(GL_TRIANGLES, len(rocks.triangles), GL_UNSIGNED_INT, rocks.triangles)
        glDisableClientState(GL_COLOR_ARRAY)

        sheet = self.model.sheet
        glDepthMask(GL_FALSE)
        glEnable(GL_BLEND)
        glBindTexture(GL_TEXTURE_2D, self.sheet_texture)
        glColor4f(0.0, 0.0, 0.0, 1.0)
        glVertexPointer(3, GL_FLOAT, 0, sheet.positions_at(morph))
        glTexCoordPointer(2, GL_FLOAT, 0, sheet.uv)
        glDrawElements(GL_TRIANGLES, len(sheet.triangles), GL_UNSIGNED_INT, sheet.triangles)
        glDepthMask(GL_TRUE)
        glDisableClientState(GL_TEXTURE_COORD_ARRAY)
        glDisableClientState(GL_VERTEX_ARRAY)
        glDisable(GL_TEXTURE_2D)
        glDisable(GL_DEPTH_TEST)

    # ----------------------------------------------------------- captions

    def _caption_texture(self, text, font):
        key = (text, id(font))
        if key not in self.caption_textures:
            surface = font.render(text, True, [int(255 * c) for c in self.ink_color])
            pixels = pygame.image.tobytes(surface, "RGBA", True)
            texture = glGenTextures(1)
            glBindTexture(GL_TEXTURE_2D, texture)
            glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, surface.get_width(), surface.get_height(), 0,
                         GL_RGBA, GL_UNSIGNED_BYTE, pixels)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
            self.caption_textures[key] = (texture, surface.get_width(), surface.get_height())
        return self.caption_textures[key]

    def draw_caption(self, title, detail, alpha):
        if alpha <= 0.0 or not (title or detail):
            return
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0, self.screen_width, 0, self.screen_height, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glDisable(GL_DEPTH_TEST)
        glEnable(GL_BLEND)
        glEnable(GL_TEXTURE_2D)
        margin = self.screen_height // 24
        top = self.screen_height - margin
        for text, font in ((title, self.title_font), (detail, self.detail_font)):
            if not text:
                continue
            texture, width, height = self._caption_texture(text, font)
            top -= height
            glBindTexture(GL_TEXTURE_2D, texture)
            glColor4f(1.0, 1.0, 1.0, alpha)
            glBegin(GL_QUADS)
            glTexCoord2f(0, 0); glVertex2f(margin, top)
            glTexCoord2f(1, 0); glVertex2f(margin + width, top)
            glTexCoord2f(1, 1); glVertex2f(margin + width, top + height)
            glTexCoord2f(0, 1); glVertex2f(margin, top + height)
            glEnd()
            top -= height // 3
        glDisable(GL_TEXTURE_2D)
