import math

import arcade
import numpy as np
from arcade.gl import BufferDescription
from arcade.types import Color
from PIL import Image
from pyglet import gl as pgl

from demos.demo1 import Constants, Globals
from demos.demo1.base import Demo1Base
from demos.demo1.stage14 import Stage14


# ---------------------------------------------------------------------------
# Small row-major 4x4 / 3x3 matrix helpers (same math as shader/stripe.py).
# arcade.gl uploads matrices column-major with no transpose, so at upload time
# we hand it mat.T (see WavingFlag.render).
# ---------------------------------------------------------------------------

def _perspective(fovy, aspect, near, far):
	f = 1.0 / math.tan(fovy / 2.0)
	m = np.zeros((4, 4), dtype=np.float32)
	m[0, 0] = f / aspect
	m[1, 1] = f
	m[2, 2] = (far + near) / (near - far)
	m[2, 3] = (2.0 * far * near) / (near - far)
	m[3, 2] = -1.0
	return m


def _translate(x, y, z):
	m = np.identity(4, dtype=np.float32)
	m[0, 3], m[1, 3], m[2, 3] = x, y, z
	return m


def _rot_x(a):
	c, s = math.cos(a), math.sin(a)
	m = np.identity(4, dtype=np.float32)
	m[1, 1], m[1, 2] = c, -s
	m[2, 1], m[2, 2] = s, c
	return m


def _rot_y(a):
	c, s = math.cos(a), math.sin(a)
	m = np.identity(4, dtype=np.float32)
	m[0, 0], m[0, 2] = c, s
	m[2, 0], m[2, 2] = -s, c
	return m


_VERTEX_SRC = """
#version 330 core
in vec2 a_pos;   // grid position in the flat strip
in vec2 a_uv;

uniform mat4  u_mvp;
uniform mat3  u_normal;   // model rotation, for lighting the normals
uniform float u_time;

out vec2 v_uv;
out vec3 v_normal;

void main() {
	float x = a_pos.x;
	float y = a_pos.y;

	// Travelling wave along the strip (+ a gentle vertical ripple).
	float amp = 0.22;
	float k = 4.0;
	float speed = 3.0;
	float phase = k * x - speed * u_time;
	float z = amp * sin(phase) + 0.04 * sin(3.0 * y + speed * u_time);

	// Surface normal from the analytic slope of that wave.
	float dzdx = amp * k * cos(phase);
	float dzdy = 0.12 * cos(3.0 * y + speed * u_time);
	vec3 n = normalize(vec3(-dzdx, -dzdy, 1.0));

	gl_Position = u_mvp * vec4(x, y, z, 1.0);
	v_uv = a_uv;
	v_normal = normalize(u_normal * n);
}
"""

_FRAGMENT_SRC = """
#version 330 core
in vec2 v_uv;
in vec3 v_normal;
uniform sampler2D u_tex;
out vec4 fragColor;

void main() {
	vec4 tex = texture(u_tex, v_uv);
	if (tex.a < 0.1) discard;               // keep PNG transparency crisp

	// abs() so both faces of the flapping strip are lit.
	vec3 n = normalize(v_normal);
	vec3 lig = normalize(vec3(0.3, 0.5, 0.8));
	float dif = abs(dot(n, lig));

	vec3 col = tex.rgb * (dif * 0.8 + 0.35);
	fragColor = vec4(sqrt(col), tex.a);     // sqrt = quick gamma correction
}
"""


class WavingFlag:
	"""A subdivided strip that waves along its length, textured with a PNG.

	Ported from shader/stripe.py to Arcade's own GL context (arcade.gl) so it
	renders inside the existing arcade.Window instead of a separate pygame one.
	"""

	def __init__(self, texture_path, cols=140, rows=20, half_w=1.7):
		self.ctx = arcade.get_window().ctx
		self.cols = cols
		self.rows = rows
		self.half_w = half_w
		self.pos = (0.0, 0.0, 0.0)

		self.prog = self.ctx.program(
			vertex_shader=_VERTEX_SRC, fragment_shader=_FRAGMENT_SRC)

		image = Image.open(texture_path).convert("RGBA")
		aspect = image.width / image.height
		half_h = self.half_w / aspect                 # keep the PNG undistorted
		self.texture = self._upload_texture(image)
		self.geometry = self._build_mesh(half_h)

		self.prog["u_tex"] = 0

	def _upload_texture(self, image):
		# Flip to GL's bottom-left origin so the mesh UVs map upright.
		image = image.transpose(Image.FLIP_TOP_BOTTOM)
		tex = self.ctx.texture((image.width, image.height), components=4,
		                        data=image.tobytes())
		tex.filter = self.ctx.LINEAR, self.ctx.LINEAR
		tex.wrap_x = self.ctx.CLAMP_TO_EDGE
		tex.wrap_y = self.ctx.CLAMP_TO_EDGE
		return tex

	def _build_mesh(self, half_h):
		cols, rows = self.cols, self.rows
		xs = np.linspace(-self.half_w, self.half_w, cols)
		ys = np.linspace(-half_h, half_h, rows)

		verts = []
		for j in range(rows):
			for i in range(cols):
				verts += [xs[i], ys[j], i / (cols - 1), j / (rows - 1)]
		verts = np.array(verts, dtype=np.float32)

		indices = []
		for j in range(rows - 1):
			for i in range(cols - 1):
				a = j * cols + i
				b, c, d = a + 1, a + cols, a + cols + 1
				indices += [a, b, c, b, d, c]
		indices = np.array(indices, dtype=np.uint32)

		vbo = self.ctx.buffer(data=verts.tobytes())
		ibo = self.ctx.buffer(data=indices.tobytes())
		content = [BufferDescription(vbo, "2f 2f", ["a_pos", "a_uv"])]
		return self.ctx.geometry(content, index_buffer=ibo,
		                         index_element_size=4, mode=self.ctx.TRIANGLES)

	def render(self, aspect, t, z=4.0):
		# Model: slow yaw plus a slight tilt, exactly as the pygame reference.
		# z is the flag's distance in front of the camera; smaller z = nearer.
		model = (_translate(*self.pos)
		         @ _rot_y(0.5 * math.sin(t * 0.4)) @ _rot_x(-0.15))
		view = _translate(0.0, 0.0, -z)
		proj = _perspective(math.radians(45.0), aspect, 0.03, 30.0)
		mvp = proj @ view @ model
		normal_mat = np.ascontiguousarray(model[:3, :3])

		# arcade.gl uploads column-major without transposing -> hand it mat.T.
		self.prog["u_mvp"] = tuple(
			np.ascontiguousarray(mvp.T, dtype=np.float32).ravel())
		self.prog["u_normal"] = tuple(
			np.ascontiguousarray(normal_mat.T, dtype=np.float32).ravel())
		self.prog["u_time"] = float(t)

		self.texture.use(0)
		self.geometry.render(self.prog)


