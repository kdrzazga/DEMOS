from OpenGL.GL import *

VERTEX_SOURCE = """
#version 120
varying vec2 texture_point;
void main() {
	texture_point = gl_MultiTexCoord0.xy;
	gl_Position = gl_ModelViewProjectionMatrix * gl_Vertex;
}
"""

FRAGMENT_SOURCE = """
#version 120
uniform sampler2D art;
uniform sampler2D paint_order;
uniform float progress;
uniform float opacity;
uniform float feather;
varying vec2 texture_point;
void main() {
	vec4 color = texture2D(art, texture_point);
	float order = texture2D(paint_order, texture_point).r;
	float paint_front = progress * (1.0 + feather);
	float coverage = clamp((paint_front - order) / feather, 0.0, 1.0);
	float wet_glow = coverage * (1.0 - coverage) * 0.6;
	vec3 sprayed = mix(color.rgb, vec3(1.0), wet_glow * step(0.001, progress) * (1.0 - step(1.0, progress)));
	gl_FragColor = vec4(sprayed, color.a * coverage * opacity);
}
"""


class SprayShader:

	def __init__(self):
		self.feather = 0.07
		self.program = self._link(self._compile(GL_VERTEX_SHADER, VERTEX_SOURCE),
		                          self._compile(GL_FRAGMENT_SHADER, FRAGMENT_SOURCE))
		self.progress_location = glGetUniformLocation(self.program, "progress")
		self.opacity_location = glGetUniformLocation(self.program, "opacity")
		self.feather_location = glGetUniformLocation(self.program, "feather")
		glUseProgram(self.program)
		glUniform1i(glGetUniformLocation(self.program, "art"), 0)
		glUniform1i(glGetUniformLocation(self.program, "paint_order"), 1)
		glUseProgram(0)

	@staticmethod
	def _compile(kind, source):
		shader = glCreateShader(kind)
		glShaderSource(shader, source)
		glCompileShader(shader)
		if not glGetShaderiv(shader, GL_COMPILE_STATUS):
			raise RuntimeError(glGetShaderInfoLog(shader).decode())
		return shader

	@staticmethod
	def _link(vertex_shader, fragment_shader):
		program = glCreateProgram()
		glAttachShader(program, vertex_shader)
		glAttachShader(program, fragment_shader)
		glLinkProgram(program)
		if not glGetProgramiv(program, GL_LINK_STATUS):
			raise RuntimeError(glGetProgramInfoLog(program).decode())
		return program

	def use(self):
		glUseProgram(self.program)
		glUniform1f(self.feather_location, self.feather)

	def apply(self, progress, opacity):
		glUniform1f(self.progress_location, progress)
		glUniform1f(self.opacity_location, opacity)

	@staticmethod
	def release():
		glUseProgram(0)
