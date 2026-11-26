import pygame
from OpenGL.GL import *

from lib.unitra.shapes import (ChamferedBlock, CrtBezel, CrtGlass, DishedCap, Material,
                               QuadPainter, RearHood, Superellipse, WoodenBox)
from lib.unitra.textures import FontLibrary, LogoDecal, SurfaceTexture, WoodGrain


class ControlPanelLayout:

    def __init__(self, cabinet):
        self.right = cabinet.half_width
        self.top = cabinet.half_height
        self.height = cabinet.half_height * 2.0
        self.width = 0.355
        self.left = self.right - self.width
        self.logo_left = 0.081
        self.logo_middle = 0.058
        self.logo_height = 0.019
        self.caption = "T50 05"
        self.caption_left = 0.214
        self.caption_height = 0.0165
        self.grille_left = 0.051
        self.grille_right = 0.305
        self.grille_first_top = 0.095
        self.grille_pitch = 0.01844
        self.grille_slot_height = 0.0078
        self.grille_slot_count = 20
        self.plate_left = 0.051
        self.plate_right = 0.302
        self.plate_top = 0.508
        self.plate_bottom = 0.952
        self.text_height = 0.0062
        self.function_labels = ("tony wysokie", "słuchawki", "sieć")
        self.function_label_left = 0.062
        self.function_label_rows = (0.531, 0.548, 0.565)
        self.function_rule_rows = (0.5395, 0.5565)
        self.function_rule_right = 0.128
        self.function_button_centers = (0.169, 0.213, 0.257)
        self.function_button_row = 0.549
        self.function_button_size = (0.042, 0.038)
        self.slider_labels = ("jaskrawość", "kontrast", "siła głosu")
        self.slider_label_left = 0.062
        self.slider_rows = (0.620, 0.659, 0.698)
        self.scale_lift = 0.0215
        self.scale_marks = ("0", ".", "2", ".", "4", ".", "6", ".", "8", ".", "10")
        self.track_left = 0.130
        self.track_right = 0.276
        self.track_thickness = 0.0045
        self.section_divider = 0.737
        self.channel_number_row = 0.7505
        self.channel_button_centers = (0.093, 0.135, 0.177, 0.219, 0.261)
        self.channel_button_row = 0.779
        self.channel_button_size = (0.040, 0.040)
        self.lid_left = 0.054
        self.lid_right = 0.299
        self.lid_top = 0.814
        self.lid_bottom = 0.948
        self.button_well_margin = 0.004

    def model_point(self, across, down):
        return self.left + across, self.top - down

    def function_well(self):
        half_width, half_height = (size / 2.0 for size in self.function_button_size)
        return (self.function_button_centers[0] - half_width, self.function_button_row - half_height,
                self.function_button_centers[-1] + half_width, self.function_button_row + half_height)

    def channel_well(self):
        half_width, half_height = (size / 2.0 for size in self.channel_button_size)
        return (self.channel_button_centers[0] - half_width, self.channel_button_row - half_height,
                self.channel_button_centers[-1] + half_width, self.channel_button_row + half_height)


