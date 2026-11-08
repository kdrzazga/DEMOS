import math

from OpenGL.GL import (
    GL_AMBIENT_AND_DIFFUSE,
    GL_COLOR_MATERIAL,
    GL_COMPILE,
    GL_ENABLE_BIT,
    GL_FRONT_AND_BACK,
    GL_LIGHTING,
    GL_QUAD_STRIP,
    GL_TEXTURE_2D,
    GL_TRUE,
    glBegin,
    glCallList,
    glColor3f,
    glColorMaterial,
    glDisable,
    glEnable,
    glEnd,
    glEndList,
    glGenLists,
    glMultMatrixf,
    glNewList,
    glNormal3f,
    glPopAttrib,
    glPopMatrix,
    glPushAttrib,
    glPushMatrix,
    glRotatef,
    glScalef,
    glTexCoord2f,
    glTranslatef,
    glVertex3f,
)
from OpenGL.GLU import gluCylinder, gluNewQuadric, gluQuadricTexture, gluSphere

from lib.vector3 import Vector3


class BodyPainter:

    def __init__(self):
        self.plain = gluNewQuadric()
        self.textured = gluNewQuadric()
        gluQuadricTexture(self.textured, GL_TRUE)
        self.slices = 14
        self.stacks = 10

    def _orient(self, origin, axis):
        forward = axis.normalized()
        reference = Vector3(0.0, 1.0, 0.0) if abs(forward.y) < 0.9 else Vector3(1.0, 0.0, 0.0)
        side = reference.cross(forward).normalized()
        lift = forward.cross(side)
        glMultMatrixf((side.x, side.y, side.z, 0.0,
                       lift.x, lift.y, lift.z, 0.0,
                       forward.x, forward.y, forward.z, 0.0,
                       origin.x, origin.y, origin.z, 1.0))

    def limb(self, start, end, start_radius, end_radius, color):
        glColor3f(*color)
        glPushMatrix()
        self._orient(start, end - start)
        gluCylinder(self.plain, start_radius, end_radius, (end - start).length(), self.slices, 2)
        glPopMatrix()
        self.ball(start, start_radius, color)
        self.ball(end, end_radius, color)

    def ball(self, center, radius, color):
        glColor3f(*color)
        glPushMatrix()
        glTranslatef(*center)
        gluSphere(self.plain, radius, self.slices, self.stacks)
        glPopMatrix()

    def ellipsoid(self, center, axis, across, along, depth, color, texture=None):
        glColor3f(*color)
        glPushMatrix()
        self._orient(center, axis)
        glScalef(across, depth, along)
        if texture is None:
            gluSphere(self.plain, 1.0, self.slices + 6, self.stacks + 4)
        else:
            glEnable(GL_TEXTURE_2D)
            texture.bind()
            gluSphere(self.textured, 1.0, self.slices + 6, self.stacks + 4)
            glDisable(GL_TEXTURE_2D)
        glPopMatrix()


class TorsoStation:

    def __init__(self, along, half_width, half_depth, clothed):
        self.along = along
        self.half_width = half_width
        self.half_depth = half_depth
        self.clothed = clothed


