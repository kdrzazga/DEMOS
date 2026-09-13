import pygame
from OpenGL.GL import *


class City:
    def __init__(self, x, y, z, grid=(), spacing=0.0, name="City", sign_size=20, sign_side="east"):
        self.x = x
        self.y = y
        self.z = z
        self.grid = tuple(tuple(line) for line in grid)
        self.spacing = spacing
        self.name = name
        self.sign_margin = 6.0
        self.towns = tuple(town for line in self.grid for town in line if town is not None)
        self.rows = len(self.grid)
        self.columns = max((len(line) for line in self.grid), default=0)
        self.width = 0.0
        self.depth = 0.0
        self._arrange()
        self.sign = CityEntranceSign(self.name, sign_size, sign_side)
        self._place_sign()

    def _place_sign(self):
        offsets = {"E": (1.0, 0.0), "W": (-1.0, 0.0), "N": (0.0, -1.0), "S": (0.0, 1.0)}
        across, along = offsets.get(self.sign.nesw[:1], (1.0, 0.0))
        self.sign.x = across * (self.width / 2.0 + self.sign_margin)
        self.sign.z = along * (self.depth / 2.0 + self.sign_margin)

    def _column_widths(self):
        return tuple(max((line[column].width for line in self.grid
                          if column < len(line) and line[column] is not None), default=0.0)
                     for column in range(self.columns))

    def _row_depths(self):
        return tuple(max((town.depth for town in line if town is not None), default=0.0)
                     for line in self.grid)

    def _arrange(self):
        if not self.towns:
            return
        column_widths = self._column_widths()
        row_depths = self._row_depths()
        self.width = sum(column_widths) + self.spacing * (self.columns - 1)
        self.depth = sum(row_depths) + self.spacing * (self.rows - 1)
        cursor_z = -self.depth / 2.0
        for row, line in enumerate(self.grid):
            cursor_x = -self.width / 2.0
            for column in range(self.columns):
                town = line[column] if column < len(line) else None
                if town is not None:
                    town.x = cursor_x + column_widths[column] / 2.0
                    town.z = cursor_z + row_depths[row] / 2.0
                cursor_x += column_widths[column] + self.spacing
            cursor_z += row_depths[row] + self.spacing

    def town_at(self, row, column):
        if 0 <= row < self.rows and 0 <= column < len(self.grid[row]):
            return self.grid[row][column]
        return None

    def town_count(self):
        return len(self.towns)

    def quarter_count(self):
        return sum(len(town.quarters) for town in self.towns)

    def house_count(self):
        return sum(town.house_count() for town in self.towns)

    def tallest(self):
        return max((town.tallest() for town in self.towns), default=0.0)

    def draw(self):
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        for town in self.towns:
            town.draw()
        self.sign.draw()
        glPopMatrix()


