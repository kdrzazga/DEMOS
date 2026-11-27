import math
import os
import sys

import numpy
import pygame
from pygame.locals import DOUBLEBUF, OPENGL, QUIT, KEYDOWN, K_ESCAPE, K_r, MOUSEBUTTONDOWN, MOUSEBUTTONUP, MOUSEMOTION
from OpenGL.GL import *

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from lib.urban.manger.glb_scene import (GlbScene, ShaderProgram, SunShadow, SCENE_VERTEX_SHADER,
                                        SCENE_FRAGMENT_SHADER, SHADOW_VERTEX_SHADER, SHADOW_FRAGMENT_SHADER,
                                        look_at, perspective)


class MangerTest:

    def __init__(self):
        self.width = 1280
        self.height = 720
        self.scene_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "urban", "manger",
                                                       "manger.glb"))
        self.ambient = (0.03, 0.026, 0.034)
        self.exposure = 1.0
        self.max_point_lights = 8
        self.shadow_map_size = 4096
        self.shadow_half_size = 22.0
        self.shadow_center = (-3.0, 0.0, -7.0)
        self.shadow_distance = 80.0
        self.walk_speed = 2.5
        self.sprint_factor = 5.0
        self.look_sensitivity = 0.004
        self.near_plane = 0.05
        self.far_plane = 1200.0
        self.vertical_fov = math.radians(50.0)
        self.dragging = False
        self.clock = pygame.time.Clock()
        pygame.init()
        pygame.display.gl_set_attribute(pygame.GL_MULTISAMPLEBUFFERS, 1)
        pygame.display.gl_set_attribute(pygame.GL_MULTISAMPLESAMPLES, 4)
        pygame.display.set_mode((self.width, self.height), DOUBLEBUF | OPENGL)
        pygame.display.set_caption("Manger GLB Test - drag to look, WASD/QE to move, Shift faster, R resets view")
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_MULTISAMPLE)
        glDisable(GL_CULL_FACE)
        glClearColor(0.01, 0.014, 0.035, 1.0)
        self.scene = GlbScene(self.scene_path)
        self.scene_program = ShaderProgram(SCENE_VERTEX_SHADER, SCENE_FRAGMENT_SHADER, ("position", "normal", "uv"))
        self.shadow_program = ShaderProgram(SHADOW_VERTEX_SHADER, SHADOW_FRAGMENT_SHADER, ("position",))
        self.shadow = SunShadow(self.shadow_map_size, self.shadow_half_size, self.shadow_center, self.shadow_distance)
        self.reset_view()

    def reset_view(self):
        if self.scene.camera:
            description, world = self.scene.camera
            self.vertical_fov = description.get("perspective", {}).get("yfov", self.vertical_fov)
            self.position = world[:3, 3].copy()
            forward = world[:3, :3] @ numpy.array((0.0, 0.0, -1.0))
        else:
            self.position = numpy.array((0.0, 1.6, 4.0))
            forward = numpy.array((0.0, 0.0, -1.0))
        self.yaw = math.atan2(forward[0], -forward[2])
        self.pitch = math.asin(max(-1.0, min(1.0, forward[1])))

    def view_direction(self):
        return numpy.array((math.sin(self.yaw) * math.cos(self.pitch), math.sin(self.pitch),
                            -math.cos(self.yaw) * math.cos(self.pitch)))

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
                return False
            if event.type == KEYDOWN and event.key == K_r:
                self.reset_view()
            elif event.type == MOUSEBUTTONDOWN and event.button == 1:
                self.dragging = True
            elif event.type == MOUSEBUTTONUP and event.button == 1:
                self.dragging = False
            elif event.type == MOUSEMOTION and self.dragging:
                self.yaw += event.rel[0] * self.look_sensitivity
                self.pitch = max(-1.5, min(1.5, self.pitch - event.rel[1] * self.look_sensitivity))
        return True

    def move(self, seconds):
        keys = pygame.key.get_pressed()
        forward = self.view_direction()
        right = numpy.array((math.cos(self.yaw), 0.0, math.sin(self.yaw)))
        step = numpy.zeros(3)
        step += forward * (keys[pygame.K_w] - keys[pygame.K_s])
        step += right * (keys[pygame.K_d] - keys[pygame.K_a])
        step[1] += keys[pygame.K_e] - keys[pygame.K_q]
        speed = self.walk_speed * (self.sprint_factor if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT] else 1.0)
        self.position += step * speed * seconds

    def render_shadow(self, light_matrix):
        glBindFramebuffer(GL_FRAMEBUFFER, self.shadow.framebuffer)
        glViewport(0, 0, self.shadow_map_size, self.shadow_map_size)
        glClear(GL_DEPTH_BUFFER_BIT)
        glEnable(GL_POLYGON_OFFSET_FILL)
        glPolygonOffset(2.0, 4.0)
        self.shadow_program.use()
        self.shadow_program.set_matrix("light_matrix", light_matrix)
        self.scene.draw(self.shadow_program, with_surface=False)
        glDisable(GL_POLYGON_OFFSET_FILL)
        glBindFramebuffer(GL_FRAMEBUFFER, 0)

    def render_scene(self, light_matrix, sun_direction, sun_irradiance):
        glViewport(0, 0, self.width, self.height)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        projection = perspective(self.vertical_fov, self.width / self.height, self.near_plane, self.far_plane)
        view = look_at(self.position, self.position + self.view_direction(), (0.0, 1.0, 0.0))
        program = self.scene_program
        program.use()
        program.set_matrix("view_projection", projection @ view)
        program.set_matrix("light_matrix", light_matrix)
        program.set_vector("sun_direction", sun_direction)
        program.set_vector("sun_irradiance", sun_irradiance)
        program.set_vector("ambient", self.ambient)
        program.set_float("exposure", self.exposure)
        program.set_float("shadow_texel", 1.0 / self.shadow_map_size)
        lights = self.scene.point_lights[:self.max_point_lights]
        program.set_int("point_count", len(lights))
        program.set_vectors("point_positions", [position for position, _ in lights])
        program.set_vectors("point_intensities", [intensity for _, intensity in lights])
        glActiveTexture(GL_TEXTURE2)
        glBindTexture(GL_TEXTURE_2D, self.shadow.texture)
        program.set_int("shadow_map", 2)
        glActiveTexture(GL_TEXTURE0)
        self.scene.draw(program)

    def run(self):
        if self.scene.sun:
            sun_direction, sun_irradiance = self.scene.sun
        else:
            sun_direction, sun_irradiance = numpy.array((0.0, 1.0, 0.0)), numpy.zeros(3)
        light_matrix = self.shadow.light_matrix(sun_direction)
        running = True
        while running:
            seconds = self.clock.tick(60) / 1000.0
            running = self.handle_events()
            self.move(seconds)
            self.render_shadow(light_matrix)
            self.render_scene(light_matrix, sun_direction, sun_irradiance)
            pygame.display.flip()
        pygame.quit()


def main():
    MangerTest().run()


if __name__ == "__main__":
    main()
