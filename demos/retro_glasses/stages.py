import math
import os

import pygame

from lib import Globals
from lib.speech_lines import read_speech


def smooth(progress):
    return progress * progress * (3.0 - 2.0 * progress)


class Stage:
    def __init__(self, duration):
        self.duration = duration

    def phase(self, time, start, duration):
        return min(max((time - start) / duration, 0.0), 1.0)

    def eased(self, time, start, duration):
        return smooth(self.phase(time, start, duration))

    def turn_once(self, show, time, start, duration):
        show.pose.turn_degrees = 360.0 * self.eased(time, start, duration)

    def enter(self, show):
        pass

    def update(self, show, time):
        pass

    def exit(self, show):
        pass


class GraffitiIntroStage(Stage):
    def __init__(self, graffiti_intro, playback_speed):
        super().__init__(graffiti_intro.duration_seconds * playback_speed)
        self.playback_speed = playback_speed

    def enter(self, show):
        show.graffiti_intro.active = True

    def update(self, show, time):
        show.graffiti_intro.update(time / self.playback_speed)

    def exit(self, show):
        show.graffiti_intro.active = False


class WelcomeStage(Stage):
    def __init__(self):
        super().__init__(4.5)
        self.fade_duration = 0.8

    def enter(self, show):
        show.soundtrack.start()

    def update(self, show, time):
        fade_in = self.phase(time, 0.0, self.fade_duration)
        fade_out = self.phase(time, self.duration - self.fade_duration,
                              self.fade_duration)
        show.welcome.alpha = fade_in * (1.0 - fade_out)


class BallStage(Stage):
    def __init__(self):
        super().__init__(11.0)
        self.build_position = (0.0, 0.6, 0.0)
        self.build_radius = 1.0
        self.points_duration = 3.0
        self.cover_start = 3.5
        self.cover_duration = 2.5
        self.shading_time = 6.5
        self.move_start = 7.5
        self.travel_duration = 2.0
        self.travel_arc = 0.6

    def enter(self, show):
        show.welcome.alpha = 0.0
        show.camera.target_tilt = 20.0
        show.balls_bobbing = False
        first = show.balls[0]
        first.visible = True
        first.shaded = False
        first.point_share = 0.0
        first.cover_share = 0.0

    def update(self, show, time):
        first = show.balls[0]
        first.point_share = self.phase(time, 0.0, self.points_duration)
        first.cover_share = self.phase(time, self.cover_start,
                                       self.cover_duration)
        first.shaded = time >= self.shading_time
        first.glide(self.build_position, first.home, self.build_radius,
                    first.full_radius, self.travel_arc,
                    self.phase(time, self.move_start, self.travel_duration))
        show.balls_bobbing = time >= self.move_start + self.travel_duration


class MeshStage(Stage):
    def __init__(self):
        super().__init__(7.5)

    def enter(self, show):
        show.camera.target_tilt = 50.0
        show.mesh.visible = True
        show.mesh.surface.fill_alpha = 0.0

    def update(self, show, time):
        show.mesh.row_share = self.phase(time, 0.0, 2.5)
        show.mesh.column_share = self.phase(time, 2.5, 2.5)
        show.mesh.surface.fill_alpha = 0.15 * self.phase(time, 5.0, 1.5)
        self.turn_once(show, time, 0.0, self.duration)


class FaceStage(Stage):
    def __init__(self):
        super().__init__(14.0)
        self.fill_duration = 1.5
        self.group_starts = (4.5, 6.5, 8.5, 10.5, 12.0)
        self.group_duration = 1.5

    def update(self, show, time):
        if time < self.fill_duration:
            fill = self.phase(time, 0.0, self.fill_duration)
            show.mesh.surface.fill_alpha = 0.15 + 0.85 * fill
            show.mesh.set_wire_darkness(fill)
            return
        show.mesh.visible = False
        show.head.visible = True
        dome_share = self.eased(time, 2.0, 2.0)
        group_shares = [self.eased(time, start, self.group_duration)
                        for start in self.group_starts]
        show.head.growth.apply(dome_share, group_shares)
        self.turn_once(show, time, self.fill_duration,
                       self.duration - self.fill_duration)


