import os

from lib.laser_line import PictureTexture
from lib.picture_surface import PictureSurface

CHUCK_PEDDLE_IMAGE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources", "history", "mos",
                                       "peddle.jpg")


class ChuckPeddleSurface(PictureSurface):

	def __init__(self, screen_plane, height_in_screen_heights=0.45):
		super().__init__(PictureTexture.load(CHUCK_PEDDLE_IMAGE_PATH), screen_plane, height_in_screen_heights)

	def place_at_bottom_middle(self):
		self.place_center_at(self.center_fractions_with_bottom_edge_on_screen_bottom(0.5))

	def drift_to_top_right_corner(self, drift_seconds, margin_in_screen_heights=0.03):
		self.glide_center_to(self.center_fractions_in_top_right_corner(margin_in_screen_heights), drift_seconds)
