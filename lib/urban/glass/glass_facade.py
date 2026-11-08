from OpenGL.GL import (
    GL_AMBIENT_AND_DIFFUSE,
    GL_COLOR_MATERIAL,
    GL_COMPILE,
    GL_EMISSION,
    GL_ENABLE_BIT,
    GL_FRONT_AND_BACK,
    GL_LIGHTING,
    GL_LIGHTING_BIT,
    GL_SHININESS,
    GL_SPECULAR,
    glCallList,
    glColorMaterial,
    glEnable,
    glEndList,
    glGenLists,
    glMaterialf,
    glMaterialfv,
    glNewList,
    glPopAttrib,
    glPushAttrib,
)

from lib.three_mirrors.mirror import Mirror


class GlassFacade:

    def __init__(self, origin, across, up, columns, rows, style, randomness):
        self.style = style
        self.plane = Mirror(origin, across, up)
        self.plane.set_blur(style.blur)
        self.columns = columns
        self.rows = rows
        self.panes = []
        self.lit_panes = set()
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
            self.lit_panes.add(pane)
            return
        brightness = 1.0 + randomness.uniform(-style.tint_variation, style.tint_variation)
        red, green, blue = (channel * brightness for channel in style.pane_tint)
        pane.apply_custom_shade(red, green, blue, style.pane_opacity)

    def set_blur(self, blur):
        self.plane.set_blur(blur)

    @property
    def blur(self):
        return self.plane.blur

    def corners(self):
        return self.plane.corners()

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

    def draw_shape(self):
        if self.shape_list is None:
            self.shape_list = self._compile(self._emit_shapes)
        glCallList(self.shape_list)

    def draw_glass(self):
        if self.glass_list is None:
            self.glass_list = self._compile(self._emit_glass)
        glPushAttrib(GL_ENABLE_BIT | GL_LIGHTING_BIT)
        glEnable(GL_LIGHTING)
        glEnable(GL_COLOR_MATERIAL)
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
        glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, self.style.specular)
        glMaterialf(GL_FRONT_AND_BACK, GL_SHININESS, self.style.shininess)
        glCallList(self.glass_list)
        glPopAttrib()

    def _emit_shapes(self):
        for pane in self.panes:
            pane.draw_shape()

    def _emit_glass(self):
        for pane in self.panes:
            if pane in self.lit_panes:
                glMaterialfv(GL_FRONT_AND_BACK, GL_EMISSION, self.style.lit_pane_glow)
                pane.draw_glass()
                glMaterialfv(GL_FRONT_AND_BACK, GL_EMISSION, self.style.no_glow)
            else:
                pane.draw_glass()

    def _compile(self, emit):
        list_id = glGenLists(1)
        glNewList(list_id, GL_COMPILE)
        emit()
        glEndList()
        return list_id
