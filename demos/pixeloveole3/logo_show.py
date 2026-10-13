import math

from OpenGL.GL import *
from OpenGL.GLU import gluLookAt, gluPerspective

from demos.pixeloveole3.hall_scene import HallScene
from demos.pixeloveole3.invader_flight import InvaderFlight, WorldFlight, WorldOrbit
from demos.pixeloveole3.scene import LibraryScene
from lib import Globals
from lib.demo_phases import CameraInterpolationHelper
from lib.pixelove_ole.logo import PixeloveOleLogo


class PartOrbit:
    """Carries a logo part round a circle in the screen plane, counter-clockwise
    as seen from the camera, starting where the part stands and easing its
    speed in over `ramp_seconds`."""

    def __init__(self, part, center, period_seconds=12.0, ramp_seconds=2.0):
        self.part = part
        self.center = center
        self.radius = math.hypot(part.x - center[0], part.y - center[1])
        self.angle = math.atan2(part.y - center[1], part.x - center[0])
        self.angular_speed = 2.0 * math.pi / period_seconds
        self.ramp_seconds = ramp_seconds
        self.elapsed = 0.0

    def update(self, seconds):
        self.elapsed += seconds
        ramp = min(1.0, self.elapsed / self.ramp_seconds)
        self.angle += self.angular_speed * ramp * seconds
        self.part.x = self.center[0] + self.radius * math.cos(self.angle)
        self.part.y = self.center[1] + self.radius * math.sin(self.angle)


class LogoStage:
    """Views the 3D Pixelove Ole logo head-on with a gentle sway. The whole
    logo can be shrunk and slid across the screen (`screen_scale`,
    `screen_offset` in normalised device units) by post-projection, so the
    perspective of the logo itself never changes. Parts in `detached` are
    left out of that and keep the full-screen view."""

    def __init__(self, width, height, lower_word="LOVE", field_of_view=40.0, distance=13.0,
                 target_height=0.7, pitch_degrees=6.0, sway_degrees=12.0, sway_speed=0.5):
        self.width = width
        self.height = height
        self.logo = PixeloveOleLogo(lower_word=lower_word)
        self.field_of_view = field_of_view
        self.distance = distance
        self.target_height = target_height
        self.pitch = math.radians(pitch_degrees)
        self.sway = math.radians(sway_degrees)
        self.sway_speed = sway_speed
        self.screen_scale = 1.0
        self.screen_offset = (0.0, 0.0)
        self.detached = []
        self.orbits = []

    @property
    def screen_center(self):
        """World point (x, y) the camera looks at, i.e. the screen centre."""
        return 0.0, self.target_height

    def detach_and_orbit(self, part, period_seconds=12.0):
        self.detached.append(part)
        self.orbits.append(PartOrbit(part, self.screen_center, period_seconds))

    def release(self, part):
        """Stop drawing / orbiting a detached part here."""
        self.detached.remove(part)
        self.orbits = [orbit for orbit in self.orbits if orbit.part is not part]

    def update(self, seconds):
        self.logo.update(seconds)
        for orbit in self.orbits:
            orbit.update(seconds)

    def camera_view(self, elapsed):
        """(eye, target) the logo is looked at from at `elapsed`."""
        yaw = self.sway * math.sin(elapsed * self.sway_speed)
        eye = (self.distance * math.cos(self.pitch) * math.sin(yaw),
               self.target_height + self.distance * math.sin(self.pitch),
               self.distance * math.cos(self.pitch) * math.cos(yaw))
        return eye, (0.0, self.target_height, 0.0)

    def _project(self, scale, offset):
        glLoadIdentity()
        glTranslatef(*offset, 0.0)
        glScalef(scale, scale, 1.0)
        gluPerspective(self.field_of_view, self.width / self.height, 0.1, 200.0)

    def render(self, elapsed, elsewhere=()):
        """Draw the logo; parts in `elsewhere` are drawn by someone else."""
        glPushAttrib(GL_ENABLE_BIT)
        glDisable(GL_FOG)
        glDisable(GL_LIGHTING)
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        self._project(self.screen_scale, self.screen_offset)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        eye, target = self.camera_view(elapsed)
        gluLookAt(*eye, *target, 0.0, 1.0, 0.0)
        self.logo.draw(exclude=(*self.detached, *elsewhere))
        if self.detached:
            glMatrixMode(GL_PROJECTION)
            self._project(1.0, (0.0, 0.0))
            glMatrixMode(GL_MODELVIEW)
            for part in self.detached:
                part.draw()
        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glPopAttrib()


