from OpenGL.GL import GL_QUADS, glBegin, glColor3f, glEnd, glVertex3f


class LitSurfaceRenderer:
    def __init__(self, light_direction, ambient_intensity=0.34, diffuse_intensity=0.66):
        self.light_direction = light_direction.normalized()
        self.ambient_intensity = ambient_intensity
        self.diffuse_intensity = diffuse_intensity

    def compute_surface_brightness(self, corner_points):
        first_edge = corner_points[1].subtracted_by(corner_points[0])
        second_edge = corner_points[3].subtracted_by(corner_points[0])
        surface_normal = first_edge.cross_product_with(second_edge).normalized()
        light_alignment = abs(surface_normal.dot_product_with(self.light_direction))
        return self.ambient_intensity + self.diffuse_intensity * light_alignment

    def render_shaded_quad(self, corner_points, base_color):
        brightness = self.compute_surface_brightness(corner_points)
        glColor3f(base_color[0] * brightness, base_color[1] * brightness, base_color[2] * brightness)
        self.emit_quad_vertices(corner_points)

    def render_emissive_quad(self, corner_points, color):
        glColor3f(color[0], color[1], color[2])
        self.emit_quad_vertices(corner_points)

    def emit_quad_vertices(self, corner_points):
        glBegin(GL_QUADS)
        for point in corner_points:
            glVertex3f(point.x, point.y, point.z)
        glEnd()
