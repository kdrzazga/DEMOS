import pygame
from pygame.locals import DOUBLEBUF, KEYDOWN, K_ESCAPE, K_SPACE, OPENGL, QUIT
from OpenGL.GL import (
    GL_COLOR_BUFFER_BIT,
    GL_DEPTH_BUFFER_BIT,
    GL_DEPTH_TEST,
    GL_LINEAR,
    GL_MODELVIEW,
    GL_PROJECTION,
    GL_QUADS,
    GL_RGBA,
    GL_TEXTURE_2D,
    GL_TEXTURE_MAG_FILTER,
    GL_TEXTURE_MIN_FILTER,
    GL_UNSIGNED_BYTE,
    glBegin,
    glBindTexture,
    glClear,
    glClearColor,
    glColor3f,
    glDisable,
    glEnable,
    glEnd,
    glGenTextures,
    glLoadIdentity,
    glMatrixMode,
    glOrtho,
    glPopMatrix,
    glPushMatrix,
    glRotatef,
    glTexCoord2f,
    glTexImage2D,
    glTexParameteri,
    glTranslatef,
    glVertex2f,
    glVertex3f,
)
from OpenGL.GLU import gluPerspective

from demos.petscii.files.kna_logo import KnaLogo
from demos.petscii.files.noise import Noise


class App:
    """PETSCII demo: a 3D animation that can also show 2D scenes. It opens with 2D noise."""

    WIDTH = 1150
    HEIGHT = 700
    FPS = 25
    NOISE_SECONDS = 6

    SCENE_NOISE = 0
    SCENE_CUBE = 1

    def __init__(self):
        pygame.init()
        pygame.display.set_mode((App.WIDTH, App.HEIGHT), DOUBLEBUF | OPENGL)
        pygame.display.set_caption("PETSCII")
        self.clock = pygame.time.Clock()
        self.running = True
        self.frame = 0
        self.scene = App.SCENE_NOISE

        glClearColor(0.0, 0.0, 0.0, 1.0)
        glEnable(GL_TEXTURE_2D)
        glEnable(GL_DEPTH_TEST)

        self.surface = pygame.Surface((App.WIDTH, App.HEIGHT))
        self.noise = Noise(App.WIDTH, App.HEIGHT)
        self.texture = glGenTextures(1)

        self.logo = KnaLogo()

    def run(self):
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            pygame.display.flip()
            self.clock.tick(App.FPS)
        pygame.quit()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == QUIT:
                self.running = False
            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    self.running = False
                elif event.key == K_SPACE:
                    self.scene ^= 1

    def update(self):
        self.frame += 1
        if self.scene == App.SCENE_NOISE and self.frame > App.FPS * App.NOISE_SECONDS:
            self.scene = App.SCENE_CUBE

    def draw(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        if self.scene == App.SCENE_NOISE:
            self.draw_noise()
        else:
            self.draw_cube()

    def draw_noise(self):
        self.noise.render(self.surface)
        if self.frame > 60:
            print(self.frame)
            self.logo.render(self.surface, transparent_space=True)
        self.draw_surface(self.surface)

    def draw_surface(self, surface):
        """Display a pygame surface as a full-screen quad (the 2D rendering path)."""
        data = pygame.image.tobytes(surface, "RGBA")
        glBindTexture(GL_TEXTURE_2D, self.texture)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, surface.get_width(), surface.get_height(),
                     0, GL_RGBA, GL_UNSIGNED_BYTE, data)

        self._begin_2d()
        glColor3f(1.0, 1.0, 1.0)
        glBegin(GL_QUADS)
        glTexCoord2f(0, 0); glVertex2f(0, 0)
        glTexCoord2f(1, 0); glVertex2f(App.WIDTH, 0)
        glTexCoord2f(1, 1); glVertex2f(App.WIDTH, App.HEIGHT)
        glTexCoord2f(0, 1); glVertex2f(0, App.HEIGHT)
        glEnd()
        self._end_2d()

    def draw_cube(self):
        """Rotating cube (the 3D rendering path)."""
        glDisable(GL_TEXTURE_2D)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45, App.WIDTH / App.HEIGHT, 0.1, 50.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glTranslatef(0.0, 0.0, -6.0)
        glRotatef(self.frame * 2, 1, 1, 0)
        self._render_cube()
        glEnable(GL_TEXTURE_2D)

    def _begin_2d(self):
        glDisable(GL_DEPTH_TEST)
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(0, App.WIDTH, App.HEIGHT, 0, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()

    def _end_2d(self):
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glPopMatrix()
        glEnable(GL_DEPTH_TEST)

    VERTICES = (
        (1, -1, -1), (1, 1, -1), (-1, 1, -1), (-1, -1, -1),
        (1, -1, 1), (1, 1, 1), (-1, -1, 1), (-1, 1, 1),
    )
    FACES = (
        (0, 1, 2, 3), (3, 2, 7, 6), (6, 7, 5, 4),
        (4, 5, 1, 0), (1, 5, 7, 2), (4, 0, 3, 6),
    )
    FACE_COLORS = (
        (0.8, 0.2, 0.2), (0.2, 0.8, 0.2), (0.2, 0.2, 0.8),
        (0.8, 0.8, 0.2), (0.8, 0.2, 0.8), (0.2, 0.8, 0.8),
    )

    def _render_cube(self):
        glBegin(GL_QUADS)
        for color, face in zip(App.FACE_COLORS, App.FACES):
            glColor3f(*color)
            for vertex in face:
                glVertex3f(*App.VERTICES[vertex])
        glEnd()
