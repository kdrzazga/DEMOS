import math

from OpenGL.GL import *
from OpenGL.GLU import gluLookAt, gluPerspective

from lib.rainy_window import ShaderProgram

VERTEX_SOURCE = """
#version 120
void main() {
    gl_Position = vec4(gl_Vertex.xy, 0.0, 1.0);
}
"""

FRAGMENT_SOURCE = """
#version 120
#define GEOMETRY_OCTAVES {geometry_octaves}
#define DETAIL_OCTAVES {detail_octaves}
#define MARCH_STEPS {march_steps}
#define REFINEMENT_STEPS {refinement_steps}
#define NOTHING 1e9
uniform sampler2D scene_color;
uniform sampler2D scene_depth;
uniform float scene_near;
uniform float scene_far;
uniform vec2 resolution;
uniform vec3 eye;
uniform float eye_underwater;
uniform vec3 right_axis;
uniform vec3 up_axis;
uniform vec3 forward_axis;
uniform float lens_zoom;
uniform float time;
uniform float wave_height;
uniform float first_frequency;
uniform float frequency_growth;
uniform float amplitude_falloff;
uniform float first_angle;
uniform float angle_step;
uniform float choppiness;
uniform float gravity;
uniform float amplitude_total;
uniform float crest_mean;
uniform float surface_top;
uniform float surface_bottom;
uniform vec3 sun_direction;
uniform vec3 sun_color;
uniform vec3 zenith_color;
uniform vec3 horizon_color;
uniform vec3 crest_water_color;
uniform float far_distance;
uniform float fog_density;
uniform float exposure;
uniform float detail_fade;
uniform float seabed_level;
uniform vec3 seabed_color;
uniform float underwater_density;
uniform vec3 light_absorption;
uniform vec3 underwater_color;
uniform vec3 abyss_color;
uniform float refraction_shift;

float waves(vec2 point, int octaves) {
    float total = 0.0;
    float amplitude = 1.0;
    float frequency = first_frequency;
    float angle = first_angle;
    for (int octave = 0; octave < DETAIL_OCTAVES; octave++) {
        if (octave >= octaves) break;
        vec2 heading = vec2(cos(angle), sin(angle));
        float phase = dot(heading, point) * frequency + time * sqrt(gravity * frequency);
        float crest = exp(sin(phase) - 1.0);
        total += crest * amplitude;
        point -= heading * crest * cos(phase) * amplitude * choppiness / frequency;
        amplitude *= amplitude_falloff;
        frequency *= frequency_growth;
        angle += angle_step;
    }
    return (total / amplitude_total - crest_mean) * wave_height;
}

vec3 sky(vec3 direction, float sun_disc_strength) {
    float above = max(direction.y, 0.0);
    vec3 color = mix(horizon_color, zenith_color, pow(above, 0.45));
    float sun_facing = max(dot(direction, sun_direction), 0.0);
    color += sun_color * (pow(sun_facing, 6.0) * 0.3 + pow(sun_facing, 90.0) * 0.6);
    color += sun_color * smoothstep(0.99986, 0.99993, sun_facing) * sun_disc_strength;
    return color;
}

vec3 haze_toward(vec3 ray) {
    return sky(normalize(vec3(ray.x, 0.015, ray.z)), 0.0);
}

float gap_at(vec3 ray, float distance_along) {
    vec3 point = eye + ray * distance_along;
    return point.y - waves(point.xz, GEOMETRY_OCTAVES);
}

float march(vec3 ray, float near_distance, float far_distance_of_ray, float side) {
    float previous_distance = near_distance;
    if (side * gap_at(ray, near_distance) < 0.0) return near_distance;
    for (int march_step = 1; march_step <= MARCH_STEPS; march_step++) {
        float fraction = float(march_step) / float(MARCH_STEPS);
        float distance_along = mix(near_distance, far_distance_of_ray, fraction * fraction);
        if (side * gap_at(ray, distance_along) < 0.0) {
            float before = previous_distance;
            float after = distance_along;
            for (int refinement = 0; refinement < REFINEMENT_STEPS; refinement++) {
                float middle = 0.5 * (before + after);
                if (side * gap_at(ray, middle) < 0.0) after = middle; else before = middle;
            }
            return 0.5 * (before + after);
        }
        previous_distance = distance_along;
    }
    return -1.0;
}

vec3 surface_normal(vec2 point, float distance_along) {
    float spacing = 0.02 + distance_along * 0.0018;
    float height = waves(point, DETAIL_OCTAVES);
    float east = waves(point + vec2(spacing, 0.0), DETAIL_OCTAVES);
    float south = waves(point + vec2(0.0, spacing), DETAIL_OCTAVES);
    vec3 normal = normalize(vec3(height - east, spacing, height - south));
    float flattening = smoothstep(0.0, far_distance, distance_along) * detail_fade;
    return normalize(mix(normal, vec3(0.0, 1.0, 0.0), flattening));
}

float scene_distance(vec2 screen_point, vec3 ray) {
    float depth = texture2D(scene_depth, screen_point).r;
    if (depth >= 1.0) return NOTHING;
    float device_depth = depth * 2.0 - 1.0;
    float view_depth = 2.0 * scene_near * scene_far / (scene_far + scene_near - device_depth * (scene_far - scene_near));
    return view_depth / dot(ray, forward_axis);
}

vec3 scene_at(vec2 screen_point) {
    return pow(texture2D(scene_color, screen_point).rgb, vec3(2.2));
}

vec3 sunlit_at_depth(vec3 color, float height) {
    return color * exp(-max(-height, 0.0) * light_absorption);
}

vec3 water_fog(vec3 ray, float depth_below_surface) {
    float upward = clamp(ray.y * 0.5 + 0.5, 0.0, 1.0);
    vec3 color = mix(abyss_color, underwater_color, upward * upward);
    vec3 toward_sun = -refract(-sun_direction, vec3(0.0, 1.0, 0.0), 1.0 / 1.33);
    color += sun_color * pow(max(dot(ray, toward_sun), 0.0), 6.0) * 0.12;
    return sunlit_at_depth(color, -depth_below_surface);
}

vec3 seen_through_water(vec3 color, float travelled, vec3 ray, float depth_below_surface) {
    float transmittance = exp(-travelled * underwater_density);
    return color * transmittance + water_fog(ray, depth_below_surface) * (1.0 - transmittance);
}

vec3 seabed_lit() {
    return seabed_color * (0.35 + 0.65 * max(sun_direction.y, 0.0));
}

vec3 water_surface(vec3 ray, float distance_along, vec2 screen_point, float scene_along) {
    vec3 point = eye + ray * distance_along;
    vec3 normal = surface_normal(point.xz, distance_along);
    vec3 reflected = reflect(ray, normal);
    reflected.y = abs(reflected.y);
    float facing = max(dot(normal, -ray), 0.0);
    float fresnel = 0.02 + 0.98 * pow(1.0 - facing, 5.0);
    float crest_fraction = clamp((point.y - surface_bottom) / (surface_top - surface_bottom), 0.0, 1.0);
    float sun_light = max(dot(normal, sun_direction), 0.0);
    vec3 into_water = refract(ray, normal, 1.0 / 1.33);
    vec3 below;
    float travelled;
    vec2 shifted_point = screen_point + normal.xz * refraction_shift;
    float shifted_along = scene_distance(shifted_point, ray);
    if (shifted_along < NOTHING && shifted_along > distance_along) {
        float submerged_height = eye.y + ray.y * shifted_along;
        below = sunlit_at_depth(scene_at(shifted_point), submerged_height);
        travelled = shifted_along - distance_along;
    } else if (scene_along < NOTHING && scene_along > distance_along) {
        float submerged_height = eye.y + ray.y * scene_along;
        below = sunlit_at_depth(scene_at(screen_point), submerged_height);
        travelled = scene_along - distance_along;
    } else {
        below = sunlit_at_depth(seabed_lit(), seabed_level);
        travelled = (seabed_level - point.y) / min(into_water.y, -0.05);
    }
    vec3 underwater = seen_through_water(below, travelled, into_water, 0.0) * (0.5 + 0.5 * sun_light)
        + crest_water_color * pow(crest_fraction, 2.5) * (0.3 + 0.7 * sun_light);
    vec3 reflection = sky(reflected, 60.0);
    float highlight = pow(max(dot(reflected, sun_direction), 0.0), 600.0) * 3.0;
    return mix(underwater, reflection, fresnel) + sun_color * highlight;
}

vec3 view_from_air(vec3 ray, vec2 screen_point, float scene_along) {
    float water_along = -1.0;
    if (ray.y < 0.0 || eye.y < surface_top) {
        float near_distance = eye.y > surface_top ? (surface_top - eye.y) / ray.y : 0.0;
        float far_distance_of_ray = ray.y < 0.0 ? min((surface_bottom - eye.y) / ray.y, far_distance) : far_distance;
        if (near_distance < far_distance) water_along = march(ray, near_distance, far_distance_of_ray, 1.0);
    }
    if (scene_along < NOTHING && (water_along < 0.0 || scene_along < water_along)) {
        return mix(scene_at(screen_point), haze_toward(ray), 1.0 - exp(-scene_along * fog_density));
    }
    if (water_along >= 0.0) {
        float fog = 1.0 - exp(-water_along * fog_density);
        return mix(water_surface(ray, water_along, screen_point, scene_along), haze_toward(ray), fog);
    }
    if (ray.y < 0.0) return haze_toward(ray);
    return sky(ray, 40.0);
}

vec3 view_from_water(vec3 ray, vec2 screen_point, float scene_along) {
    float eye_depth = max(-eye.y, 0.0);
    float surface_along = -1.0;
    if (ray.y > 0.0) {
        float top_along = min((surface_top - eye.y) / ray.y, far_distance);
        surface_along = march(ray, 0.0, top_along, -1.0);
    }
    float seabed_along = ray.y < 0.0 ? (seabed_level - eye.y) / ray.y : NOTHING;
    float surface_or_seabed = surface_along >= 0.0 ? surface_along : seabed_along;
    if (scene_along < NOTHING && scene_along < surface_or_seabed) {
        vec3 point = eye + ray * scene_along;
        return seen_through_water(sunlit_at_depth(scene_at(screen_point), point.y), scene_along, ray, eye_depth);
    }
    if (surface_along >= 0.0) {
        vec3 point = eye + ray * surface_along;
        vec3 normal = surface_normal(point.xz, surface_along);
        vec3 into_air = refract(ray, -normal, 1.33);
        vec3 surface_color = dot(into_air, into_air) < 0.001
            ? water_fog(reflect(ray, -normal), 0.0)
            : sky(into_air, 40.0) * 0.85;
        return seen_through_water(surface_color, surface_along, ray, eye_depth);
    }
    if (seabed_along < NOTHING) {
        return seen_through_water(sunlit_at_depth(seabed_lit(), seabed_level), seabed_along, ray, eye_depth);
    }
    return water_fog(ray, eye_depth);
}

void main() {
    vec2 screen_point = gl_FragCoord.xy / resolution;
    vec2 screen = (gl_FragCoord.xy * 2.0 - resolution) / resolution.y;
    vec3 ray = normalize(forward_axis * lens_zoom + right_axis * screen.x + up_axis * screen.y);
    float scene_along = scene_distance(screen_point, ray);
    vec3 color = eye_underwater > 0.5
        ? view_from_water(ray, screen_point, scene_along)
        : view_from_air(ray, screen_point, scene_along);
    color = vec3(1.0) - exp(-color * exposure);
    gl_FragColor = vec4(pow(color, vec3(1.0 / 2.2)), 1.0);
}
"""


