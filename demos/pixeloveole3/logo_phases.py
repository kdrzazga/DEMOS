from lib.demo_phases import CameraInterpolationHelper, DemoPhase


class LogoShowPhase(DemoPhase):
    """A timed step of the logo show. Subclasses kick their effect off in
    begin(); the shared LogoShow keeps animating and drawing everything."""

    def __init__(self, show, duration):
        super().__init__(show.stage)
        self.show = show
        self.duration = duration

    def begin(self, handover):
        super().begin(handover)
        self.done = False

    def update(self, seconds):
        super().update(seconds)
        self.show.update(seconds)
        self.done = self.elapsed >= self.duration

    def render(self):
        self.show.render()


class ShowLoveLogoPhase(LogoShowPhase):
    """PIXELOVE / LOVE, as the logo starts."""


class MorphToOlePhase(LogoShowPhase):
    """V spins away and the lower row rearranges LOVE -> OLE."""

    def begin(self, handover):
        super().begin(handover)
        self.show.logo.lower_row.morph_to("OLE")


class FadeBasePhase(LogoShowPhase):
    """The checkerboard floor fades out."""

    def __init__(self, show, duration, fade_seconds=1.5):
        super().__init__(show, duration)
        self.fade_seconds = fade_seconds

    def begin(self, handover):
        super().begin(handover)
        self.show.logo.floor.fade_to(0.0, self.fade_seconds)


class FadeDetailsPhase(LogoShowPhase):
    """Triangle, frame, comet, star and the floating pixels fade out."""

    def __init__(self, show, duration, fade_seconds=1.5):
        super().__init__(show, duration)
        self.fade_seconds = fade_seconds

    def begin(self, handover):
        super().begin(handover)
        self.show.logo.details.fade_to(0.0, self.fade_seconds)


class RevealLibraryPhase(LogoShowPhase):
    """The BIBLIOTEKA scene fades in behind the remaining logo."""

    def __init__(self, show, duration, fade_seconds=2.5):
        super().__init__(show, duration)
        self.fade_seconds = fade_seconds

    def begin(self, handover):
        super().begin(handover)
        self.show.show_library(self.fade_seconds)


class DriftToCornerPhase(LogoShowPhase):
    """The logo shrinks to a quarter and drifts into the top-left corner over
    `drift_seconds`, then stays there over the library scene. The invader
    breaks away instead and keeps circling the screen centre
    counter-clockwise from then on."""

    def __init__(self, show, duration, drift_seconds=3.0, target_scale=0.25, target_offset=(-0.83, 0.77)):
        super().__init__(show, duration)
        self.drift_seconds = drift_seconds
        self.target_scale = target_scale
        self.target_offset = target_offset

    def begin(self, handover):
        super().begin(handover)
        self.show.stage.detach_and_orbit(self.show.logo.invader)

    def update(self, seconds):
        super().update(seconds)
        drift = CameraInterpolationHelper.smooth(self.elapsed / self.drift_seconds)
        stage = self.show.stage
        stage.screen_scale = CameraInterpolationHelper.blend(1.0, self.target_scale, drift)
        stage.screen_offset = tuple(CameraInterpolationHelper.blend(0.0, target, drift)
                                    for target in self.target_offset)


class ZoomToLibraryPhase(LogoShowPhase):
    """The library camera leaves its orbit and closes in on the BIBLIOTEKA
    front. It heads for a close-up over the road (z 17..27) but stops after
    `zoom_fraction` of the way. The logo stays in its corner."""

    def __init__(self, show, duration, zoom_seconds=6.0, zoom_fraction=0.5, close_eye=(15.5, 20.0, 17.0),
                 close_target=(15.5, 12.8, 0.0)):
        super().__init__(show, duration)
        self.zoom_seconds = zoom_seconds
        self.zoom_fraction = zoom_fraction
        self.close_eye = close_eye
        self.close_target = close_target
        self.start_eye = None
        self.start_target = None

    def begin(self, handover):
        super().begin(handover)
        self.start_eye, self.start_target = self.show.current_library_view()

    def update(self, seconds):
        super().update(seconds)
        zoom = self.zoom_fraction * CameraInterpolationHelper.smooth(self.elapsed / self.zoom_seconds)
        eye = tuple(CameraInterpolationHelper.blend(start, end, zoom)
                    for start, end in zip(self.start_eye, self.close_eye))
        target = tuple(CameraInterpolationHelper.blend(start, end, zoom)
                       for start, end in zip(self.start_target, self.close_target))
        self.show.library_view = (eye, target)