class Torso:

    def __init__(self, pose, skin_color, shirt_color, shirt_texture):
        self.skin_color = skin_color
        self.shirt_color = shirt_color
        self.shirt_texture = shirt_texture
        self.spine_bottom = pose.pelvis + Vector3(0.0, 0.05, -0.02)
        self.spine_bend = pose.chest + Vector3(0.0, -0.06, 0.04)
        self.spine_top = pose.neck_base + Vector3(0.0, -0.01, 0.01)
        self.segments = 24
        self.crop_line = 0.34
        self.shirt_slack = 0.008
        self.stations = [
            TorsoStation(0.0, 0.14, 0.1, False),
            TorsoStation(0.16, 0.128, 0.088, False),
            TorsoStation(self.crop_line, 0.136, 0.094, False),
            TorsoStation(self.crop_line, 0.136 + self.shirt_slack, 0.094 + self.shirt_slack, True),
            TorsoStation(0.5, 0.16, 0.112, True),
            TorsoStation(0.68, 0.176, 0.12, True),
            TorsoStation(0.86, 0.19, 0.108, True),
            TorsoStation(0.96, 0.15, 0.085, True),
            TorsoStation(1.0, 0.07, 0.055, True),
            TorsoStation(1.0, 0.012, 0.01, True),
        ]

    def spine_point(self, along):
        rest = 1.0 - along
        return (self.spine_bottom * (rest * rest) + self.spine_bend * (2.0 * rest * along)
                + self.spine_top * (along * along))

    def spine_direction(self, along):
        return ((self.spine_bend - self.spine_bottom) * (2.0 * (1.0 - along))
                + (self.spine_top - self.spine_bend) * (2.0 * along)).normalized()

    def ring(self, station):
        center = self.spine_point(station.along)
        side = Vector3(1.0, 0.0, 0.0)
        depth_axis = self.spine_direction(station.along).cross(side).normalized()
        points = []
        for segment in range(self.segments + 1):
            angle = 2.0 * math.pi * segment / self.segments
            cosine = math.cos(angle)
            sine = math.sin(angle)
            position = center + side * (station.half_width * cosine) + depth_axis * (station.half_depth * sine)
            normal = (side * (cosine / station.half_width) + depth_axis * (sine / station.half_depth)).normalized()
            points.append((position, normal, segment / self.segments))
        return points

    def emit(self):
        rings = [self.ring(station) for station in self.stations]
        for lower_index in range(len(self.stations) - 1):
            lower = self.stations[lower_index]
            upper = self.stations[lower_index + 1]
            self._band(rings[lower_index], rings[lower_index + 1], lower, upper)

    def _band(self, lower_ring, upper_ring, lower, upper):
        clothed = upper.clothed
        glColor3f(*(self.shirt_color if clothed else self.skin_color))
        if clothed:
            glEnable(GL_TEXTURE_2D)
            self.shirt_texture.bind()
        glBegin(GL_QUAD_STRIP)
        for (low_position, low_normal, around), (high_position, high_normal, _) in zip(lower_ring, upper_ring):
            glNormal3f(*low_normal)
            glTexCoord2f(around, lower.along)
            glVertex3f(*low_position)
            glNormal3f(*high_normal)
            glTexCoord2f(around, upper.along)
            glVertex3f(*high_position)
        glEnd()
        if clothed:
            glDisable(GL_TEXTURE_2D)


class WomanPose:

    def __init__(self):
        self.left_foot = Vector3(-0.12, 0.04, 0.06)
        self.right_foot = Vector3(0.15, 0.04, 0.14)
        self.left_knee = Vector3(-0.11, 0.47, -0.03)
        self.right_knee = Vector3(0.14, 0.46, 0.05)
        self.left_hip = Vector3(-0.1, 0.86, 0.0)
        self.right_hip = Vector3(0.1, 0.86, 0.02)
        self.pelvis = Vector3(0.0, 0.88, 0.0)
        self.waist = Vector3(0.0, 1.0, -0.06)
        self.chest = Vector3(0.0, 1.2, -0.2)
        self.neck_base = Vector3(0.0, 1.36, -0.33)
        self.neck_top = Vector3(0.0, 1.43, -0.38)
        self.head = Vector3(0.0, 1.52, -0.44)
        self.left_shoulder = Vector3(-0.19, 1.32, -0.29)
        self.right_shoulder = Vector3(0.19, 1.32, -0.29)
        self.left_elbow = Vector3(-0.28, 1.1, -0.56)
        self.right_elbow = Vector3(0.28, 1.1, -0.56)
        self.left_hand = Vector3(-0.04, 1.11, -0.63)
        self.right_hand = Vector3(0.07, 1.11, -0.6)