class SceneTarget:

    def __init__(self, size):
        self.size = size
        self.previous_framebuffer = 0
        self.color_texture = self.make_texture(GL_RGBA8, GL_RGBA, GL_UNSIGNED_BYTE, GL_LINEAR)
        self.depth_texture = self.make_texture(GL_DEPTH_COMPONENT24, GL_DEPTH_COMPONENT, GL_FLOAT, GL_NEAREST)
        self.framebuffer = glGenFramebuffers(1)
        self.begin()
        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, self.color_texture, 0)
        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, GL_TEXTURE_2D, self.depth_texture, 0)
        if glCheckFramebufferStatus(GL_FRAMEBUFFER) != GL_FRAMEBUFFER_COMPLETE:
            raise RuntimeError("sea scene target is incomplete")
        self.end()

    def make_texture(self, internal_format, pixel_format, pixel_type, filtering):
        texture = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, texture)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, filtering)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, filtering)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
        glTexImage2D(GL_TEXTURE_2D, 0, internal_format, self.size[0], self.size[1], 0, pixel_format, pixel_type, None)
        glBindTexture(GL_TEXTURE_2D, 0)
        return texture

    def begin(self):
        self.previous_framebuffer = int(glGetIntegerv(GL_FRAMEBUFFER_BINDING))
        glBindFramebuffer(GL_FRAMEBUFFER, self.framebuffer)

    def end(self):
        glBindFramebuffer(GL_FRAMEBUFFER, self.previous_framebuffer)