class Outro(Demo1Base):

	START_FRAME = Stage14.START_FRAME + 10
	DIMINISH_PHASE_FRAME = START_FRAME + 555

	def __init__(self):
		super().__init__()

		self.flag = WavingFlag(Constants.RES_PATH + "flag.png")

		# (text, appear-after-frame, line number, cursor x offset). Line numbers
		# >= 22 keep the credits in the lower half, below the waving flag.
		self.texts = (("THANKS FOR WATCHING", 60, 22, 2.5),
		              ("PLEASE VISIT WWW.KA-PLUS.PL", 180, 26, 3.5))

	def on_draw(self, frame):
		relative_frame = frame - Outro.START_FRAME

		self._draw_background()
		self._draw_flag(relative_frame)

		c = Color.from_hex_string(Constants.LIGHT_BLUE)
		self.type_with_cursor(c, 0, 22 * 12 + 5, relative_frame,
		                      Constants.WHITE, self.texts)

		if frame > Outro.DIMINISH_PHASE_FRAME:
			self.darken(frame)
			self.conditional_quit(frame)

	def _draw_background(self):
		# Cover the light-blue base main.py paints, so everything is black.
		arcade.draw_rect_filled(
			arcade.LBWH(0, 0, Constants.WIDTH, Constants.HEIGHT), color=(0, 0, 0))

	def _draw_flag(self, relative_frame):
		"""Render the 3D waving flag into the upper half of the world viewport.

		main.py has already activated scale_cam, so ctx.viewport is the
		letter-boxed rect for the 800x600 world; we shrink it to that rect's
		top half, draw, and restore it so the arcade text below is unaffected.
		"""
		ctx = self.flag.ctx
		saved_vp = ctx.viewport
		x, y, w, h = saved_vp
		top_h = h - h // 2
		ctx.viewport = (x, y + h // 2, w, top_h)

		ctx.enable(ctx.BLEND)
		ctx.enable(ctx.DEPTH_TEST)             # so wave folds overlap correctly
		pgl.glClear(pgl.GL_DEPTH_BUFFER_BIT)   # scissor-clipped to this world

		# Push-in: the flag moves forward as its z distance decreases. The zoom
		# finishes right as the screen starts to dim, so the closest view is
		# actually seen (the old span ran the close-up entirely under black).
		zoom_span = Outro.DIMINISH_PHASE_FRAME - Outro.START_FRAME
		progress = min(1.0, max(0.0, relative_frame / zoom_span))
		z = 6.0 - 5.2 * progress               # 6.0 (far) -> 0.8 (near)
		# Freeze the wave/yaw once fully zoomed so the huge close-up can't swing
		# through the camera as it fades out.
		t = min(relative_frame, zoom_span) / 60.0
		self.flag.render(w / top_h, t, z)
		ctx.disable(ctx.DEPTH_TEST)

		ctx.viewport = saved_vp

	def darken(self, frame):
		frames_since_diminish = frame - Outro.DIMINISH_PHASE_FRAME
		transparency = min(255, int(frames_since_diminish * 3.6))
		arcade.draw_rect_filled(
			arcade.LBWH(0, 0, Constants.WIDTH, Constants.HEIGHT),
			color=(0, 0, 0, transparency))

	def conditional_quit(self, frame):
		if frame > Outro.DIMINISH_PHASE_FRAME + 240:
			print()
			print(self.texts[0][0])
			print(self.texts[1][0])
			print()
			print("Bye !")
			print(Globals.get_duration())
			arcade.exit()

	def on_update(self, frame, delta_time):
		relative_frame = frame - Outro.START_FRAME
		if relative_frame == 1:
			print(self.__class__.__name__ + " ", Globals.get_duration(),
			      "[frame", str(frame) + "]")