class PanelArtwork:

    def __init__(self, layout, fonts):
        self.layout = layout
        self.fonts = fonts
        self.pixels_per_unit = 3000
        self.background = (110, 72, 44, 0)
        self.print_color = (226, 222, 210)
        self.groove_color = (24, 17, 12)
        self.slot_color = (12, 10, 9)
        self.track_color = (6, 6, 6)
        self.well_color = (16, 14, 13)
        self.label_font_file = "arial.ttf"
        self.caption_font_file = "bahnschrift.ttf"
        self.cap_height_per_em = 0.716
        self.groove_width = 0.0028
        self.outline_width = 0.0016
        self.rule_width = 0.0007
        self.scale_dot_radius = 0.0011

    def pixels(self, units):
        return int(round(units * self.pixels_per_unit))

    def point(self, across, down):
        return self.pixels(across), self.pixels(down)

    def surface(self):
        surface = pygame.Surface((self.pixels(self.layout.width), self.pixels(self.layout.height)), pygame.SRCALPHA)
        surface.fill(self.background)
        self.draw_groove(surface)
        self.draw_logo(surface)
        self.draw_grille(surface)
        self.draw_plate(surface)
        self.draw_function_labels(surface)
        self.draw_slider_scales(surface)
        self.draw_channel_numbers(surface)
        return surface

    def label(self, text):
        font = self.fonts.font(self.label_font_file, max(8, self.pixels(self.layout.text_height / self.cap_height_per_em)))
        return font.render(text, True, self.print_color)

    def fitted(self, text, font_file, height):
        rendered = self.fonts.font(font_file, 160).render(text, True, self.print_color)
        glyphs = rendered.subsurface(rendered.get_bounding_rect())
        target_height = self.pixels(height)
        target_width = round(glyphs.get_width() * target_height / glyphs.get_height())
        return pygame.transform.smoothscale(glyphs, (target_width, target_height))

    def draw_groove(self, surface):
        pygame.draw.rect(surface, self.groove_color, (0, 0, self.pixels(self.groove_width), surface.get_height()))

    def draw_logo(self, surface):
        layout = self.layout
        logo = LogoDecal().surface()
        logo_height = self.pixels(layout.logo_height)
        logo_width = round(logo.get_width() * logo_height / logo.get_height())
        logo = pygame.transform.smoothscale(logo, (logo_width, logo_height))
        surface.blit(logo, logo.get_rect(midleft=self.point(layout.logo_left, layout.logo_middle)))
        caption = self.fitted(layout.caption, self.caption_font_file, layout.caption_height)
        surface.blit(caption, caption.get_rect(midleft=self.point(layout.caption_left, layout.logo_middle)))

    def draw_grille(self, surface):
        layout = self.layout
        left = self.pixels(layout.grille_left)
        width = self.pixels(layout.grille_right - layout.grille_left)
        height = self.pixels(layout.grille_slot_height)
        for slot in range(layout.grille_slot_count):
            top = self.pixels(layout.grille_first_top + slot * layout.grille_pitch)
            pygame.draw.rect(surface, self.slot_color, (left, top, width, height), border_radius=height // 2)

    def draw_plate(self, surface):
        layout = self.layout
        left, top = self.point(layout.plate_left, layout.plate_top)
        right, bottom = self.point(layout.plate_right, layout.plate_bottom)
        pygame.draw.rect(surface, self.groove_color, (left, top, right - left, bottom - top),
                         width=self.pixels(self.outline_width), border_radius=self.pixels(0.002))
        divider = self.pixels(layout.section_divider)
        pygame.draw.line(surface, self.groove_color, (left, divider), (right, divider), self.pixels(self.outline_width))
        for well in (layout.function_well(), layout.channel_well()):
            self.draw_well(surface, well)

    def draw_well(self, surface, well):
        margin = self.layout.button_well_margin
        left, top = self.point(well[0] - margin, well[1] - margin)
        right, bottom = self.point(well[2] + margin, well[3] + margin)
        pygame.draw.rect(surface, self.well_color, (left, top, right - left, bottom - top), border_radius=self.pixels(0.002))

    def draw_function_labels(self, surface):
        layout = self.layout
        for text, row in zip(layout.function_labels, layout.function_label_rows):
            rendered = self.label(text)
            surface.blit(rendered, rendered.get_rect(midleft=self.point(layout.function_label_left, row)))
        for row in layout.function_rule_rows:
            start = self.point(layout.function_label_left, row)
            end = self.point(layout.function_rule_right, row)
            pygame.draw.line(surface, self.print_color, start, end, max(1, self.pixels(self.rule_width)))

    def draw_slider_scales(self, surface):
        layout = self.layout
        for text, row in zip(layout.slider_labels, layout.slider_rows):
            rendered = self.label(text)
            surface.blit(rendered, rendered.get_rect(midleft=self.point(layout.slider_label_left, row)))
            left, top = self.point(layout.track_left, row - layout.track_thickness / 2.0)
            right, bottom = self.point(layout.track_right, row + layout.track_thickness / 2.0)
            pygame.draw.rect(surface, self.track_color, (left, top, right - left, bottom - top),
                             border_radius=(bottom - top) // 2)
            self.draw_scale(surface, row - layout.scale_lift)

    def draw_scale(self, surface, row):
        layout = self.layout
        step = (layout.track_right - layout.track_left) / (len(layout.scale_marks) - 1)
        for index, mark in enumerate(layout.scale_marks):
            center = self.point(layout.track_left + index * step, row)
            if mark == ".":
                pygame.draw.circle(surface, self.print_color, center, max(1, self.pixels(self.scale_dot_radius)))
            else:
                rendered = self.fitted(mark, self.label_font_file, layout.text_height)
                surface.blit(rendered, rendered.get_rect(center=center))

    def draw_channel_numbers(self, surface):
        layout = self.layout
        for number, across in enumerate(layout.channel_button_centers, start=1):
            rendered = self.fitted(str(number), self.label_font_file, layout.text_height)
            surface.blit(rendered, rendered.get_rect(center=self.point(across, layout.channel_number_row)))


class PanelDecal:

    def __init__(self, layout):
        self.layout = layout
        self.lift = 0.0008
        self.texture = None

    def render(self):
        if self.texture is None:
            self.texture = SurfaceTexture(PanelArtwork(self.layout, FontLibrary()).surface(), False)
        layout = self.layout
        bottom = layout.top - layout.height
        glEnable(GL_TEXTURE_2D)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glDepthMask(GL_FALSE)
        self.texture.bind()
        glColor3f(1.0, 1.0, 1.0)
        glBegin(GL_QUADS)
        QuadPainter.quad([(layout.left, bottom, self.lift), (layout.right, bottom, self.lift),
                          (layout.right, layout.top, self.lift), (layout.left, layout.top, self.lift)],
                         ((0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)))
        glEnd()
        glDepthMask(GL_TRUE)
        glDisable(GL_BLEND)
        glDisable(GL_TEXTURE_2D)

    def destroy(self):
        if self.texture is not None:
            self.texture.destroy()


class PushButton:

    def __init__(self, center, size, color):
        self.center = center
        self.color = color
        self.dish_color = tuple(channel * 0.9 for channel in color)
        self.block = ChamferedBlock(size[0], size[1], 0.024, 0.005)
        self.dish = DishedCap(0.36 * min(size), 1.3)
        self.pressed_depth = 0.011
        self.travel_speed = 0.12
        self.pressed = False
        self.inset = 0.0

    def press(self):
        self.pressed = True

    def release(self):
        self.pressed = False

    def toggle(self):
        self.pressed = not self.pressed

    def update(self, seconds):
        target = self.pressed_depth if self.pressed else 0.0
        step = self.travel_speed * seconds
        self.inset += max(-step, min(step, target - self.inset))

    def render(self):
        glPushMatrix()
        glTranslatef(self.center[0], self.center[1], -self.inset)
        glColor3f(*self.color)
        self.block.render()
        glTranslatef(0.0, 0.0, self.block.depth + 0.0005)
        glColor3f(*self.dish_color)
        self.dish.render()
        glPopMatrix()

    def destroy(self):
        self.block.destroy()
        self.dish.destroy()


class Slider:

    def __init__(self, start, end_x, value):
        self.start_x, self.row_y = start
        self.end_x = end_x
        self.lowest = 0.0
        self.highest = 10.0
        self.value = value
        self.target = value
        self.glide_speed = 20.0
        self.color = (0.06, 0.06, 0.065)
        self.knob = ChamferedBlock(0.034, 0.021, 0.019, 0.004)
        self.grip = ChamferedBlock(0.007, 0.025, 0.026, 0.002)

    def set(self, value):
        self.target = max(self.lowest, min(self.highest, value))

    def nudge(self, delta):
        self.set(self.target + delta)

    def update(self, seconds):
        step = self.glide_speed * seconds
        self.value += max(-step, min(step, self.target - self.value))

    def knob_x(self):
        fraction = (self.value - self.lowest) / (self.highest - self.lowest)
        return self.start_x + fraction * (self.end_x - self.start_x)

    def render(self):
        glPushMatrix()
        glTranslatef(self.knob_x(), self.row_y, 0.0)
        glColor3f(*self.color)
        self.knob.render()
        self.grip.render()
        glPopMatrix()

    def destroy(self):
        self.knob.destroy()
        self.grip.destroy()


class Lid:

    def __init__(self, layout, color):
        left, top = layout.model_point(layout.lid_left, layout.lid_top)
        right, bottom = layout.model_point(layout.lid_right, layout.lid_bottom)
        self.center = ((left + right) / 2.0, (top + bottom) / 2.0)
        self.color = color
        self.block = ChamferedBlock(right - left, top - bottom, 0.007, 0.0025)

    def render(self):
        glPushMatrix()
        glTranslatef(self.center[0], self.center[1], 0.0)
        glColor3f(*self.color)
        self.block.render()
        glPopMatrix()

    def destroy(self):
        self.block.destroy()


class ControlPanel:

    def __init__(self, layout):
        self.layout = layout
        self.button_black = (0.075, 0.075, 0.085)
        self.button_red = (0.86, 0.24, 0.12)
        self.lid_color = (0.12, 0.14, 0.19)
        self.plastic = Material(0.35, 40.0)
        self.function_buttons = [PushButton(layout.model_point(across, layout.function_button_row),
                                            layout.function_button_size, color)
                                 for across, color in zip(layout.function_button_centers,
                                                          (self.button_black, self.button_black, self.button_red))]
        self.treble_button, self.headphones_button, self.power_button = self.function_buttons
        self.channel_buttons = [PushButton(layout.model_point(across, layout.channel_button_row),
                                           layout.channel_button_size, self.button_black)
                                for across in layout.channel_button_centers]
        self.sliders = [Slider(layout.model_point(layout.track_left, row),
                               layout.model_point(layout.track_right, row)[0], value)
                        for row, value in zip(layout.slider_rows, (5.8, 5.2, 1.8))]
        self.brightness_slider, self.contrast_slider, self.volume_slider = self.sliders
        self.lid = Lid(layout, self.lid_color)
        self.artwork = PanelDecal(layout)
        self.channel_buttons[0].press()

    def select_channel(self, index):
        for number, button in enumerate(self.channel_buttons):
            button.pressed = number == index

    def channel(self):
        for number, button in enumerate(self.channel_buttons):
            if button.pressed:
                return number
        return None

    def moving_parts(self):
        return self.function_buttons + self.channel_buttons + self.sliders

    def update(self, seconds):
        for part in self.moving_parts():
            part.update(seconds)

    def render(self):
        self.artwork.render()
        self.plastic.apply()
        for part in self.moving_parts():
            part.render()
        self.lid.render()

    def destroy(self):
        for part in self.moving_parts():
            part.destroy()
        self.lid.destroy()
        self.artwork.destroy()


class CrtScreen:

    def __init__(self):
        self.center = (-0.19, 0.01)
        self.glass_outline = Superellipse(0.488, 0.415, 4.6)
        self.bezel_outline = Superellipse(0.531, 0.455, 4.2)
        self.rim_height = 0.012
        self.bulge = 0.034
        self.bezel_profile = ((0.0, 0.012), (0.15, 0.022), (0.45, 0.028), (0.8, 0.024), (0.95, 0.012), (1.0, 0.0))
        self.glass = CrtGlass(self.center, self.glass_outline, self.rim_height, self.bulge)
        self.bezel = CrtBezel(self.center, self.glass_outline, self.bezel_outline, self.bezel_profile)
        self.bezel_color = (0.04, 0.04, 0.045)
        self.dark_glass_color = (0.16, 0.18, 0.175)
        self.bezel_material = Material(0.5, 60.0)
        self.glass_reflection = 0.55
        self.glass_shininess = 90.0
        self.warm_up_seconds = 1.6
        self.cool_down_seconds = 0.35
        self.picture = None
        self.powered = False
        self.glow = 0.0

    def update(self, seconds):
        if self.powered:
            self.glow = min(1.0, self.glow + seconds / self.warm_up_seconds)
        else:
            self.glow = max(0.0, self.glow - seconds / self.cool_down_seconds)

    def render(self):
        self.bezel_material.apply()
        glColor3f(*self.bezel_color)
        self.bezel.render()
        if self.picture is not None and self.glow > 0.0:
            self.render_picture()
        else:
            Material(0.0, 1.0).apply()
            glColor3f(*self.dark_glass_color)
            self.glass.render()
        self.render_reflection()

    def render_picture(self):
        glDisable(GL_LIGHTING)
        glEnable(GL_TEXTURE_2D)
        self.picture.bind()
        glColor3f(*(self.dark_glass_color[index] + (1.0 - self.dark_glass_color[index]) * self.glow
                    for index in range(3)))
        self.glass.render()
        glDisable(GL_TEXTURE_2D)
        glEnable(GL_LIGHTING)

    def render_reflection(self):
        glDisable(GL_COLOR_MATERIAL)
        glMaterialfv(GL_FRONT_AND_BACK, GL_AMBIENT, (0.0, 0.0, 0.0, 1.0))
        glMaterialfv(GL_FRONT_AND_BACK, GL_DIFFUSE, (0.0, 0.0, 0.0, 1.0))
        Material(self.glass_reflection, self.glass_shininess).apply()
        glEnable(GL_BLEND)
        glBlendFunc(GL_ONE, GL_ONE)
        glDepthFunc(GL_LEQUAL)
        glDepthMask(GL_FALSE)
        self.glass.render()
        glDepthMask(GL_TRUE)
        glDepthFunc(GL_LESS)
        glDisable(GL_BLEND)
        glEnable(GL_COLOR_MATERIAL)

    def destroy(self):
        self.glass.destroy()
        self.bezel.destroy()


class Cabinet:

    def __init__(self):
        self.half_width = 0.8
        self.half_height = 0.5
        self.depth = 0.82
        self.hood_depth = 0.34
        self.hood_center = (-0.12, 0.0)
        self.hood_shrink = (0.5, 0.6)
        self.wood_material = Material(0.12, 18.0)
        self.hood_material = Material(0.2, 25.0)
        self.wood = None
        self.box = None
        self.hood = RearHood(self.half_width, self.half_height, self.depth, self.hood_depth,
                             self.hood_center, self.hood_shrink)

    def render(self):
        if self.wood is None:
            self.wood = WoodGrain().texture()
            self.box = WoodenBox(self.half_width, self.half_height, self.depth, self.wood)
        self.wood_material.apply()
        glEnable(GL_TEXTURE_2D)
        self.wood.bind()
        glColor3f(1.0, 1.0, 1.0)
        self.box.render()
        glDisable(GL_TEXTURE_2D)
        self.hood_material.apply()
        self.hood.render()

    def destroy(self):
        if self.wood is not None:
            self.wood.destroy()
            self.box.destroy()
        self.hood.destroy()


class Feet:

    def __init__(self, cabinet):
        self.cabinet = cabinet
        self.positions = (-0.57, 0.6)
        self.width = 0.07
        self.height = 0.045
        self.front_inset = 0.06
        self.back_inset = 0.06
        self.color = (0.05, 0.05, 0.05)
        self.length = cabinet.depth - self.front_inset - self.back_inset
        self.rail = ChamferedBlock(self.width, self.length, self.height, 0.012)
        self.material = Material(0.3, 30.0)

    def render(self):
        self.material.apply()
        glColor3f(*self.color)
        for x in self.positions:
            glPushMatrix()
            glTranslatef(x, -self.cabinet.half_height, -self.front_inset - self.length / 2.0)
            glRotatef(90.0, 1.0, 0.0, 0.0)
            self.rail.render()
            glPopMatrix()

    def destroy(self):
        self.rail.destroy()


class UnitraT50:

    def __init__(self):
        self.cabinet = Cabinet()
        self.layout = ControlPanelLayout(self.cabinet)
        self.screen = CrtScreen()
        self.panel = ControlPanel(self.layout)
        self.feet = Feet(self.cabinet)

    @property
    def height(self):
        return self.cabinet.half_height * 2.0 + self.feet.height

    def show(self, picture):
        self.screen.picture = picture

    @property
    def powered(self):
        return self.panel.power_button.pressed

    def toggle_power(self):
        self.panel.power_button.toggle()

    def toggle_treble(self):
        self.panel.treble_button.toggle()

    def toggle_headphones(self):
        self.panel.headphones_button.toggle()

    def select_channel(self, index):
        self.panel.select_channel(index)

    @property
    def channel(self):
        return self.panel.channel()

    @property
    def sliders(self):
        return self.panel.sliders

    def update(self, seconds):
        self.panel.update(seconds)
        self.screen.powered = self.powered
        self.screen.update(seconds)

    def render(self):
        glPushAttrib(GL_ALL_ATTRIB_BITS)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
        glEnable(GL_NORMALIZE)
        glEnable(GL_COLOR_MATERIAL)
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
        glLightModeli(GL_LIGHT_MODEL_COLOR_CONTROL, GL_SEPARATE_SPECULAR_COLOR)
        glShadeModel(GL_SMOOTH)
        glTexEnvi(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_MODULATE)
        self.cabinet.render()
        self.feet.render()
        self.panel.render()
        self.screen.render()
        glPopAttrib()

    def destroy(self):
        self.cabinet.destroy()
        self.panel.destroy()
        self.screen.destroy()
        self.feet.destroy()
