import math
import os
import sys
import pygame
from OpenGL.GL import *
from OpenGL.GLU import *

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from demos.WinterDemo26.land import Land, FlattyLand
from demos.WinterDemo26.tree import Tree
from demos.WinterDemo26.snowman import Snowman
from demos.WinterDemo26.snow import Snow
from demos.WinterDemo26.igloo import Igloo
from demos.WinterDemo26.patch import GroundPatch
from demos.WinterDemo26.bonfire import Bonfire
from demos.WinterDemo26.christmas_robin import ChristmasRobin
from demos.WinterDemo26.cloud import Cloud
from demos.WinterDemo26.stars import Stars
from lib.backdrop import SpaceBackdrop
from lib.pygame_demo import PygameDemo
from demos.WinterDemo26.santa_ride import SantaRide


class WinterDemo(PygameDemo):
    def __init__(self, windowed=False, triggered=False):
        super().__init__(1100, 700, "3D Winter", fps=60, opengl=True,
                         windowed=windowed, triggered=triggered)

    def setup(self):
        self.sky_color = (0.66, 0.76, 0.86)
        self.tree_positions = ((-8.0, -4.0), (-5.5, 3.0), (6.5, -6.0), (9.0, 2.5),
                               (-10.0, -9.0), (3.0, 8.0), (-2.0, -11.0), (11.0, -1.0),
                               (-12.0, -14.0), (1.0, 13.0), (-4.0, -14.0), (12.0, -12.0))
        self.elapsed = 0.0
        self.sway_duration = 5.0
        self.travel_duration = 2.5
        self.settle_duration = 4.0
        self.enter_duration = 3.0
        self.igloo_show_duration = 6.0
        self.ascend_duration = 4.6
        self.hole_tilt_duration = 0.4
        self.hole_hold_duration = 0.5
        self.space_duration = 11.0
        self.ascend_top = 40.0
        self.space_color = (0.01, 0.01, 0.04)
        self.nebula_delay = 2.0
        self.nebula_fade = 2.5
        self.nebula_travel_speed = 90.0
        self.nebula_travel_cap = 700.0
        self.santa_delay = 2.0
        self.santa_approach = 6.0
        self.santa_size = 2.0
        self.santa_start_offset = (110.0, 100.0, 30.0)
        self.santa_end_offset = (18.0, 22.0, 6.0)
        self.snowman_end = self.sway_duration
        self.transition_end = self.snowman_end + self.travel_duration
        self.outside_end = self.transition_end + self.settle_duration
        self.enter_end = self.outside_end + self.enter_duration
        self.show_end = self.enter_end + self.igloo_show_duration
        self.hole_gaze_duration = self.hole_tilt_duration + self.hole_hold_duration
        self.ascend_end = self.show_end + self.hole_gaze_duration + self.ascend_duration
        self.space_end = self.ascend_end + self.space_duration
        self.nebula_start = self.ascend_end + self.nebula_delay
        self.santa_start = self.nebula_start + self.santa_delay
        self.eye = (0.0, 10.0, 26.0)
        self.target = (0.0, 3.0, 0.0)
        self.thanks_printed = False
        self._start_music()
        self._init_gl()
        self.land = Land(extent=80.0, resolution=144, seed=7)
        self.flatty_offset = (2.0 * self.land.extent, 0.0, 0.0)
        self.flatty_land = FlattyLand(extent=80.0, resolution=144, seed=11)
        self.trees = self._create_trees()
        self.snowman = Snowman(1.7, 0.0, self.land.surface_height(1.7, 0.0) - 0.6)
        self.igloo = Igloo(self.flatty_offset[0], self.flatty_offset[2],
                           self.flatty_land.surface_height(0.0, 0.0),
                           base_radius=3.5, layers_count=6)
        self.igloo_patch = GroundPatch(0.0, 0.0, self.igloo.base_radius * 4.0, self.flatty_land)
        self.bonfire = Bonfire(self.igloo.x, self.igloo.ground_height, self.igloo.z, scale=0.9,
                               smoke_fade_height=3.0 * self.igloo.base_radius)
        self.robins = self._create_robins()
        self.clouds = self._create_clouds()
        self.stars = Stars(seed=5)
        self.space_backdrop = SpaceBackdrop(self.width / self.height, fov=55.0)
        self.santa_ride = self._create_santa_ride()
        self.snow = Snow(220, (-22.0, 22.0, -20.0, 20.0, -1.5, 18.0))
        self.igloo_snow = Snow(200, (self.flatty_offset[0] - 22.0, self.flatty_offset[0] + 22.0,
                                     self.flatty_offset[2] - 20.0, self.flatty_offset[2] + 20.0,
                                     -1.5, 18.0), seed=123,
                               dome=(self.igloo.x, self.igloo.z, self.igloo.base_radius, self.igloo.ground_height))

    def _play_scene(self):
        time = self.elapsed
        if time <= self.snowman_end:
            self._snowman_scene()
        elif time <= self.transition_end:
            self._igloo_transition()
        elif time <= self.outside_end:
            self._igloo_approach()
        elif time <= self.enter_end:
            self._enter_igloo()
        elif time <= self.show_end:
            self._igloo_scene()
        elif time <= self.ascend_end:
            self._ascend_scene()
        elif time <= self.space_end:
            self._space_scene()
        else:
            self._finish()

    def _start_music(self):
        music_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dzisiaj.mp3")
        try:
            pygame.mixer.init()
            pygame.mixer.music.load(music_path)
            pygame.mixer.music.set_volume(1.0)
            pygame.mixer.music.play()
        except pygame.error:
            pass

    def _init_gl(self):
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glEnable(GL_COLOR_MATERIAL)
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
        glShadeModel(GL_SMOOTH)
        glEnable(GL_NORMALIZE)
        glLightfv(GL_LIGHT0, GL_DIFFUSE, (1.0, 0.98, 0.92, 1.0))
        glLightfv(GL_LIGHT0, GL_AMBIENT, (0.35, 0.40, 0.48, 1.0))
        glLightModelfv(GL_LIGHT_MODEL_AMBIENT, (0.35, 0.40, 0.48, 1.0))
        glEnable(GL_LIGHT1)
        glLightfv(GL_LIGHT1, GL_AMBIENT, (0.14, 0.07, 0.02, 1.0))
        glLightf(GL_LIGHT1, GL_CONSTANT_ATTENUATION, 1.0)
        glLightf(GL_LIGHT1, GL_LINEAR_ATTENUATION, 0.09)
        glLightf(GL_LIGHT1, GL_QUADRATIC_ATTENUATION, 0.032)
        glClearColor(self.sky_color[0], self.sky_color[1], self.sky_color[2], 1.0)
        glEnable(GL_FOG)
        glFogi(GL_FOG_MODE, GL_LINEAR)
        glFogfv(GL_FOG_COLOR, (self.sky_color[0], self.sky_color[1], self.sky_color[2], 1.0))
        glFogf(GL_FOG_START, 30.0)
        glFogf(GL_FOG_END, 80.0)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(55.0, self.width / self.height, 0.1, 220.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

    def _create_trees(self):
        trees = []
        for index, (x, z) in enumerate(self.tree_positions):
            ground = self.land.surface_height(x, z)
            trees.append(Tree(x, z, ground, snow_top=index % 3 != 0, seed=index + 1))
        return trees

    def _create_robins(self):
        placements = ((-1.45, 0.55, 1.0, 0.15, 1), (1.30, -0.35, 0.8, 0.85, 2))
        robins = []
        for offset_x, offset_z, size, hue, seed in placements:
            ground = self.flatty_land.surface_height(offset_x, offset_z) + self.igloo_patch.height_offset
            facing = math.degrees(math.atan2(-offset_x, -offset_z))
            robins.append(ChristmasRobin(self.bonfire.x + offset_x, self.bonfire.z + offset_z, ground,
                                         size=size, hue=hue, facing=facing, head_bob=True, seed=seed))
        return robins

    def _create_clouds(self):
        placements = ((-14.0, 24.0, -9.0, 5.0, 1), (12.0, 27.5, 8.0, 6.2, 2),
                      (-8.0, 31.0, 13.0, 4.4, 3), (16.0, 34.0, -12.0, 7.0, 4),
                      (-18.0, 37.0, 4.0, 5.6, 5), (6.0, 39.5, -16.0, 4.8, 6))
        clouds = []
        for offset_x, height, offset_z, size, seed in placements:
            clouds.append(Cloud(self.igloo.x + offset_x, height, self.igloo.z + offset_z, size=size, seed=seed))
        return clouds

    def _santa_anchor(self):
        return (self.igloo.x, self.ascend_top + 8.0, self.igloo.z)

    def _santa_waypoint(self, offset):
        anchor = self._santa_anchor()
        return (anchor[0] + offset[0], anchor[1] + offset[1], anchor[2] + offset[2])

    def _create_santa_ride(self):
        start = self._santa_waypoint(self.santa_start_offset)
        end = self._santa_waypoint(self.santa_end_offset)
        course = tuple(end[axis] - start[axis] for axis in range(3))
        flat = math.hypot(course[0], course[2])
        facing = math.degrees(math.atan2(course[0], course[2]))
        pitch = math.degrees(math.atan2(-course[1], flat))
        return SantaRide(start[0], start[1], start[2], size=self.santa_size,
                         facing=facing, pitch=pitch, bob=True, seed=4)

    def _santa_progress(self):
        return (self.elapsed - self.santa_start) / self.santa_approach

    def _place_santa(self, progress):
        start = self._santa_waypoint(self.santa_start_offset)
        end = self._santa_waypoint(self.santa_end_offset)
        self.santa_ride.x, self.santa_ride.y, self.santa_ride.z = self._lerp(start, end, self._clamp01(progress))

    def _nebula_travel(self):
        return min(self.nebula_travel_cap,
                   max(0.0, self.elapsed - self.nebula_start) * self.nebula_travel_speed)

    def _space_factor(self):
        return self._ease(self._clamp01((self.eye[1] - 28.0) / 24.0))

    def _nebula_factor(self):
        started = self.elapsed - self.ascend_end - self.nebula_delay
        return self._ease(self._clamp01(started / self.nebula_fade))

    def _clamp01(self, value):
        return max(0.0, min(1.0, value))

    def _ease(self, value):
        return value * value * (3.0 - 2.0 * value)

    def _sway_eye(self, moment):
        orbit = math.radians(35.0 * math.sin(moment * 0.25))
        radius = 26.0
        return (math.sin(orbit) * radius, 10.0, math.cos(orbit) * radius)

    def _lerp(self, start, end, factor):
        return tuple(start[axis] + (end[axis] - start[axis]) * factor for axis in range(3))

    def _outside_igloo_view(self, local_time):
        flatty_x, _, flatty_z = self.flatty_offset
        eye = (flatty_x - 12.0 + math.sin(local_time * 0.35) * 4.0,
               8.0,
               flatty_z + 15.0 + math.cos(local_time * 0.35) * 2.0)
        return eye, (flatty_x, 2.5, flatty_z)

    def _snowman_scene(self):
        self.eye = self._sway_eye(self.elapsed)
        self.target = (0.0, 3.0, 0.0)

    def _igloo_transition(self):
        progress = (self.elapsed - self.snowman_end) / self.travel_duration
        eased = progress * progress * (3.0 - 2.0 * progress)
        end_eye, end_target = self._outside_igloo_view(0.0)
        self.eye = self._lerp(self._sway_eye(self.snowman_end), end_eye, eased)
        self.target = self._lerp((0.0, 3.0, 0.0), end_target, eased)

    def _igloo_approach(self):
        self.eye, self.target = self._outside_igloo_view(self.elapsed - self.transition_end)

    def _enter_igloo(self):
        progress = (self.elapsed - self.outside_end) / self.enter_duration
        start_eye, _ = self._outside_igloo_view(self.settle_duration)
        self.eye, self.target = self.igloo.enter_igloo(start_eye, progress)

    def _igloo_inside_view(self):
        start_eye, _ = self._outside_igloo_view(self.settle_duration)
        return self.igloo.enter_igloo(start_eye, 1.0)

    def _igloo_scene(self):
        self.eye, self.target = self._igloo_inside_view()

    def _skyward_target(self, eye, spin):
        yaw = math.radians(-90.0 + spin * 55.0)
        return (eye[0] + math.cos(yaw) * 6.0, eye[1] + 10.0, eye[2] + math.sin(yaw) * 6.0)

    def _hole_position(self):
        return (self.igloo.x, self.igloo.ground_height + self.igloo.base_radius, self.igloo.z)

    def _hole_gaze_view(self, local_time):
        inside_eye, inside_target = self._igloo_inside_view()
        tilt = self._ease(self._clamp01(local_time / self.hole_tilt_duration))
        return inside_eye, self._lerp(inside_target, self._hole_position(), tilt)

    def _ascend_view(self, progress):
        start_eye, _ = self._igloo_inside_view()
        centering = self._ease(self._clamp01(progress / 0.30))
        eye = (start_eye[0] + (self.igloo.x - start_eye[0]) * centering,
               start_eye[1] + (self.ascend_top - start_eye[1]) * progress,
               start_eye[2] + (self.igloo.z - start_eye[2]) * centering)
        skyward = self._skyward_target(eye, progress)
        return eye, self._lerp(self._hole_position(), skyward, self._ease(self._clamp01(progress / 0.22)))

    def _space_view(self, progress):
        eye = (self.igloo.x, self.ascend_top + progress * 16.0, self.igloo.z)
        return eye, self._skyward_target(eye, 1.0 + progress * 1.6)

    def _ascend_scene(self):
        local_time = self.elapsed - self.show_end
        if local_time <= self.hole_gaze_duration:
            self.eye, self.target = self._hole_gaze_view(local_time)
        else:
            rise = (local_time - self.hole_gaze_duration) / self.ascend_duration
            self.eye, self.target = self._ascend_view(self._clamp01(rise))

    def _space_scene(self):
        self.eye, self.target = self._space_view(self._clamp01((self.elapsed - self.ascend_end) / self.space_duration))

    def _finish(self):
        self.eye, self.target = self._space_view(1.0)
        if not self.thanks_printed:
            print("thanks for watching")
            self.thanks_printed = True

    def _place_camera(self):
        gluLookAt(self.eye[0], self.eye[1], self.eye[2],
                  self.target[0], self.target[1], self.target[2], 0.0, 1.0, 0.0)

    def _draw(self):
        space_factor = self._space_factor()
        sky = self._lerp(self.sky_color, self.space_color, space_factor)
        glClearColor(sky[0], sky[1], sky[2], 1.0)
        glFogfv(GL_FOG_COLOR, (sky[0], sky[1], sky[2], 1.0))
        glFogf(GL_FOG_END, 80.0 + 180.0 * space_factor)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        self._place_camera()
        self.space_backdrop.draw(self._nebula_factor(), self.eye, self.target, self._nebula_travel())
        self.stars.draw(space_factor, self.eye)
        glLightfv(GL_LIGHT0, GL_POSITION, (0.5, 1.0, 0.6, 0.0))
        glow = self.bonfire.glow_intensity()
        glLightfv(GL_LIGHT1, GL_POSITION, self.bonfire.light_position())
        glLightfv(GL_LIGHT1, GL_DIFFUSE, (glow, 0.5 * glow, 0.18 * glow, 1.0))
        self.land.draw()
        glPushMatrix()
        glTranslatef(*self.flatty_offset)
        self.flatty_land.draw()
        self.igloo_patch.draw()
        glPopMatrix()
        for cloud in self.clouds:
            cloud.draw()
        for tree in self.trees:
            tree.draw()
        self.snowman.draw()
        self.igloo.draw(glow)
        for robin in self.robins:
            robin.draw()
        self.bonfire.draw()
        santa_progress = self._santa_progress()
        if santa_progress >= 0.0:
            self._place_santa(santa_progress)
            self.santa_ride.draw()
        self.snow.draw()
        self.igloo_snow.draw()

    def on_pause(self):
        try:
            pygame.mixer.music.pause()
        except pygame.error:
            pass

    def on_start(self):
        try:
            pygame.mixer.music.unpause()
        except pygame.error:
            pass

    def step(self):
        delta_seconds = self.clock.get_time() / 1000.0
        self.elapsed += delta_seconds
        self.snow.update(delta_seconds)
        self.igloo_snow.update(delta_seconds)
        self.bonfire.update(delta_seconds)
        for robin in self.robins:
            robin.update(delta_seconds)
        self.santa_ride.update(delta_seconds)
        self._play_scene()
        self.space_backdrop.update(self.elapsed, self._nebula_factor())
        self._draw()


def main():
    args = [arg.lower() for arg in sys.argv[1:]]
    windowed = any(arg in ("w", "window", "windowed") for arg in args)
    triggered = any(arg in ("t", "trigger", "triggered") for arg in args)
    WinterDemo(windowed=windowed, triggered=triggered).run()


if __name__ == "__main__":
    main()