class Woman:

    def __init__(self, position, palette, shirt_texture):
        self.position = position
        self.palette = palette
        self.shirt_texture = shirt_texture
        self.pose = WomanPose()
        self.shirt_color = (1.0, 1.0, 1.0)
        self.shoe_color = (0.04, 0.04, 0.045)
        self.band_color = (0.05, 0.05, 0.06)
        self.look_swing_degrees = 9.0
        self.look_speed = 0.23
        self.nod_degrees = 3.0
        self.nod_speed = 0.37
        self.elapsed = 0.0
        self.body_list = None
        self.head_list = None
        self.painter = None

    def prepare(self):
        self.painter = BodyPainter()
        self.body_list = self._compile(self._emit_body)
        self.head_list = self._compile(self._emit_head)

    def update(self, seconds):
        self.elapsed += seconds

    def draw(self):
        glPushAttrib(GL_ENABLE_BIT)
        glEnable(GL_LIGHTING)
        glEnable(GL_COLOR_MATERIAL)
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
        glPushMatrix()
        glTranslatef(*self.position)
        glCallList(self.body_list)
        neck = self.pose.neck_top
        glTranslatef(*neck)
        glRotatef(self.look_swing_degrees * math.sin(self.elapsed * self.look_speed), 0.0, 1.0, 0.0)
        glRotatef(self.nod_degrees * math.sin(self.elapsed * self.nod_speed), 1.0, 0.0, 0.0)
        glTranslatef(-neck.x, -neck.y, -neck.z)
        glCallList(self.head_list)
        glPopMatrix()
        glPopAttrib()

    def _compile(self, emit):
        list_id = glGenLists(1)
        glNewList(list_id, GL_COMPILE)
        emit()
        glEndList()
        return list_id

    def _emit_body(self):
        pose = self.pose
        painter = self.painter
        skin = self.palette.skin
        shorts = self.palette.shorts
        for foot in (pose.left_foot, pose.right_foot):
            painter.ellipsoid(foot + Vector3(0.0, 0.0, -0.06), Vector3(0.0, 0.0, -1.0), 0.05, 0.12, 0.045,
                              self.shoe_color)
        painter.limb(pose.left_knee, pose.left_foot + Vector3(0.0, 0.06, 0.0), 0.05, 0.036, skin)
        painter.limb(pose.right_knee, pose.right_foot + Vector3(0.0, 0.06, 0.0), 0.05, 0.036, skin)
        painter.limb(pose.left_hip, pose.left_knee, 0.075, 0.052, skin)
        painter.limb(pose.right_hip, pose.right_knee, 0.075, 0.052, skin)
        painter.ellipsoid(pose.pelvis, pose.waist - pose.pelvis, 0.19, 0.13, 0.13, shorts)
        for hip, knee in ((pose.left_hip, pose.left_knee), (pose.right_hip, pose.right_knee)):
            cuff = hip + (knee - hip) * 0.35
            painter.limb(hip, cuff, 0.085, 0.08, shorts)
        Torso(pose, skin, self.shirt_color, self.shirt_texture).emit()
        for shoulder, elbow, hand in ((pose.left_shoulder, pose.left_elbow, pose.left_hand),
                                      (pose.right_shoulder, pose.right_elbow, pose.right_hand)):
            painter.limb(shoulder, elbow, 0.045, 0.038, skin)
            painter.limb(elbow, hand, 0.038, 0.032, skin)
            painter.ball(hand, 0.045, skin)
            painter.limb(shoulder, shoulder + (elbow - shoulder) * 0.42, 0.068, 0.06, self.shirt_color)
        band_start = pose.left_elbow + (pose.left_hand - pose.left_elbow) * 0.78
        painter.limb(band_start, band_start + (pose.left_hand - pose.left_elbow) * 0.1, 0.042, 0.04, self.band_color)
        painter.limb(pose.neck_base, pose.neck_top, 0.05, 0.045, skin)

    def _emit_head(self):
        pose = self.pose
        painter = self.painter
        painter.ball(pose.head, 0.102, self.palette.skin)
        hair = self.palette.hair
        upward = Vector3(0.0, 1.0, 0.0)
        painter.ellipsoid(pose.head + Vector3(0.0, 0.025, 0.02), upward, 0.122, 0.118, 0.128, hair)
        painter.ellipsoid(pose.head + Vector3(0.0, -0.045, 0.03), upward, 0.135, 0.085, 0.13, hair)
