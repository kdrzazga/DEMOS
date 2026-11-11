import math
import os

import pygame
from OpenGL.GL import (
    GL_AMBIENT_AND_DIFFUSE,
    GL_COLOR_MATERIAL,
    GL_CURRENT_BIT,
    GL_ENABLE_BIT,
    GL_FRONT_AND_BACK,
    GL_LIGHTING,
    GL_QUADS,
    GL_TEXTURE_2D,
    glBegin,
    glColor3f,
    glColorMaterial,
    glDisable,
    glEnable,
    glEnd,
    glPopAttrib,
    glPopMatrix,
    glPushAttrib,
    glPushMatrix,
    glRotatef,
    glTexCoord2f,
    glTranslatef,
    glVertex3f,
)

from lib import Globals
from lib.urban.neon.textures import GlTexture
from lib.urban.neon.woman import Woman, WomanPose
from lib.vector3 import Vector3


def smoothstep(progress):
    progress = min(max(progress, 0.0), 1.0)
    return progress * progress * (3.0 - 2.0 * progress)


def between(origin, target, amount):
    return origin + (target - origin) * amount


class StandingPose(WomanPose):

    def __init__(self):
        super().__init__()
        self.left_foot = Vector3(-0.1, 0.04, 0.0)
        self.right_foot = Vector3(0.1, 0.04, 0.0)
        self.left_knee = Vector3(-0.1, 0.46, -0.02)
        self.right_knee = Vector3(0.1, 0.46, -0.02)
        self.left_hip = Vector3(-0.1, 0.86, 0.0)
        self.right_hip = Vector3(0.1, 0.86, 0.0)
        self.pelvis = Vector3(0.0, 0.88, 0.0)
        self.waist = Vector3(0.0, 1.0, 0.0)
        self.chest = Vector3(0.0, 1.2, -0.01)
        self.neck_base = Vector3(0.0, 1.38, 0.0)
        self.neck_top = Vector3(0.0, 1.46, -0.01)
        self.head = Vector3(0.0, 1.56, -0.02)
        self.left_shoulder = Vector3(-0.19, 1.34, 0.0)
        self.right_shoulder = Vector3(0.19, 1.34, 0.0)
        self.left_elbow = Vector3(-0.23, 1.02, 0.03)
        self.right_elbow = Vector3(0.23, 1.02, 0.03)
        self.left_hand = Vector3(-0.21, 0.72, -0.05)
        self.right_hand = Vector3(0.21, 0.72, -0.05)


class ReadingPose(StandingPose):

    def __init__(self):
        super().__init__()
        self.right_elbow = Vector3(0.26, 1.04, -0.06)
        self.right_hand = Vector3(0.12, 1.14, -0.34)
        self.left_elbow = Vector3(-0.3, 1.16, 0.1)
        self.left_hand = Vector3(-0.32, 1.08, 0.36)


class PoseBlender:

    @staticmethod
    def blend(origin_pose, target_pose, amount):
        blended = WomanPose()
        for joint_name, origin_joint in vars(origin_pose).items():
            setattr(blended, joint_name, between(origin_joint, getattr(target_pose, joint_name), amount))
        return blended


class WalkCycle:

    def __init__(self):
        self.standing_pose = StandingPose()
        self.full_cycle_distance = 1.3
        self.half_step_length = 0.3
        self.foot_lift = 0.09
        self.resting_knee_bend = 0.04
        self.swinging_knee_bend = 0.1
        self.hand_swing = 0.22
        self.elbow_swing = 0.1
        self.carrying_arm_swing_share = 0.25

    def pose_at(self, walked_distance, carrying_in_right_hand):
        phase = 2.0 * math.pi * walked_distance / self.full_cycle_distance
        pose = PoseBlender.blend(self.standing_pose, self.standing_pose, 0.0)
        self._swing_side(pose, "left", phase, 1.0)
        right_arm_share = self.carrying_arm_swing_share if carrying_in_right_hand else 1.0
        self._swing_side(pose, "right", phase + math.pi, right_arm_share)
        return pose

    def _swing_side(self, pose, side, leg_phase, arm_swing_share):
        leg_swing = math.sin(leg_phase)
        moving_forward = max(0.0, math.cos(leg_phase))
        hip = getattr(pose, side + "_hip")
        foot = getattr(pose, side + "_foot") + Vector3(0.0, self.foot_lift * moving_forward,
                                                       -self.half_step_length * leg_swing)
        knee_bend = self.resting_knee_bend + self.swinging_knee_bend * moving_forward
        knee = between(hip, foot + Vector3(0.0, 0.06, 0.0), 0.5) + Vector3(0.0, 0.0, -knee_bend)
        setattr(pose, side + "_foot", foot)
        setattr(pose, side + "_knee", knee)
        arm_swing = leg_swing * arm_swing_share
        setattr(pose, side + "_hand", getattr(pose, side + "_hand") + Vector3(0.0, 0.0, self.hand_swing * arm_swing))
        setattr(pose, side + "_elbow",
                getattr(pose, side + "_elbow") + Vector3(0.0, 0.0, self.elbow_swing * arm_swing))


