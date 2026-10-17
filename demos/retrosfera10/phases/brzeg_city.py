import math

from OpenGL.GL import (
	GL_BLEND, GL_COLOR_BUFFER_BIT, GL_DEPTH_BUFFER_BIT, GL_DEPTH_TEST, GL_LIGHTING, GL_ONE_MINUS_SRC_ALPHA, GL_QUADS,
	GL_SRC_ALPHA, GL_TEXTURE_2D, glBegin, glBindTexture, glBlendFunc, glClear, glClearColor, glColor3f, glColor4f,
	glDisable, glEnable, glEnd, glPopMatrix, glPushMatrix, glScalef, glTexCoord2f, glVertex3f,
)

from lib.demo_phases import CameraInterpolationHelper, GeoPoint, Light, DemoPhase, PhaseStepSequencer
from demos.retrosfera10.models.brzeg import Brzeg
from demos.retrosfera10.models.townhall import Vector3


class BrzegTimeline:
	def __init__(self, magnify=0.5, landing=3.5, glide=7.0, sway=4.0, sway_count=2, hall_zoom=6.0, hall_orbit=14.0,
			descent=4.0, entry=3.0):
		self.magnify = magnify
		self.landing = landing
		self.glide = glide
		self.sway = sway
		self.sway_count = sway_count
		self.hall_zoom = hall_zoom
		self.hall_orbit = hall_orbit
		self.descent = descent
		self.entry = entry


class CityProgress:
	def __init__(self, timeline, time):
		cursor = PhaseStepSequencer(time)
		self.magnify = CameraInterpolationHelper.smooth(cursor.advance(timeline.magnify))
		self.landing = CameraInterpolationHelper.smooth(cursor.advance(timeline.landing))
		self.glide = CameraInterpolationHelper.smooth(cursor.advance(timeline.glide))
		self.sway = cursor.advance(timeline.sway)
		self.hall = CameraInterpolationHelper.smooth(cursor.advance(timeline.hall_zoom))
		self.orbit = CameraInterpolationHelper.smooth(cursor.advance(timeline.hall_orbit))
		self.descent = CameraInterpolationHelper.smooth(cursor.advance(timeline.descent))
		entry = cursor.advance(timeline.entry)
		self.entry = entry * entry
		self.finished = cursor.finished()


class MagnifiedGround:
	def __init__(self, texture_id, anchor, anchor_site, start_degrees_per_unit, end_degrees_per_unit, half_size=2000.0,
			ground_color=(0.42, 0.43, 0.38), ground_cover=0.85):
		self.texture_id = texture_id
		self.anchor = anchor
		self.anchor_site = anchor_site
		self.start_degrees_per_unit = start_degrees_per_unit
		self.end_degrees_per_unit = end_degrees_per_unit
		self.half_size = half_size
		self.ground_color = ground_color
		self.ground_cover = ground_cover

	def degrees_per_unit(self, progress):
		return self.start_degrees_per_unit * (self.end_degrees_per_unit / self.start_degrees_per_unit) ** progress

	def corners(self):
		half = self.half_size
		return ((-half, half), (half, half), (half, -half), (-half, -half))

	def draw(self, progress, brightness):
		degrees = self.degrees_per_unit(progress)
		latitude_scale = degrees / 180.0
		longitude_scale = degrees / math.cos(math.radians(self.anchor_site.latitude)) / 360.0
		center_u = (self.anchor_site.longitude + 180.0) / 360.0
		center_v = (self.anchor_site.latitude + 90.0) / 180.0
		glDisable(GL_LIGHTING)
		glDisable(GL_DEPTH_TEST)
		glEnable(GL_TEXTURE_2D)
		glBindTexture(GL_TEXTURE_2D, self.texture_id)
		glColor3f(brightness, brightness, brightness)
		glBegin(GL_QUADS)
		for x, z in self.corners():
			glTexCoord2f(center_u + (x - self.anchor.x) * longitude_scale, center_v - (z - self.anchor.z) * latitude_scale)
			glVertex3f(x, 0.0, z)
		glEnd()
		glDisable(GL_TEXTURE_2D)
		glEnable(GL_BLEND)
		glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
		glColor4f(*self.ground_color, self.ground_cover * progress)
		glBegin(GL_QUADS)
		for x, z in self.corners():
			glVertex3f(x, 0.0, z)
		glEnd()
		glDisable(GL_BLEND)
		glEnable(GL_DEPTH_TEST)
		glEnable(GL_LIGHTING)