class TalkStage(Stage):
    def __init__(self):
        super().__init__(8.0)

    def enter(self, show):
        show.talking = True

    def update(self, show, time):
        self.turn_once(show, time, 0.0, self.duration)


class OvalStage(Stage):
    def __init__(self):
        super().__init__(7.0)
        self.upright_start = 3.5
        self.upright_duration = 3.0

    def update(self, show, time):
        show.head.front.oval_share = self.eased(time, 0.0, 3.0)
        upright = self.eased(time, self.upright_start,
                             self.upright_duration)
        if time >= self.upright_start:
            show.camera.target_tilt = 12.0
        pose = show.pose
        pose.upright_degrees = 90.0 * upright
        pose.scale = 1.0 - 0.3 * upright
        pose.lift = 0.2 * upright


class BackStage(Stage):
    def __init__(self):
        super().__init__(10.0)

    def enter(self, show):
        show.head.show_back = True

    def update(self, show, time):
        show.head.set_back_depth(self.eased(time, 0.5, 2.5))
        self.turn_once(show, time, 3.5, 6.5)


class SecondBallStage(Stage):
    def __init__(self):
        super().__init__(3.0)
        self.entry_position = (7.0, 1.3, 0.0)
        self.travel_duration = 2.0
        self.travel_arc = 0.6

    def enter(self, show):
        show.balls_bobbing = False
        show.balls[1].visible = True

    def update(self, show, time):
        second = show.balls[1]
        second.glide(self.entry_position, second.home, second.full_radius,
                     second.full_radius, self.travel_arc,
                     self.phase(time, 0.0, self.travel_duration))


class DetailsStage(Stage):
    def __init__(self):
        super().__init__(17.0)
        self.jump_duration = 1.8
        self.arc_height = 1.2
        self.targets = []
        self.target_radius = 0.0
        self.zoom_start = 9.5
        self.zoom_duration = 2.5
        self.head_height = 2.3
        self.head_center_height = 0.25
        self.fill_share = 0.92
        self.start_distance = 0.0
        self.turn_start = 9.5
        self.turn_duration = 7.0
        self.talk_stop_requested = False
        self.wires_hidden = False

    def enter(self, show):
        show.pose.turn_degrees = 0.0
        show.balls_bobbing = False
        self.start_distance = show.camera.distance
        self.targets = show.head.eye_targets()
        self.target_radius = show.head.eye_world_radius()

    def update(self, show, time):
        head = show.head
        if time < self.jump_duration:
            progress = self.phase(time, 0.0, self.jump_duration)
            for ball, target in zip(show.balls, self.targets):
                ball.jump(target, self.target_radius, self.arc_height,
                          progress)
            return
        for ball in show.balls:
            ball.visible = False
        head.show_eyes = True
        head.set_eye_colors(self.eased(time, 2.0, 1.5),
                            self.eased(time, 3.5, 1.0))
        head.show_ears = True
        for ear in head.ears:
            ear.size = max(self.eased(time, 5.0, 1.5), 0.01)
        head.show_hair = time >= 7.0
        head.sprouting = time >= 9.0
        hair_share = self.phase(time, 7.0, 2.0)
        head.haircut.visible_count = round(
            head.haircut.hair_count * hair_share)
        self.zoom(show, self.eased(time, self.zoom_start,
                                   self.zoom_duration))
        self.turn_once(show, time, self.turn_start, self.turn_duration)
        if time >= self.turn_start and not self.wires_hidden:
            self.wires_hidden = True
            head.hide_wires()
        if time >= self.turn_start + self.turn_duration and not self.talk_stop_requested:
            self.talk_stop_requested = True
            show.stop_talking()

    def exit(self, show):
        show.head.sprouting = False

    def zoom(self, show, share):
        camera = show.camera
        close_distance = camera.distance_to_fill(self.head_height,
                                                 self.fill_share)
        camera.distance = (self.start_distance
                           + (close_distance - self.start_distance) * share)
        camera.focus_point = (0.0, self.head_center_height * share, 0.0)


