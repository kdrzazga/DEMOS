"""CD32-specific GLSL: the rainbow waves (also the reflection environment) and the starfield."""
from demos.amiga.common.glsl import COMMON_GLSL

AURORA_GLSL = """
#define MAX_PULSES 8
uniform int   u_pulse_count;
uniform vec4  u_pulse_timing[MAX_PULSES];  // start, travel time across band, colour duration, band (0 sky, 1 ground)
uniform vec4  u_pulse_look[MAX_PULSES];    // hue at wave front, hue at tail, saturation, brightness
uniform float u_sky_horizon;               // screen v (0 = bottom) where the sky band starts
uniform float u_ground_horizon;            // screen v where the ground band starts

// Premultiplied colour of the rainbow waves at screen uv (0..1).
vec4 aurora(vec2 uv) {
	float aspect = u_viewport.x / u_viewport.y;
	float x = (uv.x - 0.5) * aspect;
	vec3 color = vec3(0.0);
	float alpha = 0.0;
	for (int i = 0; i < u_pulse_count; i++) {
		vec4 timing = u_pulse_timing[i];
		vec4 look = u_pulse_look[i];
		float elapsed = u_time - timing.x;
		if (elapsed < 0.0 || elapsed > timing.y * 1.3 + timing.z) continue;

		float depth;
		vec2 cloud;
		if (timing.w < 0.5) {
			float ridge = u_sky_horizon + 0.045 * (fbm(vec2(x * 5.0, 1.7)) - 0.45) + 0.012 * value_noise(vec2(x * 23.0, 4.0));
			if (uv.y < ridge) continue;
			depth = (uv.y - ridge) / (1.0 - u_sky_horizon);
			cloud = vec2(x * 2.2, depth * 2.6);
		} else {
			float ridge = u_ground_horizon + 0.04 * (fbm(vec2(x * 4.0, 8.3)) - 0.45);
			if (uv.y > ridge) continue;
			depth = (ridge - uv.y) / u_ground_horizon;
			// ground plane: features grow toward the viewer (bottom of screen)
			cloud = vec2(x * 2.6 / (0.45 + depth * 1.6), 1.6 / (0.25 + depth));
		}
		vec2 drift = vec2(u_time * 0.12, -u_time * 0.05) + float(i) * 3.7;
		float wobble = fbm(cloud + drift);
		float front_depth = max(depth + 0.32 * (wobble - 0.5), 0.0);
		float phase = (elapsed - front_depth * timing.y) / timing.z;
		if (phase < 0.0 || phase > 1.0) continue;

		float envelope = smoothstep(0.0, 0.05, phase) * (1.0 - smoothstep(0.72, 1.0, phase));
		float density = smoothstep(0.2, 0.8, fbm(cloud * 1.8 - drift * 1.3));
		float hue = mix(look.x, look.y, phase) + 0.07 * (wobble - 0.5);
		vec3 wave_color = hsv2rgb(vec3(fract(hue), look.z, look.w * (0.55 + 0.45 * density)));
		float wave_alpha = envelope * (0.45 + 0.55 * density);
		color = color * (1.0 - wave_alpha) + wave_color * wave_alpha;
		alpha = alpha + wave_alpha * (1.0 - alpha);
	}
	return vec4(color, alpha);
}

vec4 environment(vec2 uv) { return aurora(uv); }
"""

AURORA_FRAGMENT = COMMON_GLSL + AURORA_GLSL + """
out vec4 frag_color;
void main() {
	frag_color = aurora(gl_FragCoord.xy / u_viewport);
}
"""

STARS_VERTEX = """
#version 330 core
layout(location = 0) in vec2 a_pos;      // NDC
layout(location = 1) in float a_size;    // pixels at 720p
layout(location = 2) in float a_sparkle; // 0 dot, 1 cross
layout(location = 3) in float a_phase;
uniform float u_time;
uniform float u_pixel_scale;
out float v_sparkle;
out float v_brightness;
void main() {
	gl_Position = vec4(a_pos, 0.0, 1.0);
	gl_PointSize = a_size * u_pixel_scale;
	v_sparkle = a_sparkle;
	v_brightness = 0.65 + 0.35 * sin(u_time * (1.3 + a_phase) + a_phase * 6.28);
}
"""

STARS_FRAGMENT = """
#version 330 core
in float v_sparkle;
in float v_brightness;
uniform float u_fade;
out vec4 frag_color;
void main() {
	vec2 p = gl_PointCoord * 2.0 - 1.0;
	float intensity;
	if (v_sparkle > 0.5) {
		float horizontal = smoothstep(0.28, 0.0, abs(p.y)) * (1.0 - abs(p.x));
		float vertical = smoothstep(0.28, 0.0, abs(p.x)) * (1.0 - abs(p.y));
		intensity = max(horizontal, vertical) + smoothstep(0.35, 0.0, length(p));
	} else {
		intensity = smoothstep(1.0, 0.2, length(p)) * 0.7;
	}
	float alpha = clamp(intensity, 0.0, 1.0) * v_brightness * u_fade;
	frag_color = vec4(vec3(0.95, 0.95, 1.0) * alpha, alpha);
}
"""
