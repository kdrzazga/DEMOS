import numpy
from OpenGL.GL import (
    GL_AMBIENT_AND_DIFFUSE,
    GL_BLEND,
    GL_COLOR_ARRAY,
    GL_COLOR_BUFFER_BIT,
    GL_COLOR_MATERIAL,
    GL_COMPILE,
    GL_EMISSION,
    GL_ENABLE_BIT,
    GL_FLOAT,
    GL_FRONT_AND_BACK,
    GL_LIGHTING,
    GL_LIGHTING_BIT,
    GL_ONE_MINUS_SRC_ALPHA,
    GL_QUADS,
    GL_SHININESS,
    GL_SPECULAR,
    GL_SRC_ALPHA,
    GL_VERTEX_ARRAY,
    glBlendFunc,
    glCallList,
    glColorMaterial,
    glColorPointer,
    glDisableClientState,
    glDrawArrays,
    glEnable,
    glEnableClientState,
    glEndList,
    glGenLists,
    glMaterialf,
    glMaterialfv,
    glNewList,
    glNormal3f,
    glPopAttrib,
    glPushAttrib,
    glVertexPointer,
)

from lib.three_mirrors.mirror import Mirror


class PaneBatch:

    def __init__(self, panes):
        self.count = 4 * len(panes)
        self.positions = numpy.array([tuple(corner) for pane in panes for corner in pane.corners()],
                                     dtype=numpy.float32).reshape(-1, 3)
        self.colors = numpy.array([pane.glass_tint for pane in panes for _ in range(4)],
                                  dtype=numpy.float32).reshape(-1, 4)

    def is_empty(self):
        return self.count == 0

    def draw_outline(self):
        if self.is_empty():
            return
        glEnableClientState(GL_VERTEX_ARRAY)
        glVertexPointer(3, GL_FLOAT, 0, self.positions)
        glDrawArrays(GL_QUADS, 0, self.count)
        glDisableClientState(GL_VERTEX_ARRAY)

    def draw_tinted(self):
        if self.is_empty():
            return
        glEnableClientState(GL_VERTEX_ARRAY)
        glEnableClientState(GL_COLOR_ARRAY)
        glVertexPointer(3, GL_FLOAT, 0, self.positions)
        glColorPointer(4, GL_FLOAT, 0, self.colors)
        glDrawArrays(GL_QUADS, 0, self.count)
        glDisableClientState(GL_COLOR_ARRAY)
        glDisableClientState(GL_VERTEX_ARRAY)


class GlassFacade:

    def __init__(self, origin, across, up, columns, rows, style, randomness):
        self.style = style
        self.plane = Mirror(origin, across, up)
        self.plane.set_blur(style.blur)
        self.columns = columns
        self.rows = rows
        self.panes = []
        self.lit_panes = []
        self.dark_panes = []
        self.shape_list = None
        self.glass_list = None
        self._lay_panes(origin, across, up, randomness)

    def _lay_panes(self, origin, across, up, randomness):
        cell_across = across * (1.0 / self.columns)
        cell_up = up * (1.0 / self.rows)
        gap = self.style.mullion_gap
        across_gap = cell_across.normalized() * gap
        up_gap = cell_up.normalized() * gap
        for row in range(self.rows):
            for column in range(self.columns):
                cell_origin = origin + cell_across * column + cell_up * row
                pane = Mirror(cell_origin + across_gap * 0.5 + up_gap * 0.5,
                              cell_across - across_gap, cell_up - up_gap)
                self._shade_pane(pane, randomness)
                self.panes.append(pane)

    def _shade_pane(self, pane, randomness):
        style = self.style
        if randomness.random() < style.lit_pane_chance:
            pane.apply_custom_shade(*style.lit_pane_tint, style.lit_pane_opacity)
            self.lit_panes.append(pane)
            return
        brightness = 1.0 + randomness.uniform(-style.tint_variation, style.tint_variation)
        red, green, blue = (min(channel * brightness, 1.0) for channel in style.pane_tint)
        pane.apply_custom_shade(red, green, blue, style.pane_opacity)
        self.dark_panes.append(pane)

    def set_blur(self, blur):
        self.plane.set_blur(blur)

    @property
    def blur(self):
        return self.plane.blur

    def corners(self):
        return self.plane.corners()

    def plane_equation(self):
        return self.plane.plane_equation()

    def faces(self, point):
        return self.plane.faces(point)

    def reflect_point(self, point):
        return self.plane.reflect_point(point)

    def reflection_matrix(self):
        return self.plane.reflection_matrix()

    def behind_clip_plane(self):
        return self.plane.behind_clip_plane()

    def is_blurred(self):
        return self.plane.is_blurred()

    def blur_radius_pixels(self):
        return self.plane.blur_radius_pixels()

    def prepare(self):
        if self.shape_list is not None:
            return
        every_pane = PaneBatch(self.panes)
        self.shape_list = self._compile(lambda: self._emit_shape(every_pane))
        self.glass_list = self._compile(lambda: self._emit_glass(PaneBatch(self.dark_panes),
                                                                 PaneBatch(self.lit_panes)))

    def draw_shape(self):
        self.prepare()
        glCallList(self.shape_list)

    def draw_glass(self):
        self.prepare()
        glCallList(self.glass_list)

    def _emit_shape(self, batch):
        glNormal3f(*self.plane.normal)
        batch.draw_outline()

    def _emit_glass(self, dark_batch, lit_batch):
        glPushAttrib(GL_ENABLE_BIT | GL_LIGHTING_BIT | GL_COLOR_BUFFER_BIT)
        glEnable(GL_LIGHTING)
        glEnable(GL_COLOR_MATERIAL)
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
        glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, self.style.specular)
        glMaterialf(GL_FRONT_AND_BACK, GL_SHININESS, self.style.shininess)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glNormal3f(*self.plane.normal)
        dark_batch.draw_tinted()
        glMaterialfv(GL_FRONT_AND_BACK, GL_EMISSION, self.style.lit_pane_glow)
        lit_batch.draw_tinted()
        glMaterialfv(GL_FRONT_AND_BACK, GL_EMISSION, self.style.no_glow)
        glPopAttrib()

    def _compile(self, emit):
        list_id = glGenLists(1)
        glNewList(list_id, GL_COMPILE)
        emit()
        glEndList()
        return list_id
