"""CDTV-specific GLSL: gradient sky (also the reflection environment), light beam and granite rock."""
from demos.amiga.common.glsl import COMMON_GLSL

SKY_GLSL = """
uniform vec3 u_sky_top;
uniform vec3 u_sky_middle;
uniform vec3 u_sky_bottom;

vec3 sky_color(vec2 uv) {
	if (uv.y > 0.5) return mix(u_sky_middle, u_sky_top, smoothstep(0.5, 1.0, uv.y));
	return mix(u_sky_bottom, u_sky_middle, smoothstep(0.0, 0.5, uv.y));
}

vec4 environment(vec2 uv) { return vec4(sky_color(uv), 1.0); }
"""

SKY_FRAGMENT = COMMON_GLSL + SKY_GLSL + """
out vec4 frag_color;
void main() {
	vec2 uv = gl_FragCoord.xy / u_viewport;
	// a touch of dithering noise so the 8-bit gradient doesn't band
	float grain = (hash21(gl_FragCoord.xy) - 0.5) / 255.0;
	frag_color = vec4(sky_color(uv) + grain, 1.0);
}
"""

BEAM_FRAGMENT = COMMON_GLSL + """
uniform vec2  u_beam_origin;   // screen uv where the light leaves the disc
uniform float u_strength;
out vec4 frag_color;

void main() {
	float px = u_viewport.y / 720.0;
	vec2 offset = gl_FragCoord.xy - u_beam_origin * u_viewport;

	// thin horizontal laser line to the right edge, slowly fading
	float line = exp(-pow(offset.y / (1.4 * px), 2.0))
		* smoothstep(-2.0 * px, 2.0 * px, offset.x)
		* (1.0 - 0.5 * clamp(offset.x / u_viewport.x, 0.0, 1.0));

	// flare at the source: soft glow plus a fan of short rays toward the right
	float glow = exp(-length(offset) / (16.0 * px));
	float rays = 0.0;
	for (int k = 0; k < 5; k++) {
		float angle = -0.45 + 0.28 * float(k);
		vec2 direction = vec2(cos(angle), sin(angle));
		float along = dot(offset, direction);
		float across = dot(offset, vec2(-direction.y, direction.x));
		if (along > 0.0) {
			rays += exp(-pow(across / (1.2 * px + 0.05 * along), 2.0)) * exp(-along / (55.0 * px)) * (k == 2 ? 1.0 : 0.55);
		}
	}
	// dispersion off the disc: a soft spectrum fan spraying back from the hit point (violet low, red high)
	float fan_angle = atan(offset.y, offset.x);
	float fan_distance = length(offset);
	float fan_mask = smoothstep(-0.9, -0.5, fan_angle) * (1.0 - smoothstep(0.7, 1.1, fan_angle))
		* smoothstep(3.0 * px, 14.0 * px, fan_distance) * exp(-fan_distance / (70.0 * px));
	vec3 spectrum = hsv2rgb(vec3(0.78 * clamp(0.5 - fan_angle * 0.55, 0.0, 1.0), 0.8, 1.0));
	float fan_streaks = 0.6 + 0.4 * sin(fan_angle * 60.0 + u_time * 2.0);

	float flicker = 0.85 + 0.15 * sin(u_time * 13.0) * sin(u_time * 7.3);
	vec3 color = vec3(1.0, 0.93, 0.96) * (line * 0.85 + (glow * 0.8 + rays * 0.6) * flicker)
		+ spectrum * fan_mask * fan_streaks * 0.45 * flicker;
	color *= u_strength;
	frag_color = vec4(color, 0.0);
}
"""

ROCK_VERTEX = """
#version 330 core
layout(location = 0) in vec3 a_pos;     // world space (the rock mesh is baked)
layout(location = 1) in vec3 a_normal;
uniform mat4 u_view_projection;
out vec3 v_world;
out vec3 v_normal;
void main() {
	v_world = a_pos;
	v_normal = a_normal;
	gl_Position = u_view_projection * vec4(a_pos, 1.0);
}
"""

ROCK_FRAGMENT = COMMON_GLSL + SKY_GLSL + """
in vec3 v_world;
in vec3 v_normal;
uniform float u_grain_scale;
out vec4 frag_color;

// speckled granite: black base, grey and white quartz, pink feldspar, a few violet flecks
vec3 granite(vec3 p) {
	float fine = hash31(floor(p * u_grain_scale));
	float coarse = hash31(floor(p * u_grain_scale * 0.4) + 17.0);
	vec3 color = vec3(0.06, 0.05, 0.07);
	if (fine > 0.52) color = vec3(0.36, 0.34, 0.38);
	if (fine > 0.75) color = vec3(0.84, 0.82, 0.86);
	if (coarse > 0.86) color = mix(color, vec3(0.88, 0.60, 0.72), 0.8);
	if (fine < 0.05) color = vec3(0.52, 0.46, 0.80);
	return color;
}

void main() {
	vec3 normal = normalize(v_normal);
	vec3 to_light = normalize(vec3(0.35, 0.8, 0.5));
	float diffuse = max(dot(normal, to_light), 0.0);
	vec3 ambient = sky_color(vec2(0.5, 0.5 + 0.5 * normal.y));
	vec3 stone = granite(v_world);
	frag_color = vec4(stone * (0.15 + 1.05 * diffuse) + stone * ambient * 0.22, 1.0);
}
"""