class LogoShow:
    """Shared state of the pixeloveole3 phases: the logo, the BIBLIOTEKA
    library scene behind it, how much of that scene is faded in and, once a
    phase takes over its camera, the (eye, target) it is viewed from. The
    logo is an overlay with its own projection, so it stays put on screen
    whatever the library camera does. Parts in `world_parts` (the invader on
    its flight) are drawn inside the library scene instead."""

    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.stage = LogoStage(width, height)
        self.library = LibraryScene(width, height)
        self.elapsed = 0.0
        self.library_elapsed = 0.0
        self.library_visibility = 0.0
        self.library_shown = False
        self.library_fade_seconds = 1.0
        self.library_view = None
        self.world_parts = []
        self.flight = None
        self.invader_circle = None
        self.world_orbit = None
        self.pending_entry = None
        self.entry_flight = None
        self.invader_inside = False
        self.hall = None
        self.hall_view = None
        self.hall_elapsed = 0.0
        self.hall_visibility = 0.0
        self.hall_fade_seconds = 1.0
        self.hall_flight = None
        self.hall_circle = None

    @property
    def logo(self):
        return self.stage.logo

    def show_library(self, fade_seconds):
        self.library_shown = True
        self.library_fade_seconds = fade_seconds

    def current_library_view(self):
        return self.library_view or self.library.camera.view(self.library_elapsed)

    def current_world_view(self):
        if self.hall:
            return self.hall_view or self.hall.default_view(self.hall_elapsed)
        return self.current_library_view()

    def enter_hall(self, view, fade_seconds):
        self.hall = HallScene(self.width, self.height)
        self.hall_view = view
        self.hall_fade_seconds = fade_seconds
        self.library_shown = False

    def fly_invader_into_hall(self, start, waypoints, duration, circle, grow_share=0.35):
        invader = self.logo.invader
        invader.x, invader.y, invader.z = start
        invader.scale = 0.0
        invader.visible = True
        if invader not in self.world_parts:
            self.world_parts.append(invader)
        self.world_orbit = None
        self.hall_circle = circle
        destination = self._nearest_on_circle(waypoints[-1], circle)
        self.hall_flight = WorldFlight(invader, (*waypoints, destination), duration, shrink_share=0.0,
                                       grow_share=grow_share)

    def _nearest_on_circle(self, point, circle):
        center, radius, across = circle
        sideways = sum((point[axis] - center[axis]) * across[axis] for axis in (0, 2))
        angle = math.atan2(point[1] - center[1], sideways)
        return (center[0] + across[0] * radius * math.cos(angle), center[1] + radius * math.sin(angle),
                center[2] + across[2] * radius * math.cos(angle))

    def _update_hall(self, seconds, eye):
        if not self.hall:
            return
        self.hall_elapsed += seconds
        self.hall_visibility = CameraInterpolationHelper.smooth(self.hall_elapsed / self.hall_fade_seconds)
        if self.hall_flight:
            self.hall_flight.update(seconds, eye)
            if self.hall_flight.done:
                center, radius, across = self.hall_circle
                self.world_orbit = WorldOrbit(self.hall_flight.part, center, radius, across=across)
                self.hall_flight = None

    def start_invader_flight(self, waypoints, duration, circle=None):
        """Fly the invader through `waypoints`. With `circle` = (centre, radius)
        it then joins that circle in the library at the point nearest the
        last waypoint and keeps going round there; without, it returns to its
        overlay circle."""
        invader = self.logo.invader
        self.stage.release(invader)
        self.world_parts.append(invader)
        destination = None
        if circle:
            (center_x, center_y, center_z), radius = circle
            last_x, last_y, _ = waypoints[-1]
            angle = math.atan2(last_y - center_y, last_x - center_x)
            destination = (center_x + radius * math.cos(angle), center_y + radius * math.sin(angle), center_z)
        self.invader_circle = circle
        self.flight = InvaderFlight(self, invader, waypoints, duration, destination)

    def _update_flight(self, seconds):
        if not self.flight:
            return
        self.flight.update(seconds)
        if self.flight.done:
            if self.flight.returns:
                self.flight.land()
                self.world_parts.remove(self.flight.part)
                self.stage.detach_and_orbit(self.flight.part)
            else:
                center, radius = self.invader_circle
                self.world_orbit = WorldOrbit(self.flight.part, center, radius)
            self.flight = None

    def send_invader_inside(self, waypoints, duration, after_revolutions=1.0):
        """Once the invader has gone round its library circle
        `after_revolutions` times, fly it through `waypoints` and let it
        vanish into the last one; `invader_inside` turns True then."""
        self.pending_entry = (waypoints, duration, after_revolutions)

    def _update_entry(self, seconds, eye):
        if self.pending_entry and self.world_orbit:
            waypoints, duration, after_revolutions = self.pending_entry
            if self.world_orbit.revolutions >= after_revolutions:
                self.entry_flight = WorldFlight(self.world_orbit.part, waypoints, duration)
                self.world_orbit = None
                self.pending_entry = None
        if self.entry_flight:
            self.entry_flight.update(seconds, eye)
            if self.entry_flight.done:
                self.entry_flight.part.visible = False
                self.world_parts.remove(self.entry_flight.part)
                self.entry_flight = None
                self.invader_inside = True

    def update(self, seconds):
        self.elapsed += seconds
        self.stage.update(seconds)
        self._update_flight(seconds)
        eye, _ = self.current_world_view()
        if self.world_orbit:
            self.world_orbit.update(seconds, eye)
        self._update_entry(seconds, eye)
        self._update_hall(seconds, eye)
        if self.library_shown:
            self.library_elapsed += seconds
            self.library_visibility = CameraInterpolationHelper.smooth(self.library_elapsed / self.library_fade_seconds)

    def render(self):
        if self.hall:
            self.hall.render(self.hall_elapsed, self.hall_view)
            for part in self.world_parts:
                part.draw()
            self._darken(1.0 - self.hall_visibility)
            glClear(GL_DEPTH_BUFFER_BIT)
        elif self.library_shown:
            self.library.render(self.library_elapsed, self.library_view)
            for part in self.world_parts:
                part.draw()
            self._darken(1.0 - self.library_visibility)
            glClear(GL_DEPTH_BUFFER_BIT)
        else:
            glClearColor(0.0, 0.0, 0.0, 1.0)
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        self.stage.render(self.elapsed, elsewhere=self.world_parts)

    def render_blank(self):
        self.library.render_blank()

    def _darken(self, amount):
        if amount <= 0.0:
            return
        glPushAttrib(GL_ENABLE_BIT | GL_COLOR_BUFFER_BIT | GL_CURRENT_BIT)
        glDisable(GL_DEPTH_TEST)
        glDisable(GL_LIGHTING)
        glDisable(GL_FOG)
        glDisable(GL_TEXTURE_2D)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(0.0, 1.0, 0.0, 1.0, -1.0, 1.0)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        glColor4f(0.0, 0.0, 0.0, amount)
        glBegin(GL_QUADS)
        glVertex2f(0.0, 0.0)
        glVertex2f(1.0, 0.0)
        glVertex2f(1.0, 1.0)
        glVertex2f(0.0, 1.0)
        glEnd()
        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glPopAttrib()
