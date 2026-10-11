"""Shared GLSL for the Amiga intros.

Scene-specific shading plugs in through an "environment" snippet that must define
	vec4 environment(vec2 screen_uv)   // rgb = what a shiny surface reflects there, a = how much
The disc and the extruded glyphs mix that into their colour, so each intro gets its own reflections.
"""

COMMON_GLSL = """
#version 330 core
const float PI = 3.14159265;
uniform float u_time;
uniform vec2  u_viewport;

float hash21(vec2 p) {
	p = fract(p * vec2(123.34, 456.21));
	p += dot(p, p + 45.32);
	return fract(p.x * p.y);
}

float hash31(vec3 p) {
	p = fract(p * vec3(0.1031, 0.1030, 0.0973));
	p += dot(p, p.yzx + 33.33);
	return fract((p.x + p.y) * p.z);
}

float value_noise(vec2 p) {
	vec2 cell = floor(p);
	vec2 f = fract(p);
	vec2 u = f * f * (3.0 - 2.0 * f);
	return mix(mix(hash21(cell), hash21(cell + vec2(1, 0)), u.x),
	           mix(hash21(cell + vec2(0, 1)), hash21(cell + vec2(1, 1)), u.x), u.y);
}

float fbm(vec2 p) {
	float sum = 0.0;
	float amplitude = 0.5;
	for (int octave = 0; octave < 5; octave++) {
		sum += amplitude * value_noise(p);
		p = p * 2.03 + vec2(17.1, 9.7);
		amplitude *= 0.5;
	}
	return sum;
}

vec3 hsv2rgb(vec3 c) {
	vec3 p = abs(fract(c.xxx + vec3(0.0, 2.0 / 3.0, 1.0 / 3.0)) * 6.0 - 3.0);
	return c.z * mix(vec3(1.0), clamp(p - 1.0, 0.0, 1.0), c.y);
}
"""

FULLSCREEN_VERTEX = """
#version 330 core
layout(location = 0) in vec2 a_pos;
void main() { gl_Position = vec4(a_pos * 2.0 - 1.0, 0.0, 1.0); }
"""

FADE_FRAGMENT = """
#version 330 core
uniform float u_darkness;
out vec4 frag_color;
void main() { frag_color = vec4(0.0, 0.0, 0.0, u_darkness); }
"""

# --------------------------------------------------------------------------- compact disc

DISC_VERTEX = """
#version 330 core
layout(location = 0) in vec2 a_pos;   // unit quad 0..1 -> disc local -1..1
uniform mat4 u_mvp;
out vec2 v_local;
void main() {
	v_local = a_pos * 2.0 - 1.0;
	gl_Position = u_mvp * vec4(v_local, 0.0, 1.0);
}
"""

