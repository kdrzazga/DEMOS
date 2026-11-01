import os

from OpenGL.GL import *

from lib.laser_line import PictureTexture
from lib.picture_surface import PictureSurface
from demos.forty_five.name_caption import NameCaption

CHUCK_PEDDLE_IMAGE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources", "history", "mos",
                                       "peddle.jpg")
CHUCK_PEDDLE_NAME_LINES = ("Charles", "Peddle")


class ChuckPeddleSurface(PictureSurface):

	def __init__(self, screen_plane, height_in_screen_heights=0.45):
		super().__init__(PictureTexture.load(CHUCK_PEDDLE_IMAGE_PATH), screen_plane, height_in_screen_heights)
		self.name_caption_line_height_in_screen_heights = 0.035
		self.name_caption_gap_in_screen_heights = 0.01
		self.name_caption = NameCaption(CHUCK_PEDDLE_NAME_LINES)
		self.name_caption.build()
		self.name_caption_visible = True

	def place_at_bottom_middle(self):
		self.place_center_at(self.center_fractions_with_bottom_edge_on_screen_bottom(0.5))

	def drift_to_top_right_corner(self, drift_seconds, margin_in_screen_heights=0.03):
		self.glide_center_to(self.center_fractions_in_top_right_corner(margin_in_screen_heights), drift_seconds)

	def draw(self):
		super().draw()
		if self.name_caption_visible:
			self._draw_name_caption()

	def _draw_name_caption(self):
		center_x, center_y = self.world_center_point
		visible_height = self.screen_plane.visible_height
		caption_top_y = center_y - self.picture_height / 2 - self.name_caption_gap_in_screen_heights * visible_height
		glPushAttrib(GL_ENABLE_BIT | GL_CURRENT_BIT | GL_COLOR_BUFFER_BIT)
		glDisable(GL_LIGHTING)
		glDisable(GL_DEPTH_TEST)
		glMatrixMode(GL_MODELVIEW)
		glPushMatrix()
		glLoadIdentity()
		self.name_caption.draw_below(center_x, caption_top_y, -self.screen_plane.camera_distance,
		                             self.name_caption_line_height_in_screen_heights * visible_height)
		glPopMatrix()
		glPopAttrib()

	def destroy(self):
		super().destroy()
		self.name_caption.destroy()
