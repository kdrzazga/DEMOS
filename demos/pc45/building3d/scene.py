from OpenGL.GL import glPopMatrix, glPushMatrix, glRotatef


class Scene:
    def __init__(self, building, camera, renderer, building_spin_degrees_per_second=14.0):
        self.building = building
        self.camera = camera
        self.renderer = renderer
        self.building_spin_degrees_per_second = building_spin_degrees_per_second
        self.building_rotation_degrees = 0.0

    def update(self, elapsed_seconds):
        self.building_rotation_degrees += self.building_spin_degrees_per_second * elapsed_seconds

    def draw(self):
        self.camera.apply_view_transform()
        glPushMatrix()
        glRotatef(self.building_rotation_degrees, 0.0, 1.0, 0.0)
        self.building.render_using(self.renderer)
        glPopMatrix()