class PaperPlacement:

    def __init__(self, center, across, upward):
        self.center = center
        self.across = across
        self.upward = upward

    def blended_toward(self, target, amount):
        return PaperPlacement(between(self.center, target.center, amount),
                              between(self.across, target.across, amount).normalized(),
                              between(self.upward, target.upward, amount).normalized())


class Newspaper:

    def __init__(self, cover_path):
        self.cover_path = cover_path
        self.height = 0.42
        self.width = 0.0
        self.cover_brightness = 0.9
        self.back_page_color = (0.8, 0.8, 0.76)
        self.back_page_gap = 0.003
        self.grip_inset = 0.04
        self.texture = None

    def prepare(self):
        cover = pygame.image.load(self.cover_path)
        cover_width, cover_height = cover.get_size()
        self.width = self.height * cover_width / cover_height
        self.texture = GlTexture(cover, repeating=False)

    def carried_placement(self, hand):
        center = hand + Vector3(0.035, self.grip_inset - self.height / 2.0, 0.0)
        return PaperPlacement(center, Vector3(0.0, 0.0, -1.0), Vector3(0.0, 1.0, 0.0))

    def read_placement(self, hand):
        center = hand + Vector3(self.grip_inset - self.width / 2.0, self.height / 2.0 - 2.0 * self.grip_inset, -0.03)
        return PaperPlacement(center, Vector3(-1.0, 0.0, 0.0), Vector3(0.0, 1.0, 0.0))

    def draw(self, placement):
        half_across = placement.across * (self.width / 2.0)
        half_upward = placement.upward * (self.height / 2.0)
        cover_corners = (placement.center - half_across - half_upward, placement.center + half_across - half_upward,
                         placement.center + half_across + half_upward, placement.center - half_across + half_upward)
        behind_cover = placement.upward.cross(placement.across).normalized() * self.back_page_gap
        glPushAttrib(GL_ENABLE_BIT | GL_CURRENT_BIT)
        glDisable(GL_LIGHTING)
        glEnable(GL_TEXTURE_2D)
        self.texture.bind()
        glColor3f(self.cover_brightness, self.cover_brightness, self.cover_brightness)
        glBegin(GL_QUADS)
        for corner, (u, v) in zip(cover_corners, ((0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0))):
            glTexCoord2f(u, v)
            glVertex3f(*corner)
        glEnd()
        glDisable(GL_TEXTURE_2D)
        glColor3f(*self.back_page_color)
        glBegin(GL_QUADS)
        for corner in cover_corners:
            glVertex3f(*(corner + behind_cover))
        glEnd()
        glPopAttrib()