_DISC_FRAGMENT_BODY = """
in vec2 v_local;
uniform float u_light_angle;
uniform float u_spoke_strength;
uniform vec3  u_base_dark;
uniform vec3  u_base_light;
uniform vec2  u_sheen_direction;
uniform float u_reflect;
uniform vec2  u_environment_offset;
uniform float u_alpha;
uniform float u_hole_radius;
out vec4 frag_color;

float ring(float r, float inner, float outer, float aa) {
	return smoothstep(inner - aa, inner + aa, r) * (1.0 - smoothstep(outer - aa, outer + aa, r));
}

float angle_distance(float a, float b) {
	return abs(mod(a - b + PI, 2.0 * PI) - PI);
}

void main() {
	float r = length(v_local);
	float aa = fwidth(r) * 0.75;
	float coverage = (1.0 - smoothstep(1.0 - aa, 1.0 + aa, r)) * smoothstep(u_hole_radius - aa, u_hole_radius + aa, r);
	if (coverage <= 0.002) discard;
	float theta = atan(v_local.y, v_local.x);

	float sheen = smoothstep(-1.1, 1.1, dot(v_local, u_sheen_direction));
	vec3 color = mix(u_base_dark, u_base_light, sheen);

	// diffraction spokes: two strong opposite fans + two weaker ones, rainbow along the radius
	float spoke_weight = 0.0;
	vec3 spoke_color = vec3(0.0);
	for (int k = 0; k < 4; k++) {
		float center = u_light_angle + float(k) * PI * 0.5;
		float offset = angle_distance(theta, center);
		float width = 0.16 + 0.16 * r;
		float strength = (k % 2 == 0) ? 1.0 : 0.55;
		float weight = exp(-pow(offset / width, 2.0)) * strength * smoothstep(0.32, 0.45, r);
		float hue = fract(0.95 - r * 1.15 + offset / width * 0.22 + float(k) * 0.17 + u_time * 0.03);
		spoke_color += hsv2rgb(vec3(hue, 0.85, 1.0)) * weight;
		spoke_weight += weight;
	}
	if (spoke_weight > 0.0) {
		color = mix(color, spoke_color / spoke_weight, clamp(spoke_weight * u_spoke_strength, 0.0, 0.88));
	}

	vec2 screen_uv = gl_FragCoord.xy / u_viewport;
	vec4 reflected = environment(clamp(screen_uv + u_environment_offset, 0.0, 0.98));
	color = mix(color, color * 0.45 + reflected.rgb * 1.1, u_reflect * reflected.a);

	// hub rings and rim
	color = mix(color, vec3(0.86, 0.85, 0.88), ring(r, 0.33, 0.345, aa));
	color = mix(color, vec3(0.55, 0.55, 0.60), ring(r, 0.30, 0.33, aa));
	color = mix(color, vec3(0.05, 0.05, 0.07), ring(r, 0.17, 0.30, aa));
	color = mix(color, vec3(0.78, 0.78, 0.82), ring(r, 0.15, 0.17, aa));
	color = mix(color, vec3(0.10, 0.10, 0.12), ring(r, 0.0, 0.15, aa));
	color = mix(color, vec3(0.30, 0.30, 0.34), smoothstep(0.975, 0.99, r));

	frag_color = vec4(color, coverage * u_alpha);
}
"""


def disc_fragment(environment_glsl):
	return COMMON_GLSL + environment_glsl + _DISC_FRAGMENT_BODY


DISC_EDGE_VERTEX = """
#version 330 core
layout(location = 0) in vec3 a_pos;   // unit cylinder: (cos, sin, depth 0..1)
uniform mat4 u_mvp;
uniform float u_thickness;
out float v_angle;
void main() {
	v_angle = atan(a_pos.y, a_pos.x);
	gl_Position = u_mvp * vec4(a_pos.xy, -a_pos.z * u_thickness, 1.0);
}
"""

DISC_EDGE_FRAGMENT = """
#version 330 core
in float v_angle;
uniform float u_alpha;
out vec4 frag_color;
void main() {
	float light = 0.75 + 0.25 * sin(v_angle + 0.6);
	frag_color = vec4(vec3(0.93, 0.92, 0.95) * light, u_alpha);
}
"""

# --------------------------------------------------------------------------- extruded glyphs

GLYPH_VERTEX = """
#version 330 core
layout(location = 0) in vec2 a_pos;
layout(location = 1) in vec2 a_uv;
uniform mat4 u_mvp;
uniform vec2 u_size;
uniform float u_slant;
uniform float u_layer_z;
out vec2 v_uv;
void main() {
	vec3 p = vec3((a_pos - 0.5) * u_size, u_layer_z);
	p.x += p.y * u_slant;
	v_uv = a_uv;
	gl_Position = u_mvp * vec4(p, 1.0);
}
"""

GLYPH_PAINTED = 0       # gradient paint (CD32 "AMIGA")
GLYPH_CHROME = 1        # silver with a rainbow band (CD32 "CD")
GLYPH_SKY_CHROME = 2    # white chrome mirroring the environment (CDTV title)

