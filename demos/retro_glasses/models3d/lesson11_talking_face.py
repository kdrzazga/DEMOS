import numpy
from OpenGL.GL import *

from .lesson10_face import FaceSurface


class LipShape:
    def __init__(self, syllable, example, opening, spread, rounding):
        self.syllable = syllable
        self.example = example
        self.opening = opening
        self.spread = spread
        self.rounding = rounding

    @property
    def pose(self):
        return (self.opening, self.spread, self.rounding)

    def blended_pose(self, other, amount):
        return tuple(mine + (theirs - mine) * amount
                     for mine, theirs in zip(self.pose, other.pose))


class LipShapes:
    def __init__(self):
        self.rest = LipShape("", "", 0.0, 0.0, 0.0)
        self.shapes = [LipShape("ing", "go-ing", 0.25, 0.7, 0.0),
                       LipShape("er", "fast-er", 0.3, 0.0, 0.5),
                       LipShape("a", "a-bout", 0.8, 0.1, 0.0),
                       LipShape("ly", "quick-ly", 0.35, 0.5, 0.0),
                       LipShape("ed", "want-ed", 0.45, 0.4, 0.0),
                       LipShape("i", "i-dea", 0.7, 0.3, 0.0),
                       LipShape("es", "box-es", 0.25, 0.8, 0.0),
                       LipShape("re", "re-turn", 0.35, 0.1, 0.4),
                       LipShape("tion", "na-tion", 0.3, -0.2, 0.6),
                       LipShape("in", "in-side", 0.3, 0.5, 0.0),
                       LipShape("e", "e-vent", 0.3, 0.6, 0.0),
                       LipShape("con", "con-trol", 0.55, -0.1, 0.3),
                       LipShape("y", "hap-py", 0.2, 0.9, 0.0),
                       LipShape("ter", "af-ter", 0.35, 0.2, 0.2),
                       LipShape("ex", "ex-it", 0.5, 0.5, 0.0),
                       LipShape("al", "fin-al", 0.55, 0.2, 0.0),
                       LipShape("de", "de-cide", 0.35, 0.4, 0.0),
                       LipShape("com", "com-pare", 0.45, -0.2, 0.4),
                       LipShape("o", "o-pen", 0.6, -0.6, 1.0),
                       LipShape("di", "di-rect", 0.4, 0.5, 0.0)]
        self.by_syllable = {shape.syllable: shape
                            for shape in self.shapes}

    def shape_for(self, syllable):
        return self.by_syllable[syllable]


class Speech:
    def __init__(self, lip_shapes, words):
        self.lip_shapes = lip_shapes
        self.words = words
        self.syllable_duration = 0.2
        self.pause_slots = 2
        self.time = 0.0

    @property
    def slots(self):
        slots = []
        for word_index, (_text, syllables) in enumerate(self.words):
            slots += [(word_index, None)] * self.pause_slots
            slots += [(word_index, syllable_index)
                      for syllable_index in range(len(syllables))]
        return slots

    @property
    def duration(self):
        return len(self.slots) * self.syllable_duration

    def update(self, seconds):
        self.time += seconds

    def slot_progress(self):
        slots = self.slots
        position = self.time / self.syllable_duration
        index = int(position) % len(slots)
        following = slots[(index + 1) % len(slots)]
        return slots[index], following, position % 1.0

    def current_slot(self):
        return self.slot_progress()[0]

    def shape_of(self, slot):
        word_index, syllable_index = slot
        if syllable_index is None:
            return self.lip_shapes.rest
        syllables = self.words[word_index][1]
        return self.lip_shapes.shape_for(syllables[syllable_index])

    def lip_pose(self):
        current, following, progress = self.slot_progress()
        change = min(max(progress * 2.0 - 1.0, 0.0), 1.0)
        smooth_change = change * change * (3.0 - 2.0 * change)
        return self.shape_of(current).blended_pose(
            self.shape_of(following), smooth_change)

    def spoken_text(self):
        word_index, syllable_index = self.current_slot()
        text, syllables = self.words[word_index]
        marked = [syllable.upper() if index == syllable_index
                  else syllable
                  for index, syllable in enumerate(syllables)]
        return f"{text}: {'-'.join(marked)}"


class TalkingFace(FaceSurface):
    def __init__(self, size, divisions):
        self.mouth_color = (0.25, 0.05, 0.08)
        self.dark_threshold = 0.03
        self.dark_range = 0.12
        super().__init__(size, divisions)
        self.spread_stretch = 0.3
        self.rounding_squeeze = 0.35
        self.max_pout = 0.06
        self.max_jaw_drop = 0.12
        self.upper_lift = 0.02
        self.max_gap_stretch = 0.05
        self.rounding_gap_stretch = 0.04
        self.max_gap_depth = 0.25
        self.neutral = {feature: (feature.center_z, feature.width_x,
                                  feature.width_z, feature.height)
                        for feature in self.lips + self.chin}

    @property
    def mouth_gap(self):
        return self.lips[2]

    def reset_mouth(self):
        for feature, neutral in self.neutral.items():
            (feature.center_z, feature.width_x,
             feature.width_z, feature.height) = neutral

    def shape_lips(self, opening, spread, rounding):
        self.reset_mouth()
        upper_lip, lower_lip, mouth_gap = self.lips
        width_scale = (1.0 + self.spread_stretch * spread
                       - self.rounding_squeeze * rounding)
        jaw_drop = self.max_jaw_drop * opening
        for lip in (upper_lip, lower_lip):
            lip.width_x *= width_scale
            lip.height += self.max_pout * rounding
        upper_lip.center_z -= self.upper_lift * opening
        lower_lip.center_z += jaw_drop
        mouth_gap.center_z += jaw_drop / 2.0
        mouth_gap.width_x *= width_scale
        mouth_gap.width_z += (self.max_gap_stretch * opening
                              + self.rounding_gap_stretch * rounding)
        mouth_gap.height -= self.max_gap_depth * opening
        for feature in self.chin:
            feature.center_z += jaw_drop

    def mouth_colors(self):
        x = self.positions[:, 0]
        z = self.positions[:, 2]
        depth = -self.mouth_gap.heights(x, z) - self.dark_threshold
        darkness = numpy.clip(depth / self.dark_range, 0.0, 1.0)
        skin = numpy.array(self.skin_color)
        mouth = numpy.array(self.mouth_color)
        colors = skin + (mouth - skin) * darkness[:, None]
        return colors.astype(numpy.float32)

    def build(self):
        super().build()
        self.colors = self.mouth_colors()

    def draw_skin(self):
        glEnableClientState(GL_COLOR_ARRAY)
        glColorPointer(3, GL_FLOAT, 0, self.colors)
        super().draw_skin()
        glDisableClientState(GL_COLOR_ARRAY)


class TalkingFaceScene:
    def __init__(self):
        self.face = TalkingFace(4.0, 200)
        self.lip_shapes = LipShapes()
        self.words = [
            ("additionally", ["a", "di", "tion", "al", "ly"]),
            ("reconditioned", ["re", "con", "di", "tion", "ed"]),
            ("intercom", ["in", "ter", "com"]),
            ("exiting", ["ex", "i", "ing"]),
            ("ideally", ["i", "de", "a", "ly"]),
            ("happy", ["a", "y"]),
            ("openers", ["o", "e", "er", "es"])]
        self.speech = Speech(self.lip_shapes, self.words)

    def update(self, seconds):
        self.speech.update(seconds)
        self.face.shape_lips(*self.speech.lip_pose())
        self.face.build()

    def draw(self):
        self.face.draw()