class NewspaperWoman(Woman):

    def __init__(self, position, palette, shirt_texture, house_door_z):
        super().__init__(position, palette, shirt_texture)
        resources = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources")
        self.newspaper = Newspaper(os.path.join(resources, "kna1-cover.png"))
        self.leaning_pose = self.pose
        self.standing_pose = StandingPose()
        self.reading_pose = ReadingPose()
        self.walk_cycle = WalkCycle()
        self.rail_position = position
        self.door_position = Vector3(position.x, position.y, house_door_z)
        self.reading_position = position + Vector3(0.0, 0.0, -0.2)
        self.walk_speed = 1.2
        self.straightening_seconds = 1.0
        self.turning_seconds = 1.0
        self.seconds_inside_house = 1.0
        self.raising_newspaper_seconds = 1.2
        self.heading_toward_house_degrees = 180.0
        self.reading_heading_degrees = 180.0
        self.reading_head_pitch_degrees = -16.0
        self.reading_nod_degrees = 2.0
        self.reading_nod_speed = 0.5
        self.stage = "leaning"
        self.stage_seconds = 0.0
        self.reading_seconds = 0.0
        self.stage_order = ("leaning", "straightening", "turning_to_house", "walking_to_house", "inside_house",
                            "walking_to_rail", "turning_to_read", "raising_newspaper", "reading")

    def prepare(self):
        super().prepare()
        self.newspaper.prepare()

    def fetch_newspaper(self):
        if self.stage == "leaning":
            self._enter_stage("straightening")

    def _stage_duration(self):
        if self.stage == "straightening":
            return self.straightening_seconds
        if self.stage in ("turning_to_house", "turning_to_read"):
            return self.turning_seconds
        if self.stage == "walking_to_house":
            return (self.door_position - self.rail_position).length() / self.walk_speed
        if self.stage == "inside_house":
            return self.seconds_inside_house
        if self.stage == "walking_to_rail":
            return (self.reading_position - self.door_position).length() / self.walk_speed
        if self.stage == "raising_newspaper":
            return self.raising_newspaper_seconds
        return None

    def _enter_stage(self, stage):
        self.stage = stage
        self.stage_seconds = 0.0

    def update(self, seconds):
        super().update(seconds)
        self.stage_seconds += seconds
        if self.stage == "reading":
            self.reading_seconds += seconds
        duration = self._stage_duration()
        while duration is not None and self.stage_seconds >= duration:
            seconds_into_next_stage = self.stage_seconds - duration
            self._enter_stage(self.stage_order[self.stage_order.index(self.stage) + 1])
            self.stage_seconds = seconds_into_next_stage
            duration = self._stage_duration()

    def _stage_progress(self):
        duration = self._stage_duration()
        return 1.0 if duration is None else self.stage_seconds / duration

    def draw(self):
        if self.stage == "leaning":
            super().draw()
        elif self.stage != "inside_house":
            self._draw_moving()
            print(Globals.get_duration())

    def _draw_moving(self):
        progress = self._stage_progress()
        eased = smoothstep(progress)
        position = self.rail_position
        heading_degrees = 0.0
        pose = self.standing_pose
        head_pitch_degrees = 0.0
        paper_placement = None
        if self.stage == "straightening":
            pose = PoseBlender.blend(self.leaning_pose, self.standing_pose, eased)
        elif self.stage == "turning_to_house":
            heading_degrees = self.heading_toward_house_degrees * eased
        elif self.stage == "walking_to_house":
            position = between(self.rail_position, self.door_position, progress)
            heading_degrees = self.heading_toward_house_degrees
            pose = self.walk_cycle.pose_at((position - self.rail_position).length(), False)
        elif self.stage == "walking_to_rail":
            position = between(self.door_position, self.reading_position, progress)
            pose = self.walk_cycle.pose_at((position - self.door_position).length(), True)
            paper_placement = self.newspaper.carried_placement(pose.right_hand)
        elif self.stage == "turning_to_read":
            position = self.reading_position
            heading_degrees = self.reading_heading_degrees * eased
            paper_placement = self.newspaper.carried_placement(pose.right_hand)
        elif self.stage == "raising_newspaper":
            position = self.reading_position
            heading_degrees = self.reading_heading_degrees
            pose = PoseBlender.blend(self.standing_pose, self.reading_pose, eased)
            head_pitch_degrees = self.reading_head_pitch_degrees * eased
            paper_placement = self.newspaper.carried_placement(pose.right_hand).blended_toward(
                self.newspaper.read_placement(pose.right_hand), eased)
        elif self.stage == "reading":
            position = self.reading_position
            heading_degrees = self.reading_heading_degrees
            pose = self.reading_pose
            head_pitch_degrees = (self.reading_head_pitch_degrees
                                  + self.reading_nod_degrees * math.sin(self.reading_seconds * self.reading_nod_speed))
            paper_placement = self.newspaper.read_placement(pose.right_hand)
        self._draw_posed(position, heading_degrees, pose, head_pitch_degrees, paper_placement)

    def _draw_posed(self, position, heading_degrees, pose, head_pitch_degrees, paper_placement):
        glPushAttrib(GL_ENABLE_BIT)
        glEnable(GL_LIGHTING)
        glEnable(GL_COLOR_MATERIAL)
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
        glPushMatrix()
        glTranslatef(*position)
        glRotatef(heading_degrees, 0.0, 1.0, 0.0)
        self.pose = pose
        self._emit_body()
        if paper_placement is not None:
            self.newspaper.draw(paper_placement)
        neck = pose.neck_top
        glTranslatef(*neck)
        glRotatef(head_pitch_degrees, 1.0, 0.0, 0.0)
        glTranslatef(-neck.x, -neck.y, -neck.z)
        self._emit_head()
        self.pose = self.leaning_pose
        glPopMatrix()
        glPopAttrib()