class SunglassesStage(Stage):
    def __init__(self):
        super().__init__(12.0)
        self.start_lift = 1.5

    def enter(self, show):
        show.head.show_sunglasses = True

    def update(self, show, time):
        arrival = self.eased(time, 0.0, 2.5)
        show.head.sunglasses.lift = self.start_lift * (1.0 - arrival)
        self.turn_once(show, time, 3.0, 8.0)


class OrbitStage(Stage):
    def __init__(self):
        super().__init__(12.0)
        self.orbit_radius = 1.6
        self.orbit_duration = 8.0
        self.self_turns = 1.0
        self.screen_start = 8.5
        self.screen_fade = 1.0

    def enter(self, show):
        show.pose.orbit_center_z = -self.orbit_radius
        show.pose.turn_degrees = 0.0

    def update(self, show, time):
        travel = self.eased(time, 0.0, self.orbit_duration)
        show.pose.orbit_degrees = 360.0 * travel
        show.pose.turn_degrees = 360.0 * self.self_turns * travel
        show.head.screen_lens.screen_share = self.phase(
            time, self.screen_start, self.screen_fade)


class ZoomStage(Stage):
    def __init__(self, c64_animation, playback_speed):
        self.zoom_duration = 6.0
        self.spinning_before_zoom_out = 5.0
        self.zoom_out_duration = 6.0
        self.hold_after_zoom_out = 4.0
        self.zoom_out_start = ((c64_animation.picture_start
                                + self.spinning_before_zoom_out)
                               * playback_speed)
        zoom_out_end = (self.zoom_out_start + self.zoom_out_duration
                        + self.hold_after_zoom_out)
        super().__init__(max(c64_animation.duration * playback_speed,
                             zoom_out_end))
        self.fill_share = 0.95
        self.start_distance = 0.0
        self.close_distance = 0.0
        self.start_focus = (0.0, 0.0, 0.0)
        self.screen_focus = (0.0, 0.0, 0.0)

    def enter(self, show):
        print("stage C= start -", Globals.get_duration())
        show.head.c64_screen.restart_typing()
        camera = show.camera
        camera.target_tilt = 0.0
        self.start_distance = camera.distance
        self.start_focus = camera.focus_point
        self.screen_focus = show.head.screen_center()
        self.close_distance = camera.distance_to_fill(
            show.head.screen_height(), self.fill_share)

    def update(self, show, time):
        zoom_in = self.eased(time, 0.0, self.zoom_duration)
        zoom_out = self.eased(time, self.zoom_out_start,
                              self.zoom_out_duration)
        share = zoom_in * (1.0 - zoom_out)
        camera = show.camera
        distance_ratio = self.close_distance / self.start_distance
        camera.distance = self.start_distance * distance_ratio ** share
        camera.focus_point = tuple(
            start + (screen - start) * share
            for start, screen in zip(self.start_focus, self.screen_focus))

    def exit(self, show):
        print("stage C= end -", Globals.get_duration())