class CityEntranceSign:
    def __init__(self, city_name: str, sign_size: int, nesw: str):
        self.city_name = city_name
        self.sign_size = sign_size
        self.nesw = nesw.upper()
        self.x = 0.0
        self.y = 0.0
        self.z = 0.0

        self.sign_yellow = (247, 196, 0)
        self.frame_black = (18, 18, 18)
        self.back_color = (0.42, 0.43, 0.45)
        self.post_color = (0.46, 0.47, 0.49)
        self.font_names = ("bahnschrift", "dinengschrift", "din1451", "arialnarrow", "arial")
        self.facings = {"N": 180.0, "E": 90.0, "S": 0.0, "W": 270.0}

        self.board_share = 0.34
        self.texture_height = 256
        self.corner_share = 0.08
        self.rim_share = 0.035
        self.frame_share = 0.04
        self.text_share = 0.42
        self.side_padding_share = 0.30
        self.board_thickness_share = 0.02
        self.post_width_share = 0.035
        self.post_inset_share = 0.2

        self.board_height = sign_size * self.board_share
        self.texture_id, texture_width = self._build_texture()
        self.board_width = self.board_height * texture_width / self.texture_height
        self.facing = self.facings.get(self.nesw[:1], 0.0)
        self.display_list = self._compile()

    def _load_font(self, pixel_height):
        for name in self.font_names:
            path = pygame.font.match_font(name)
            if path:
                return pygame.font.Font(path, pixel_height)
        return pygame.font.Font(None, pixel_height)

    def _build_texture(self):
        if not pygame.font.get_init():
            pygame.font.init()
        height = self.texture_height
        font = self._load_font(int(height * self.text_share))
        caption = font.render(self.city_name, True, self.frame_black)
        padding = int(height * self.side_padding_share)
        width = max(height, caption.get_width() + padding * 2)
        surface = pygame.Surface((width, height), pygame.SRCALPHA)
        outline = surface.get_rect()
        corner = int(height * self.corner_share)
        rim = max(1, int(height * self.rim_share))
        frame = max(1, int(height * self.frame_share))
        pygame.draw.rect(surface, self.sign_yellow, outline, border_radius=corner)
        pygame.draw.rect(surface, self.frame_black, outline.inflate(-2 * rim, -2 * rim),
                         width=frame, border_radius=max(0, corner - rim))
        surface.blit(caption, caption.get_rect(center=outline.center))
        pixels = pygame.image.tobytes(surface, "RGBA", True)
        texture_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, texture_id)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, pixels)
        return texture_id, width

    def _draw_box(self, left, right, bottom, top, back, front, color, closed_front=True):
        glColor3f(*color)
        glBegin(GL_QUADS)
        if closed_front:
            glNormal3f(0.0, 0.0, 1.0)
            glVertex3f(left, bottom, front)
            glVertex3f(right, bottom, front)
            glVertex3f(right, top, front)
            glVertex3f(left, top, front)
        glNormal3f(0.0, 0.0, -1.0)
        glVertex3f(right, bottom, back)
        glVertex3f(left, bottom, back)
        glVertex3f(left, top, back)
        glVertex3f(right, top, back)
        glNormal3f(1.0, 0.0, 0.0)
        glVertex3f(right, bottom, front)
        glVertex3f(right, bottom, back)
        glVertex3f(right, top, back)
        glVertex3f(right, top, front)
        glNormal3f(-1.0, 0.0, 0.0)
        glVertex3f(left, bottom, back)
        glVertex3f(left, bottom, front)
        glVertex3f(left, top, front)
        glVertex3f(left, top, back)
        glNormal3f(0.0, 1.0, 0.0)
        glVertex3f(left, top, front)
        glVertex3f(right, top, front)
        glVertex3f(right, top, back)
        glVertex3f(left, top, back)
        glEnd()

    def _draw_posts(self, board_back):
        half_post = self.sign_size * self.post_width_share / 2.0
        spread = self.board_width / 2.0 - self.board_width * self.post_inset_share / 2.0
        for side in (-1.0, 1.0):
            center = side * spread
            self._draw_box(center - half_post, center + half_post, 0.0, self.sign_size,
                           board_back - half_post * 2.0, board_back, self.post_color)

    def _draw_board(self):
        half_width = self.board_width / 2.0
        top = self.sign_size
        bottom = top - self.board_height
        thickness = self.sign_size * self.board_thickness_share
        self._draw_box(-half_width, half_width, bottom, top, -thickness, 0.0, self.back_color, closed_front=False)
        glDisable(GL_LIGHTING)
        glEnable(GL_TEXTURE_2D)
        glEnable(GL_ALPHA_TEST)
        glAlphaFunc(GL_GREATER, 0.5)
        glBindTexture(GL_TEXTURE_2D, self.texture_id)
        glTexEnvf(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_REPLACE)
        glBegin(GL_QUADS)
        glTexCoord2f(0.0, 0.0)
        glVertex3f(-half_width, bottom, 0.01)
        glTexCoord2f(1.0, 0.0)
        glVertex3f(half_width, bottom, 0.01)
        glTexCoord2f(1.0, 1.0)
        glVertex3f(half_width, top, 0.01)
        glTexCoord2f(0.0, 1.0)
        glVertex3f(-half_width, top, 0.01)
        glEnd()
        glTexEnvf(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_MODULATE)
        glDisable(GL_ALPHA_TEST)
        glDisable(GL_TEXTURE_2D)
        glEnable(GL_LIGHTING)
        return -thickness

    def _compile(self):
        display_list = glGenLists(1)
        glNewList(display_list, GL_COMPILE)
        board_back = self._draw_board()
        self._draw_posts(board_back)
        glEndList()
        return display_list

    def draw(self):
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        glRotatef(self.facing, 0.0, 1.0, 0.0)
        glCallList(self.display_list)
        glPopMatrix()