class BrzegDemoPhase(DemoPhase):
	def __init__(self, camera, timeline=None, house_style="simple"):
		super().__init__(camera)
		self.timeline = timeline or BrzegTimeline()
		self.earth_texture_longitude_offset = -12.5
		self.site = GeoPoint(50.86, 17.47 + self.earth_texture_longitude_offset)
		self.light = Light(Vector3(0.55, 0.85, 0.65), (0.42, 0.42, 0.45, 1.0), (0.72, 0.7, 0.66, 1.0))
		self.sky_color = (0.55, 0.72, 0.92)
		self.top_view_height = 150.0
		self.view_pitch = 30.0
		self.landing_distance = 420.0
		self.landing_height = 28.0
		self.sign_view_distance = 24.0
		self.sway_amplitude = 2.5
		self.hall_waypoint = Vector3(0.0, 26.0, 55.0)
		self.hall_eye = Vector3(0.0, 30.0, 27.0)
		self.hall_target = Vector3(0.0, 14.0, 0.0)
		self.window_target = Vector3(0.25, 7.225, 12.0)
		self.window_approach_eye = Vector3(0.25, 7.225, 24.0)
		self.window_stop_eye = Vector3(0.25, 7.225, 12.7)
		self.final_degrees_per_unit = 3.5e-4
		self.brzeg = Brzeg(house_style=house_style)
		self.arrival = self.landing_eye(self.sign_focus()).at_height(0.0)
		self.arrival_site = self.site_at(self.arrival)
		self.ground = None
		self.surface_brightness = 1.0

	def site_at(self, position):
		latitude = self.site.latitude - position.z * self.final_degrees_per_unit
		longitude = self.site.longitude + position.x * self.final_degrees_per_unit / math.cos(math.radians(self.site.latitude))
		return GeoPoint(latitude, longitude)

	def begin(self, handover):
		super().begin(handover)
		self.surface_brightness = handover.surface_brightness
		self.ground = MagnifiedGround(
			handover.earth_texture_id, self.arrival, self.arrival_site,
			handover.altitude_degrees / self.top_view_height, self.final_degrees_per_unit,
		)

	def sign_focus(self):
		sign = self.brzeg.city_sign
		return Vector3(sign.x, sign.sign_size - sign.board_height / 2, sign.z)

	def view_line(self):
		pitch = math.radians(self.view_pitch)
		return Vector3(0.0, math.sin(pitch), math.cos(pitch))

	def landing_eye(self, focus):
		return Vector3(focus.x, self.landing_height, focus.z + self.landing_distance)

	def orbit_eye(self, eye, turn):
		angle = math.tau * turn
		offset = eye - self.hall_target.at_height(eye.y)
		return Vector3(
			self.hall_target.x + offset.x * math.cos(angle) + offset.z * math.sin(angle), eye.y,
			self.hall_target.z - offset.x * math.sin(angle) + offset.z * math.cos(angle),
		)

	def city_view(self, progress):
		focus = self.sign_focus()
		landed_eye = self.landing_eye(focus)
		sign_eye = focus + self.view_line() * self.sign_view_distance
		gliding_eye = CameraInterpolationHelper.blend(landed_eye, sign_eye, progress.glide)
		sway_offset = Vector3(self.sway_amplitude * math.sin(math.tau * self.timeline.sway_count * progress.sway), 0.0, 0.0)
		hall_eye = self.orbit_eye(CameraInterpolationHelper.curve(sign_eye, self.hall_waypoint, self.hall_eye, progress.hall), progress.orbit)
		eye = CameraInterpolationHelper.blend(self.arrival.at_height(self.top_view_height), gliding_eye, progress.landing)
		if progress.glide >= 1.0:
			eye = hall_eye + sway_offset
		if progress.descent > 0.0:
			eye = CameraInterpolationHelper.blend(CameraInterpolationHelper.blend(hall_eye, self.window_approach_eye, progress.descent), self.window_stop_eye, progress.entry)
		target = CameraInterpolationHelper.blend(CameraInterpolationHelper.blend(self.arrival, focus, progress.landing), self.hall_target, progress.hall)
		target = CameraInterpolationHelper.blend(target, self.window_target, progress.descent)
		up = CameraInterpolationHelper.blend(Vector3(0.0, 0.0, -1.0), Vector3.up(), progress.landing).normalized()
		return eye, target, up

	def update(self, seconds):
		super().update(seconds)
		self.done = CityProgress(self.timeline, self.elapsed).finished

	def render(self):
		progress = CityProgress(self.timeline, self.elapsed)
		sky = [CameraInterpolationHelper.blend(0.0, channel, progress.magnify) for channel in self.sky_color]
		glClearColor(sky[0], sky[1], sky[2], 1.0)
		glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
		self.camera.apply_projection(0.5, 4000.0)
		eye, target, up = self.city_view(progress)
		self.camera.look(eye, target, up)
		self.light.apply()
		self.ground.draw(progress.magnify, CameraInterpolationHelper.blend(self.surface_brightness, 1.0, progress.magnify))
		if progress.landing > 0.0:
			glPushMatrix()
			glScalef(1.0, max(0.01, progress.landing), 1.0)
			self.brzeg.draw()
			glPopMatrix()