_GLYPH_FRAGMENT_BODY = """
in vec2 v_uv;
uniform sampler2D u_glyph;
uniform mat3  u_normal_matrix;
uniform int   u_material;
uniform vec3  u_color_low;
uniform vec3  u_color_high;
uniform vec3  u_side_color;
uniform int   u_is_side;      // 1 = extrusion slice
uniform float u_layer_fraction;
uniform float u_alpha;
uniform float u_reflect;
out vec4 frag_color;

void main() {
	vec4 texel = texture(u_glyph, v_uv);
	if (texel.a < 0.04) discard;
	float coverage = smoothstep(0.35, 0.65, texel.a);

	if (u_is_side == 1) {
		frag_color = vec4(u_side_color * (0.55 + 0.45 * (1.0 - u_layer_fraction)), coverage * u_alpha);
		return;
	}

	vec3 normal = normalize(u_normal_matrix * (texel.rgb * 2.0 - 1.0));
	vec3 to_light = normalize(vec3(-0.45, 0.75, 0.55));
	vec3 to_eye = vec3(0.0, 0.0, 1.0);
	float diffuse = max(dot(normal, to_light), 0.0);
	float specular = pow(max(dot(reflect(-to_light, normal), to_eye), 0.0), 28.0);
	float bevel = 1.0 - normal.z;   // 0 on the flat face, grows on the bevelled rim
	vec2 screen_uv = gl_FragCoord.xy / u_viewport;
	vec3 color;

	if (u_material == 0) {
		vec4 reflected = environment(clamp(screen_uv + normal.xy * 0.06, 0.0, 1.0));
		vec3 base = mix(u_color_low, u_color_high, smoothstep(0.15, 0.85, v_uv.y));
		color = base * (0.62 + 0.5 * diffuse) + vec3(1.0, 0.85, 0.6) * specular * 0.7;
		color = mix(color, reflected.rgb * 1.35 + base * 0.15, u_reflect * reflected.a);
	} else if (u_material == 1) {
		vec4 reflected = environment(clamp(screen_uv + normal.xy * 0.06, 0.0, 1.0));
		float height = v_uv.y + normal.y * 0.35;
		vec3 silver = mix(u_color_low, u_color_high, smoothstep(0.2, 0.95, height));
		float band = exp(-pow((height - 0.47) / 0.11, 2.0));
		vec3 rainbow = hsv2rgb(vec3(fract(v_uv.x * 1.3 + height * 0.6 + u_time * 0.08), 0.55, 1.0));
		color = mix(silver, rainbow, band * 0.7);
		color *= 1.0 - bevel * 0.45;
		color += vec3(1.0) * specular * 0.6;
		color = mix(color, color * 0.4 + reflected.rgb * 1.2, u_reflect * 0.6 * reflected.a);
	} else {
		vec4 reflected = environment(clamp(screen_uv + normal.xy * 0.25 + vec2(0.0, 0.08), 0.0, 1.0));
		float rim = clamp(bevel * 2.2, 0.0, 1.0);
		vec3 face = mix(u_color_high, reflected.rgb, 0.25 + 0.2 * (1.0 - v_uv.y));
		color = mix(face, reflected.rgb * 0.85 + u_color_low * 0.25, rim);
		color = color * (0.75 + 0.35 * diffuse) + vec3(1.0) * specular * 0.8;
	}
	frag_color = vec4(color, coverage * u_alpha);
}
"""


def glyph_fragment(environment_glsl):
	return COMMON_GLSL + environment_glsl + _GLYPH_FRAGMENT_BODY

# --------------------------------------------------------------------------- flat-coloured lit meshes

COLORED_MESH_VERTEX = """
#version 330 core
layout(location = 0) in vec3 a_pos;
layout(location = 1) in vec3 a_normal;
layout(location = 2) in vec3 a_color;
uniform mat4 u_mvp;
uniform mat3 u_normal_matrix;
out vec3 v_normal;
out vec3 v_color;
void main() {
	v_normal = u_normal_matrix * a_normal;
	v_color = a_color;
	gl_Position = u_mvp * vec4(a_pos, 1.0);
}
"""

COLORED_MESH_FRAGMENT = """
#version 330 core
in vec3 v_normal;
in vec3 v_color;
uniform vec3  u_to_light;
uniform float u_shadow_level;   // brightness of faces turned away from the light
uniform float u_alpha;
out vec4 frag_color;
void main() {
	float light = mix(u_shadow_level, 1.0, max(dot(normalize(v_normal), u_to_light), 0.0));
	frag_color = vec4(v_color * light, u_alpha);
}
"""
