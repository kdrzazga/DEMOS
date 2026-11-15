from OpenGL.GL import (
    GL_MODELVIEW,
    GL_TEXTURE,
    glLoadIdentity,
    glMatrixMode,
    glPopMatrix,
    glPushMatrix,
    glScalef,
    glTranslatef,
)


class ReadableTexturing:

    def __enter__(self):
        glMatrixMode(GL_TEXTURE)
        glPushMatrix()
        glLoadIdentity()
        glTranslatef(1.0, 0.0, 0.0)
        glScalef(-1.0, 1.0, 1.0)
        glMatrixMode(GL_MODELVIEW)
        return self

    def __exit__(self, error_type, error, traceback):
        glMatrixMode(GL_TEXTURE)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        return False


class SceneMirror:

    def mirror_projection(self):
        glScalef(-1.0, 1.0, 1.0)

    def readable_texturing(self):
        return ReadableTexturing()

    def unflip_signs(self, sign_field):
        corners_per_sign = sign_field.texture_corners.reshape(-1, 4, 2)
        corners_per_sign[:, :, 0] = corners_per_sign[:, (1, 0, 3, 2), 0]
