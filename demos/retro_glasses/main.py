import os

import pygame
from OpenGL.GL import *

from lib.pygame_demo import PygameDemo
from lib import Globals
from demos.retro_glasses.actors import DemoHead, SkinMesh, StageBall
from demos.retro_glasses.credits import Credits
from demos.retro_glasses.graffiti_intro import GraffitiIntro
from demos.retro_glasses.left_lens import LeftLens, LeftLensStage
from demos.retro_glasses.pulse_backdrop import PulseBackdrop
from demos.retro_glasses.models3d.lesson11_talking_face import (
    LipShapes, Speech)
from demos.retro_glasses.stage_view import (
    Pose, ScreenOverlay, SpeechSubtitles, StageCamera, WelcomeText)
from demos.retro_glasses.stages import (
    BackStage, BallStage, CreditsStage, DetailsStage, FaceStage, FinalTalkStage, GraffitiIntroStage,
    MeshStage, OrbitStage, OvalStage, SecondBallStage, StageTimeline,
    SunglassesStage, TalkStage, WelcomeStage, ZoomStage)


class Soundtrack:
    def __init__(self):
        self.path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "resources", "sounds",
            #"ElectricElwizz - We Rise Through Fire (Electro Freestyle).mp3")
            "Cleo.mp3") #Atrox 'Cleopatraz Castle'
        self.volume = 1.0
        self.start_seconds = 52.0

    def start(self):
        pygame.mixer.music.load(self.path)
        pygame.mixer.music.set_volume(self.volume)
        pygame.mixer.music.play(loops=0, start=self.start_seconds)

    def current_volume(self):
        return pygame.mixer.music.get_volume()

    def set_volume(self, volume):
        pygame.mixer.music.set_volume(volume)

    def fade_out(self, seconds):
        pygame.mixer.music.fadeout(int(seconds * 1000))


class Show:
    def __init__(self, screen_width, screen_height):
        self.soundtrack = Soundtrack()
        self.playback_speed = 2.0
        self.camera = StageCamera(screen_width, screen_height)
        self.overlay = ScreenOverlay(screen_width, screen_height)
        self.welcome = WelcomeText()
        self.subtitles = SpeechSubtitles()
        self.pulse_backdrop = PulseBackdrop(screen_width, screen_height)
        self.graffiti_intro = GraffitiIntro(screen_width, screen_height)
        self.credits = Credits(screen_width, screen_height)
        self.pose = Pose()
        self.head = DemoHead(self.pose)
        self.head.prepare_hair()
        self.left_lens = LeftLens(self.head)
        self.mesh = SkinMesh(self.head.front.skin_color,
                             self.head.front.line_color)
        self.balls = [StageBall((-3.0, 1.3, 0.0), 0.45),
                      StageBall((3.0, 1.3, 0.0), 0.45)]
        self.words = [
            ("condition", ["con", "di", "tion"]),
            ("exited", ["ex", "i", "ed"]),
            ("deter", ["de", "ter"]),
            ("openly", ["o", "e", "ly"]),
            ("intercom", ["in", "ter", "com"]),
            ("happier", ["a", "y", "er"])]
        self.speech = Speech(LipShapes(), self.words)
        self.talking = False
        self.speech_ending = False
        self.balls_bobbing = True
        self.darkness = 0.0
        self.no_shine = (0.0, 0.0, 0.0, 1.0)
        self.time = 0.0

    def update(self, seconds):
        self.time += seconds
        self.camera.update(seconds)
        if self.balls_bobbing:
            for ball in self.balls:
                ball.bob(self.time)
        real_seconds = seconds / self.playback_speed
        self.head.update_sprouts(real_seconds)
        self.head.c64_screen.update(real_seconds)
        self.left_lens.update(real_seconds)
        self.pulse_backdrop.update(real_seconds)
        if self.talking:
            self.speech.update(seconds)
            if self.speech_ending and self.speech.current_slot()[1] is None:
                self.talking = False
                self.speech_ending = False
                self.head.front.shape_lips(*self.speech.lip_shapes.rest.pose)
            else:
                self.head.front.shape_lips(*self.speech.lip_pose())
            self.head.front.build()

    def stop_talking(self):
        self.speech_ending = True

    def draw(self):
        if self.graffiti_intro.active:
            self.graffiti_intro.draw()
            return
        self.left_lens.capture_tunnel()
        self.pulse_backdrop.clear_screen()
        self.camera.apply()
        self.pulse_backdrop.draw()
        glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, self.no_shine)
        for ball in self.balls:
            ball.draw()
        self.mesh.draw(self.pose)
        self.head.draw()
        self.left_lens.draw_escaping_ball()
        self.head.c64_animation.draw_unsync()
        self.overlay.begin()
        self.welcome.draw(self.overlay)
        self.subtitles.draw(self.overlay)
        self.credits.draw(self.overlay)
        self.overlay.darken(self.darkness)
        self.overlay.end()


class RetroGlasses(PygameDemo):
    def __init__(self, windowed=False, triggered=False):
        self.time = 0.0
        self.timeline = None
        self.show = None
        self.longest_frame = 0.1
        super().__init__(1280, 720, "Old and New", fps=60,
                         windowed=windowed, triggered=triggered)

    def setup(self):
        screen_width, screen_height = pygame.display.get_surface().get_size()
        glClearColor(0.0, 0.0, 0.0, 1.0)
        glEnable(GL_DEPTH_TEST)
        self.show = Show(screen_width, screen_height)
        self.timeline = StageTimeline([
            GraffitiIntroStage(self.show.graffiti_intro, self.show.playback_speed),
            WelcomeStage(), BallStage(), MeshStage(), FaceStage(),
            TalkStage(), OvalStage(), BackStage(), SecondBallStage(),
            DetailsStage(), SunglassesStage(), OrbitStage(),
            ZoomStage(self.show.head.c64_animation, self.show.playback_speed),
            LeftLensStage(), FinalTalkStage(self.show.playback_speed),
            CreditsStage(self.show.credits, self.show.playback_speed)])
        self.time = 0.0

    def step(self):
        real_seconds = min(self.clock.get_time() / 1000.0,
                           self.longest_frame)
        seconds = real_seconds * self.show.playback_speed
        self.time += seconds
        self.timeline.update(self.show, self.time)
        self.show.update(seconds)
        self.show.draw()
        if self.timeline.finished(self.time):
            print('Demo duration: ' + str(Globals.get_duration()))
            self.running = False


if __name__ == "__main__":
    RetroGlasses(windowed=True).run()