class Sea:

    def __init__(self, window_size):
        self.window_size = window_size
        self.time = 0.0
        self.field_of_view_degrees = 70.0
        self.wave_height = 7.0
        self.first_wavelength = 130.0
        self.frequency_growth = 1.18
        self.amplitude_falloff = 0.82
        self.first_angle = 0.4
        self.angle_step = 2.399963
        self.choppiness = 0.38
        self.gravity = 9.81
        self.geometry_octaves = 12
        self.detail_octaves = 34
        self.march_steps = 90
        self.refinement_steps = 8
        self.sun_elevation_degrees = 9.0
        self.sun_azimuth_degrees = 0.0
        self.sun_color = (1.0, 0.72, 0.45)
        self.zenith_color = (0.05, 0.12, 0.30)
        self.horizon_color = (0.55, 0.52, 0.55)
        self.crest_water_color = (0.02, 0.09, 0.10)
        self.far_distance = 7000.0
        self.fog_density = 0.00028
        self.exposure = 1.5
        self.detail_fade = 0.55
        self.seabed_depth = 80.0
        self.seabed_color = (0.30, 0.27, 0.20)
        self.underwater_density = 0.038
        self.light_absorption = (0.075, 0.028, 0.018)
        self.underwater_color = (0.03, 0.17, 0.21)
        self.abyss_color = (0.002, 0.018, 0.04)
        self.refraction_shift = 0.025
        self.scene_near = 0.3
        self.scene_far = 4000.0
        self.scene_ambient = (0.32, 0.36, 0.44, 1.0)
        self.crest_mean = math.exp(-1.0) * self.bessel_i0_of_one()
        self.amplitude_total = sum(self.amplitude_falloff ** octave for octave in range(self.geometry_octaves))
        self.surface_top = (1.0 - self.crest_mean) * self.wave_height
        self.surface_bottom = (math.exp(-2.0) - self.crest_mean) * self.wave_height
        self.scene_target = SceneTarget(window_size)
        self.program = ShaderProgram(VERTEX_SOURCE, FRAGMENT_SOURCE.replace("{geometry_octaves}", str(self.geometry_octaves))
                                     .replace("{detail_octaves}", str(self.detail_octaves))
                                     .replace("{march_steps}", str(self.march_steps))
                                     .replace("{refinement_steps}", str(self.refinement_steps)))

    @staticmethod
    def bessel_i0_of_one():
        return sum(1.0 / (4.0 ** term * math.factorial(term) ** 2) for term in range(12))

    @property
    def first_frequency(self):
        return 2.0 * math.pi / self.first_wavelength

    @property
    def seabed_level(self):
        return -self.seabed_depth

    @property
    def sun_direction(self):
        elevation = math.radians(self.sun_elevation_degrees)
        azimuth = math.radians(self.sun_azimuth_degrees)
        return (math.sin(azimuth) * math.cos(elevation), math.sin(elevation), -math.cos(azimuth) * math.cos(elevation))

    def update(self, seconds):
        self.time += seconds

    def surface_height(self, x, z):
        total = 0.0
        amplitude = 1.0
        frequency = self.first_frequency
        angle = self.first_angle
        for _ in range(self.geometry_octaves):
            heading_x, heading_z = math.cos(angle), math.sin(angle)
            phase = (heading_x * x + heading_z * z) * frequency + self.time * math.sqrt(self.gravity * frequency)
            crest = math.exp(math.sin(phase) - 1.0)
            total += crest * amplitude
            push = crest * math.cos(phase) * amplitude * self.choppiness / frequency
            x -= heading_x * push
            z -= heading_z * push
            amplitude *= self.amplitude_falloff
            frequency *= self.frequency_growth
            angle += self.angle_step
        return (total / self.amplitude_total - self.crest_mean) * self.wave_height

    def is_underwater(self, eye):
        return eye[1] < self.surface_height(eye[0], eye[2])

    @staticmethod
    def camera_axes(yaw, pitch, roll):
        forward = (math.sin(yaw) * math.cos(pitch), math.sin(pitch), -math.cos(yaw) * math.cos(pitch))
        flat_right = (math.cos(yaw), 0.0, math.sin(yaw))
        level_up = (flat_right[1] * forward[2] - flat_right[2] * forward[1],
                    flat_right[2] * forward[0] - flat_right[0] * forward[2],
                    flat_right[0] * forward[1] - flat_right[1] * forward[0])
        cosine, sine = math.cos(roll), math.sin(roll)
        right = tuple(r * cosine + u * sine for r, u in zip(flat_right, level_up))
        up = tuple(u * cosine - r * sine for r, u in zip(flat_right, level_up))
        return right, up, forward

    def light_scene(self):
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glEnable(GL_NORMALIZE)
        glEnable(GL_COLOR_MATERIAL)
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
        glLightModelfv(GL_LIGHT_MODEL_AMBIENT, self.scene_ambient)
        glLightfv(GL_LIGHT0, GL_POSITION, (*self.sun_direction, 0.0))
        glLightfv(GL_LIGHT0, GL_DIFFUSE, (*self.sun_color, 1.0))
        glLightfv(GL_LIGHT0, GL_AMBIENT, (0.0, 0.0, 0.0, 1.0))
        glLightfv(GL_LIGHT0, GL_SPECULAR, (0.0, 0.0, 0.0, 1.0))

    def draw_scene_into_target(self, eye, axes, draw_scene):
        right, up, forward = axes
        self.scene_target.begin()
        glViewport(0, 0, self.window_size[0], self.window_size[1])
        glClearColor(0.0, 0.0, 0.0, 0.0)
        glClearDepth(1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        if draw_scene is not None:
            glPushAttrib(GL_ALL_ATTRIB_BITS)
            glMatrixMode(GL_PROJECTION)
            glPushMatrix()
            glLoadIdentity()
            gluPerspective(self.field_of_view_degrees, self.window_size[0] / self.window_size[1],
                           self.scene_near, self.scene_far)
            glMatrixMode(GL_MODELVIEW)
            glPushMatrix()
            glLoadIdentity()
            gluLookAt(*eye, *(e + f for e, f in zip(eye, forward)), *up)
            self.light_scene()
            glEnable(GL_DEPTH_TEST)
            glDepthFunc(GL_LESS)
            draw_scene()
            glMatrixMode(GL_PROJECTION)
            glPopMatrix()
            glMatrixMode(GL_MODELVIEW)
            glPopMatrix()
            glPopAttrib()
        self.scene_target.end()

    def set_uniforms(self, eye, axes):
        right, up, forward = axes
        location = self.program.location
        glUniform1i(location("scene_color"), 0)
        glUniform1i(location("scene_depth"), 1)
        glUniform1f(location("scene_near"), self.scene_near)
        glUniform1f(location("scene_far"), self.scene_far)
        glUniform2f(location("resolution"), float(self.window_size[0]), float(self.window_size[1]))
        glUniform3f(location("eye"), *eye)
        glUniform1f(location("eye_underwater"), 1.0 if self.is_underwater(eye) else 0.0)
        glUniform3f(location("right_axis"), *right)
        glUniform3f(location("up_axis"), *up)
        glUniform3f(location("forward_axis"), *forward)
        glUniform1f(location("lens_zoom"), 1.0 / math.tan(math.radians(self.field_of_view_degrees) * 0.5))
        glUniform1f(location("time"), self.time)
        glUniform1f(location("wave_height"), self.wave_height)
        glUniform1f(location("first_frequency"), self.first_frequency)
        glUniform1f(location("frequency_growth"), self.frequency_growth)
        glUniform1f(location("amplitude_falloff"), self.amplitude_falloff)
        glUniform1f(location("first_angle"), self.first_angle)
        glUniform1f(location("angle_step"), self.angle_step)
        glUniform1f(location("choppiness"), self.choppiness)
        glUniform1f(location("gravity"), self.gravity)
        glUniform1f(location("amplitude_total"), self.amplitude_total)
        glUniform1f(location("crest_mean"), self.crest_mean)
        glUniform1f(location("surface_top"), self.surface_top)
        glUniform1f(location("surface_bottom"), self.surface_bottom)
        glUniform3f(location("sun_direction"), *self.sun_direction)
        glUniform3f(location("sun_color"), *self.sun_color)
        glUniform3f(location("zenith_color"), *self.zenith_color)
        glUniform3f(location("horizon_color"), *self.horizon_color)
        glUniform3f(location("crest_water_color"), *self.crest_water_color)
        glUniform1f(location("far_distance"), self.far_distance)
        glUniform1f(location("fog_density"), self.fog_density)
        glUniform1f(location("exposure"), self.exposure)
        glUniform1f(location("detail_fade"), self.detail_fade)
        glUniform1f(location("seabed_level"), self.seabed_level)
        glUniform3f(location("seabed_color"), *self.seabed_color)
        glUniform1f(location("underwater_density"), self.underwater_density)
        glUniform3f(location("light_absorption"), *self.light_absorption)
        glUniform3f(location("underwater_color"), *self.underwater_color)
        glUniform3f(location("abyss_color"), *self.abyss_color)
        glUniform1f(location("refraction_shift"), self.refraction_shift)

    def bind_scene_textures(self):
        glActiveTexture(GL_TEXTURE1)
        glBindTexture(GL_TEXTURE_2D, self.scene_target.depth_texture)
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, self.scene_target.color_texture)

    @staticmethod
    def unbind_scene_textures():
        glActiveTexture(GL_TEXTURE1)
        glBindTexture(GL_TEXTURE_2D, 0)
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, 0)

    def render(self, eye, yaw, pitch, roll=0.0, draw_scene=None):
        axes = self.camera_axes(yaw, pitch, roll)
        self.draw_scene_into_target(eye, axes, draw_scene)
        glViewport(0, 0, self.window_size[0], self.window_size[1])
        glDisable(GL_DEPTH_TEST)
        glDisable(GL_LIGHTING)
        glDisable(GL_TEXTURE_2D)
        self.program.use()
        self.set_uniforms(eye, axes)
        self.bind_scene_textures()
        glBegin(GL_QUADS)
        glVertex2f(-1.0, -1.0)
        glVertex2f(1.0, -1.0)
        glVertex2f(1.0, 1.0)
        glVertex2f(-1.0, 1.0)
        glEnd()
        self.unbind_scene_textures()
        self.program.release()
