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


class WelcomeStage(Stage):
    def __init__(self):
        super().__init__(4.5)
        self.fade_duration = 0.8

    def update(self, show, time):
        fade_in = self.phase(time, 0.0, self.fade_duration)
        fade_out = self.phase(time, self.duration - self.fade_duration,
                              self.fade_duration)
        show.welcome.alpha = fade_in * (1.0 - fade_out)


class BallStage(Stage):
    def __init__(self):
        super().__init__(3.0)

    def enter(self, show):
        show.welcome.alpha = 0.0
        show.camera.target_tilt = 20.0
        for ball in show.balls:
            ball.visible = True

    def update(self, show, time):
        for ball in show.balls:
            ball.size = self.eased(time, 0.0, 1.5)


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


class DetailsStage(Stage):
    def __init__(self):
        super().__init__(17.0)
        self.jump_duration = 1.8
        self.arc_height = 1.2
        self.targets = []
        self.target_radius = 0.0

    def enter(self, show):
        show.pose.turn_degrees = 0.0
        show.balls_bobbing = False
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
        hair_share = self.phase(time, 7.0, 2.0)
        head.haircut.visible_count = round(
            head.haircut.hair_count * hair_share)
        self.turn_once(show, time, 9.5, 7.0)


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


class EndingStage(Stage):
    def __init__(self):
        super().__init__(3.0)

    def update(self, show, time):
        show.darkness = self.phase(time, 0.0, self.duration)


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
            self.current_index += 1
            self.stages[self.current_index].enter(show)
        self.stages[index].update(show, stage_time)

    def finished(self, time):
        return time >= self.total_duration