class SpinInvaderPhase(LogoShowPhase):
    """The circling invader turns once around its own vertical axis."""

    def __init__(self, show, duration, spin_seconds=2.5):
        super().__init__(show, duration)
        self.spin_seconds = spin_seconds

    def update(self, seconds):
        super().update(seconds)
        spin = CameraInterpolationHelper.smooth(self.elapsed / self.spin_seconds)
        self.show.logo.invader.yaw = 0.0 if spin >= 1.0 else 360.0 * spin


class InvaderVisitsLibraryPhase(LogoShowPhase):
    """The invader leaves its circle for the library entrance: in through
    the portico's right arch, across inside, out through the left arch and
    onto a smaller circle in front of the BIBLIOTEKA front (`circle_center`,
    `circle_radius`), where it keeps going round. The camera stays where the
    zoom left it."""

    def __init__(self, show, duration, flight_seconds=8.0, fly_height=2.6, right_arch_x=17.3, left_arch_x=13.7,
                 inside_z=1.95, doorstep_z=5.5, approach_z=10.0, glide_rise=2.5, glide_z=16.0,
                 circle_center=(15.5, 6.0, 7.0), circle_radius=3.0):
        super().__init__(show, duration)
        self.flight_seconds = flight_seconds
        self.circle = (circle_center, circle_radius)
        # The glide points ease the steep dive onto the arch line so the spline does not dip below it.
        glide_height = fly_height + glide_rise
        self.waypoints = ((right_arch_x, glide_height, glide_z), (right_arch_x, fly_height, approach_z),
                          (right_arch_x, fly_height, doorstep_z), (right_arch_x, fly_height, inside_z),
                          (left_arch_x, fly_height, inside_z), (left_arch_x, fly_height, doorstep_z))

    def begin(self, handover):
        super().begin(handover)
        self.show.start_invader_flight(self.waypoints, self.flight_seconds, self.circle)


class EnterLibraryPhase(LogoShowPhase):
    """After one more full revolution of its library circle the invader dives
    through the left arch and vanishes into the entrance door at the back of
    the portico. Ends `linger_seconds` after it is inside, which hands over
    to stage 2."""

    def __init__(self, show, linger_seconds=1.0, flight_seconds=4.0, arch_x=13.7, fly_height=2.6,
                 doorstep_z=5.5, inside_z=2.2, door=(13.7, 2.1, 0.75), revolutions=1.0):
        super().__init__(show, duration=linger_seconds)
        self.flight_seconds = flight_seconds
        self.revolutions = revolutions
        self.waypoints = ((arch_x, fly_height, doorstep_z), (arch_x, fly_height - 0.2, inside_z), door)
        self.inside_for = 0.0

    def begin(self, handover):
        super().begin(handover)
        self.inside_for = 0.0
        self.show.send_invader_inside(self.waypoints, self.flight_seconds, self.revolutions)

    def update(self, seconds):
        super().update(seconds)
        if self.show.invader_inside:
            self.inside_for += seconds
        self.done = self.inside_for >= self.duration


class HoldPhase(LogoShowPhase):
    """Keeps everything running as it is (the final state)."""


def build_logo_phases(show):
    return [
        ShowLoveLogoPhase(show, 3.0),
        MorphToOlePhase(show, 4.0),
        FadeBasePhase(show, 3.0),
        FadeDetailsPhase(show, 3.0),
        RevealLibraryPhase(show, 7.0),
        DriftToCornerPhase(show, 5.0, drift_seconds=3.0),
        ZoomToLibraryPhase(show, 6.0),
        SpinInvaderPhase(show, 4.0),
        InvaderVisitsLibraryPhase(show, 9.0),
        ZoomToLibraryPhase(show, 6.0, zoom_fraction=1.0, close_eye=(15.5, 7.0, 15.0),
                           close_target=(15.5, 6.0, 7.0)),
        EnterLibraryPhase(show),
    ]