class FinalTalkStage(Stage):
    def __init__(self, playback_speed):
        self.playback_speed = playback_speed
        sounds_directory = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources", "sounds")
        self.first_voice = pygame.mixer.Sound(os.path.join(sounds_directory, "compare1.mp3"))
        self.second_voice = pygame.mixer.Sound(os.path.join(sounds_directory, "compare2.mp3"))
        self.first_speech = read_speech(os.path.join(sounds_directory, "compare1.srt"))
        self.second_speech = read_speech(os.path.join(sounds_directory, "compare2.srt"))
        self.second_voice_start = 7.5
        self.talk_end = self.second_voice_start + self.second_voice.get_length()
        self.trailing_silence = 0.5
        self.head_shift_duration = 1.0
        self.head_width_with_ears_and_hair = 1.35
        self.screen_edge_margin = 0.03
        self.target_focus_x = 0.0
        self.music_volume_drop = 0.5
        self.music_volume_duration = 1.0
        self.second_voice_started = False
        self.talk_stop_requested = False
        self.start_focus = (0.0, 0.0, 0.0)
        super().__init__((self.talk_end + self.trailing_silence) * playback_speed)

    def enter(self, show):
        self.start_focus = show.camera.focus_point
        self.target_focus_x = self.focus_x_with_head_at_left_edge(show)
        show.pulse_backdrop.start()
        self.first_voice.play()
        show.subtitles.show(self.first_speech)
        show.talking = True

    def update(self, show, time):
        real_time = time / self.playback_speed
        shift = self.eased(real_time, 0.0, self.head_shift_duration)
        focus_x, focus_y, focus_z = self.start_focus
        show.camera.focus_point = (focus_x + (self.target_focus_x - focus_x) * shift, focus_y, focus_z)
        volume_drop = self.phase(real_time, 0.0, self.music_volume_duration)
        show.soundtrack.set_volume(show.soundtrack.volume * (1.0 - self.music_volume_drop * volume_drop))
        if real_time >= self.second_voice_start and not self.second_voice_started:
            self.second_voice_started = True
            self.second_voice.play()
            show.subtitles.show(self.second_speech)
        if real_time >= self.talk_end and not self.talk_stop_requested:
            self.talk_stop_requested = True
            show.stop_talking()
            show.subtitles.hide()

    def focus_x_with_head_at_left_edge(self, show):
        camera = show.camera
        aspect = camera.screen_width / camera.screen_height
        half_view_width = camera.distance * math.tan(math.radians(camera.field_of_view / 2.0)) * aspect
        head_half_width = (show.head.front.head_half_width * show.pose.scale
                           * self.head_width_with_ears_and_hair)
        head_center_on_view = -half_view_width * (1.0 - 2.0 * self.screen_edge_margin) + head_half_width
        return -head_center_on_view


class CreditsStage(Stage):
    def __init__(self, caption_letter_count, playback_speed):
        self.playback_speed = playback_speed
        self.head_drop_duration = 1.2
        self.head_drop_distance = 9.0
        self.thanks_fade_start = 0.4
        self.thanks_fade_duration = 0.8
        self.typing_start = 1.4
        self.letters_per_second = 14.0
        self.typing_duration = caption_letter_count / self.letters_per_second
        self.logo_start = self.typing_start + self.typing_duration + 0.3
        self.logo_fade_duration = 0.4
        self.hold_duration = 4.0
        self.music_fade = 1.5
        self.music_fading = False
        self.head_start_lift = 0.0
        real_duration = self.logo_start + self.logo_fade_duration + self.hold_duration
        super().__init__(real_duration * playback_speed)

    def enter(self, show):
        print('Final stage ' + str(Globals.get_duration()))
        show.darkness = 0.0
        show.credits.visible = True
        self.head_start_lift = show.pose.lift

    def update(self, show, time):
        real_time = time / self.playback_speed
        drop = self.phase(real_time, 0.0, self.head_drop_duration)
        show.pose.lift = self.head_start_lift - self.head_drop_distance * drop * drop
        show.head.visible = drop < 1.0
        show.credits.type_letters(int((real_time - self.typing_start) * self.letters_per_second))
        show.credits.logo_alpha = self.phase(real_time, self.logo_start, self.logo_fade_duration)
        show.credits.thanks_picture.alpha = self.phase(real_time, self.thanks_fade_start, self.thanks_fade_duration)
        real_duration = self.duration / self.playback_speed
        if real_time >= real_duration - self.music_fade and not self.music_fading:
            self.music_fading = True
            show.soundtrack.fade_out(self.music_fade)


class StageTimeline:
    def __init__(self, stages):
        self.stages = stages
        self.current_index = -1

    @property
    def total_duration(self):
        return sum(stage.duration for stage in self.stages)

    def locate(self, time):
        stage_start = 0.0
        for index, stage in enumerate(self.stages):
            if time < stage_start + stage.duration:
                return index, time - stage_start
            stage_start += stage.duration
        last = len(self.stages) - 1
        return last, self.stages[last].duration

    def update(self, show, time):
        index, stage_time = self.locate(time)
        while self.current_index < index:
            if self.current_index >= 0:
                finished_stage = self.stages[self.current_index]
                finished_stage.update(show, finished_stage.duration)
                finished_stage.exit(show)
            self.current_index += 1
            self.stages[self.current_index].enter(show)
        self.stages[index].update(show, stage_time)

    def finished(self, time):
        return time >= self.total_duration
