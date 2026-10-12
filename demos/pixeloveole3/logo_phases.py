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
    `drift_seconds`, then stays there over the library scene."""

    def __init__(self, show, duration, drift_seconds=3.0, target_scale=0.25, target_offset=(-0.83, 0.77)):
        super().__init__(show, duration)
        self.drift_seconds = drift_seconds
        self.target_scale = target_scale
        self.target_offset = target_offset

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


def build_logo_phases(show):
    return [
        ShowLoveLogoPhase(show, 3.0),
        MorphToOlePhase(show, 4.0),
        FadeBasePhase(show, 3.0),
        FadeDetailsPhase(show, 3.0),
        RevealLibraryPhase(show, 7.0),
        DriftToCornerPhase(show, 5.0, drift_seconds=3.0),
        ZoomToLibraryPhase(show, 6.0),
    ]
