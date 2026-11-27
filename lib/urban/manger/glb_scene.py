import ctypes
import io
import json
import math
import struct

import numpy
import pygame
from OpenGL.GL import *

COMPONENT_TYPES = {5120: numpy.int8, 5121: numpy.uint8, 5122: numpy.int16, 5123: numpy.uint16, 5125: numpy.uint32,
                   5126: numpy.float32}
COMPONENT_COUNTS = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}
LUMENS_PER_WATT = 683.0

SCENE_VERTEX_SHADER = """
#version 120
uniform mat4 view_projection;
uniform mat4 light_matrix;
attribute vec3 position;
attribute vec3 normal;
attribute vec2 uv;
varying vec3 world_position;
varying vec3 world_normal;
varying vec2 texture_uv;
varying vec4 light_space;
void main() {
    world_position = position;
    world_normal = normal;
    texture_uv = uv;
    light_space = light_matrix * vec4(position, 1.0);
    gl_Position = view_projection * vec4(position, 1.0);
}
"""

SCENE_FRAGMENT_SHADER = """
#version 120
const int MAX_POINT_LIGHTS = 8;
uniform vec4 base_color;
uniform sampler2D base_texture;
uniform bool has_base_texture;
uniform vec3 emissive;
uniform sampler2D emissive_texture;
uniform bool has_emissive_texture;
uniform vec3 ambient;
uniform vec3 sun_direction;
uniform vec3 sun_irradiance;
uniform int point_count;
uniform vec3 point_positions[MAX_POINT_LIGHTS];
uniform vec3 point_intensities[MAX_POINT_LIGHTS];
uniform sampler2D shadow_map;
uniform float shadow_texel;
uniform float exposure;
varying vec3 world_position;
varying vec3 world_normal;
varying vec2 texture_uv;
varying vec4 light_space;

vec3 to_linear(vec3 color) {
    return pow(color, vec3(2.2));
}

float sun_visibility(float facing) {
    vec3 projected = light_space.xyz / light_space.w * 0.5 + 0.5;
    if (projected.x < 0.0 || projected.x > 1.0 || projected.y < 0.0 || projected.y > 1.0 || projected.z > 1.0) {
        return 1.0;
    }
    float bias = mix(0.0015, 0.0004, facing);
    float lit = 0.0;
    for (int x = -1; x <= 1; x++) {
        for (int y = -1; y <= 1; y++) {
            float stored = texture2D(shadow_map, projected.xy + vec2(x, y) * shadow_texel).r;
            lit += projected.z - bias <= stored ? 1.0 : 0.0;
        }
    }
    return lit / 9.0;
}

vec3 tone_map(vec3 color) {
    color *= exposure;
    vec3 mapped = (color * (2.51 * color + 0.03)) / (color * (2.43 * color + 0.59) + 0.14);
    return pow(clamp(mapped, 0.0, 1.0), vec3(1.0 / 2.2));
}

void main() {
    vec3 albedo = base_color.rgb;
    if (has_base_texture) {
        albedo *= to_linear(texture2D(base_texture, texture_uv).rgb);
    }
    vec3 surface_normal = normalize(world_normal);
    if (!gl_FrontFacing) {
        surface_normal = -surface_normal;
    }
    float sun_facing = max(dot(surface_normal, sun_direction), 0.0);
    vec3 irradiance = sun_irradiance * sun_facing * sun_visibility(sun_facing);
    for (int index = 0; index < MAX_POINT_LIGHTS; index++) {
        if (index >= point_count) {
            break;
        }
        vec3 to_light = point_positions[index] - world_position;
        float distance_squared = max(dot(to_light, to_light), 0.04);
        float facing = max(dot(surface_normal, to_light * inversesqrt(distance_squared)), 0.0);
        irradiance += point_intensities[index] * facing / distance_squared;
    }
    vec3 emission = emissive;
    if (has_emissive_texture) {
        emission *= to_linear(texture2D(emissive_texture, texture_uv).rgb);
    }
    vec3 color = albedo * (ambient + irradiance / 3.14159265) + emission;
    gl_FragColor = vec4(tone_map(color), 1.0);
}
"""

SHADOW_VERTEX_SHADER = """
#version 120
uniform mat4 light_matrix;
attribute vec3 position;
void main() {
    gl_Position = light_matrix * vec4(position, 1.0);
}
"""

SHADOW_FRAGMENT_SHADER = """
#version 120
void main() {
    gl_FragColor = vec4(1.0);
}
"""


def quaternion_matrix(quaternion):
    x, y, z, w = quaternion
    return numpy.array([
        [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w), 0],
        [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w), 0],
        [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y), 0],
        [0, 0, 0, 1]], dtype=numpy.float64)


def node_matrix(node):
    if "matrix" in node:
        return numpy.array(node["matrix"], dtype=numpy.float64).reshape(4, 4).T
    translation = numpy.identity(4)
    translation[:3, 3] = node.get("translation", (0.0, 0.0, 0.0))
    rotation = quaternion_matrix(node.get("rotation", (0.0, 0.0, 0.0, 1.0)))
    scale = numpy.diag((*node.get("scale", (1.0, 1.0, 1.0)), 1.0))
    return translation @ rotation @ scale


def perspective(vertical_fov, aspect, near, far):
    focal = 1.0 / math.tan(vertical_fov / 2.0)
    return numpy.array([
        [focal / aspect, 0, 0, 0],
        [0, focal, 0, 0],
        [0, 0, (far + near) / (near - far), 2 * far * near / (near - far)],
        [0, 0, -1, 0]], dtype=numpy.float64)


def orthographic(half_size, near, far):
    return numpy.array([
        [1.0 / half_size, 0, 0, 0],
        [0, 1.0 / half_size, 0, 0],
        [0, 0, -2.0 / (far - near), -(far + near) / (far - near)],
        [0, 0, 0, 1]], dtype=numpy.float64)


def look_at(eye, target, up):
    eye, target, up = (numpy.asarray(vector, dtype=numpy.float64) for vector in (eye, target, up))
    forward = target - eye
    forward /= numpy.linalg.norm(forward)
    side = numpy.cross(forward, up)
    side /= numpy.linalg.norm(side)
    true_up = numpy.cross(side, forward)
    view = numpy.identity(4)
    view[0, :3], view[1, :3], view[2, :3] = side, true_up, -forward
    view[:3, 3] = -view[:3, :3] @ eye
    return view


class GlbDocument:

    def __init__(self, path):
        with open(path, "rb") as glb_file:
            data = glb_file.read()
        magic, _, _ = struct.unpack_from("<4sII", data, 0)
        if magic != b"glTF":
            raise ValueError(f"{path} is not a GLB file")
        json_length, _ = struct.unpack_from("<II", data, 12)
        self.json = json.loads(data[20:20 + json_length])
        binary_start = 20 + json_length
        binary_length, _ = struct.unpack_from("<II", data, binary_start)
        self.binary = data[binary_start + 8:binary_start + 8 + binary_length]

    def buffer_view_bytes(self, index):
        view = self.json["bufferViews"][index]
        start = view.get("byteOffset", 0)
        return self.binary[start:start + view["byteLength"]], view.get("byteStride")

    def accessor(self, index):
        accessor = self.json["accessors"][index]
        component_type = COMPONENT_TYPES[accessor["componentType"]]
        components = COMPONENT_COUNTS[accessor["type"]]
        raw, stride = self.buffer_view_bytes(accessor["bufferView"])
        offset = accessor.get("byteOffset", 0)
        element_size = numpy.dtype(component_type).itemsize * components
        count = accessor["count"]
        if stride and stride != element_size:
            rows = numpy.frombuffer(raw, dtype=numpy.uint8, count=stride * (count - 1) + element_size, offset=offset)
            padded = numpy.zeros(stride * count, dtype=numpy.uint8)
            padded[:rows.size] = rows
            values = padded.reshape(count, stride)[:, :element_size].copy().view(component_type)
        else:
            values = numpy.frombuffer(raw, dtype=component_type, count=count * components, offset=offset)
        return values.reshape(count, components) if components > 1 else values.copy()

    def image_bytes(self, index):
        image = self.json["images"][index]
        return self.buffer_view_bytes(image["bufferView"])[0], image.get("mimeType", "image/png")

    def world_nodes(self):
        scene = self.json["scenes"][self.json.get("scene", 0)]
        pending = [(index, numpy.identity(4)) for index in scene["nodes"]]
        while pending:
            index, parent = pending.pop()
            node = self.json["nodes"][index]
            world = parent @ node_matrix(node)
            yield node, world
            pending.extend((child, world) for child in node.get("children", ()))


class MaterialBatch:

    def __init__(self, material, positions, normals, uvs, indices):
        self.material = material
        self.index_count = len(indices)
        self.buffers = glGenBuffers(4)
        for buffer, values in zip(self.buffers[:3], (positions, normals, uvs)):
            glBindBuffer(GL_ARRAY_BUFFER, buffer)
            glBufferData(GL_ARRAY_BUFFER, values.astype(numpy.float32).nbytes, values.astype(numpy.float32),
                         GL_STATIC_DRAW)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.buffers[3])
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, indices.astype(numpy.uint32).nbytes, indices.astype(numpy.uint32),
                     GL_STATIC_DRAW)
        glBindBuffer(GL_ARRAY_BUFFER, 0)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, 0)

    def bind_attribute(self, location, buffer, size):
        glBindBuffer(GL_ARRAY_BUFFER, buffer)
        glEnableVertexAttribArray(location)
        glVertexAttribPointer(location, size, GL_FLOAT, GL_FALSE, 0, ctypes.c_void_p(0))

    def draw(self, with_surface):
        self.bind_attribute(0, self.buffers[0], 3)
        if with_surface:
            self.bind_attribute(1, self.buffers[1], 3)
            self.bind_attribute(2, self.buffers[2], 2)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.buffers[3])
        glDrawElements(GL_TRIANGLES, self.index_count, GL_UNSIGNED_INT, ctypes.c_void_p(0))
        for location in (0, 1, 2):
            glDisableVertexAttribArray(location)
        glBindBuffer(GL_ARRAY_BUFFER, 0)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, 0)


class SceneMaterial:

    def __init__(self, description, textures):
        metallic_roughness = description.get("pbrMetallicRoughness", {})
        self.name = description.get("name", "material")
        self.base_color = tuple(metallic_roughness.get("baseColorFactor", (1.0, 1.0, 1.0, 1.0)))
        base_texture = metallic_roughness.get("baseColorTexture")
        self.base_texture = textures[base_texture["index"]] if base_texture else None
        strength = description.get("extensions", {}).get("KHR_materials_emissive_strength", {}).get(
            "emissiveStrength", 1.0)
        self.emissive = tuple(channel * strength for channel in description.get("emissiveFactor", (0.0, 0.0, 0.0)))
        emissive_texture = description.get("emissiveTexture")
        self.emissive_texture = textures[emissive_texture["index"]] if emissive_texture else None
        self.casts_shadow = max(self.emissive) == 0.0


class GlbScene:

    def __init__(self, path):
        self.document = GlbDocument(path)
        self.textures = self.load_textures()
        self.materials = [SceneMaterial(description, self.textures)
                          for description in self.document.json.get("materials", [])]
        self.default_material = SceneMaterial({"name": "default"}, self.textures)
        self.point_lights = []
        self.sun = None
        self.camera = None
        self.batches = self.build_batches()

    def load_textures(self):
        document = self.document.json
        samplers = document.get("samplers", [])
        images = {}
        textures = []
        for texture in document.get("textures", []):
            source = texture["source"]
            if source not in images:
                images[source] = self.load_image(source)
            sampler = samplers[texture["sampler"]] if "sampler" in texture else {}
            handle = glGenTextures(1)
            pixels, width, height = images[source]
            glBindTexture(GL_TEXTURE_2D, handle)
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, pixels)
            glGenerateMipmap(GL_TEXTURE_2D)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, sampler.get("minFilter", GL_LINEAR_MIPMAP_LINEAR))
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, sampler.get("magFilter", GL_LINEAR))
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, sampler.get("wrapS", GL_REPEAT))
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, sampler.get("wrapT", GL_REPEAT))
            textures.append(handle)
        glBindTexture(GL_TEXTURE_2D, 0)
        return textures

    def load_image(self, index):
        data, mime_type = self.document.image_bytes(index)
        extension = "jpg" if "jpeg" in mime_type else "png"
        surface = pygame.image.load(io.BytesIO(data), f"image.{extension}")
        return pygame.image.tobytes(surface, "RGBA", False), surface.get_width(), surface.get_height()

    def build_batches(self):
        grouped = {}
        lights = self.document.json.get("extensions", {}).get("KHR_lights_punctual", {}).get("lights", [])
        for node, world in self.document.world_nodes():
            light_reference = node.get("extensions", {}).get("KHR_lights_punctual")
            if light_reference:
                self.add_light(lights[light_reference["light"]], world)
            if "camera" in node and self.camera is None:
                self.camera = (self.document.json["cameras"][node["camera"]], world)
            if "mesh" in node:
                self.collect_mesh(self.document.json["meshes"][node["mesh"]], world, grouped)
        batches = []
        for material_index, parts in grouped.items():
            material = self.materials[material_index] if material_index is not None else self.default_material
            offset = 0
            indices = []
            for positions, _, _, part_indices in parts:
                indices.append(part_indices + offset)
                offset += len(positions)
            batches.append(MaterialBatch(material, numpy.concatenate([part[0] for part in parts]),
                                         numpy.concatenate([part[1] for part in parts]),
                                         numpy.concatenate([part[2] for part in parts]), numpy.concatenate(indices)))
        return batches

    def collect_mesh(self, mesh, world, grouped):
        normal_matrix = numpy.linalg.inv(world[:3, :3]).T
        for primitive in mesh["primitives"]:
            if primitive.get("mode", 4) != 4:
                continue
            attributes = primitive["attributes"]
            positions = self.document.accessor(attributes["POSITION"]).astype(numpy.float64)
            count = len(positions)
            positions = positions @ world[:3, :3].T + world[:3, 3]
            if "NORMAL" in attributes:
                normals = self.document.accessor(attributes["NORMAL"]).astype(numpy.float64) @ normal_matrix.T
                lengths = numpy.linalg.norm(normals, axis=1, keepdims=True)
                normals /= numpy.maximum(lengths, 1e-9)
            else:
                normals = numpy.tile((0.0, 1.0, 0.0), (count, 1))
            if "TEXCOORD_0" in attributes:
                uvs = self.document.accessor(attributes["TEXCOORD_0"]).astype(numpy.float64)
            else:
                uvs = numpy.zeros((count, 2))
            if "indices" in primitive:
                indices = self.document.accessor(primitive["indices"]).astype(numpy.uint32)
            else:
                indices = numpy.arange(count, dtype=numpy.uint32)
            grouped.setdefault(primitive.get("material"), []).append((positions, normals, uvs, indices))

    def add_light(self, light, world):
        color = numpy.asarray(light.get("color", (1.0, 1.0, 1.0)))
        power = light.get("intensity", 1.0) / LUMENS_PER_WATT
        if light["type"] == "directional":
            toward_light = world[:3, :3] @ numpy.array((0.0, 0.0, 1.0))
            self.sun = (toward_light / numpy.linalg.norm(toward_light), color * power)
        elif light["type"] == "point":
            self.point_lights.append((world[:3, 3].copy(), color * power))

    def draw(self, program, with_surface=True):
        for batch in self.batches:
            if not with_surface and not batch.material.casts_shadow:
                continue
            if with_surface:
                program.apply_material(batch.material)
            batch.draw(with_surface)


class ShaderProgram:

    def __init__(self, vertex_source, fragment_source, attributes):
        self.handle = glCreateProgram()
        shaders = [self.compile(GL_VERTEX_SHADER, vertex_source), self.compile(GL_FRAGMENT_SHADER, fragment_source)]
        for shader in shaders:
            glAttachShader(self.handle, shader)
        for location, name in enumerate(attributes):
            glBindAttribLocation(self.handle, location, name)
        glLinkProgram(self.handle)
        if not glGetProgramiv(self.handle, GL_LINK_STATUS):
            raise RuntimeError("Shader link failed:\n" + glGetProgramInfoLog(self.handle).decode(errors="replace"))
        for shader in shaders:
            glDeleteShader(shader)
        self.locations = {}

    @staticmethod
    def compile(kind, source):
        shader = glCreateShader(kind)
        glShaderSource(shader, source)
        glCompileShader(shader)
        if not glGetShaderiv(shader, GL_COMPILE_STATUS):
            raise RuntimeError("Shader compile failed:\n" + glGetShaderInfoLog(shader).decode(errors="replace"))
        return shader

    def location(self, name):
        if name not in self.locations:
            self.locations[name] = glGetUniformLocation(self.handle, name)
        return self.locations[name]

    def use(self):
        glUseProgram(self.handle)

    def set_matrix(self, name, matrix):
        glUniformMatrix4fv(self.location(name), 1, GL_TRUE, numpy.asarray(matrix, dtype=numpy.float32))

    def set_vector(self, name, vector):
        glUniform3f(self.location(name), *(float(value) for value in vector))

    def set_vectors(self, name, vectors):
        if len(vectors):
            glUniform3fv(self.location(name), len(vectors), numpy.asarray(vectors, dtype=numpy.float32))

    def set_float(self, name, value):
        glUniform1f(self.location(name), float(value))

    def set_int(self, name, value):
        glUniform1i(self.location(name), int(value))

    def apply_material(self, material):
        glUniform4f(self.location("base_color"), *material.base_color)
        self.set_vector("emissive", material.emissive)
        self.bind_texture("base_texture", "has_base_texture", material.base_texture, 0)
        self.bind_texture("emissive_texture", "has_emissive_texture", material.emissive_texture, 1)

    def bind_texture(self, sampler_name, flag_name, texture, unit):
        glActiveTexture(GL_TEXTURE0 + unit)
        glBindTexture(GL_TEXTURE_2D, texture or 0)
        self.set_int(sampler_name, unit)
        self.set_int(flag_name, texture is not None)
        glActiveTexture(GL_TEXTURE0)


class SunShadow:

    def __init__(self, size, half_size, center, distance):
        self.size = size
        self.half_size = half_size
        self.center = numpy.asarray(center, dtype=numpy.float64)
        self.distance = distance
        self.texture = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.texture)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_DEPTH_COMPONENT24, size, size, 0, GL_DEPTH_COMPONENT, GL_FLOAT, None)
        for parameter, value in ((GL_TEXTURE_MIN_FILTER, GL_NEAREST), (GL_TEXTURE_MAG_FILTER, GL_NEAREST),
                                 (GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE), (GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)):
            glTexParameteri(GL_TEXTURE_2D, parameter, value)
        glBindTexture(GL_TEXTURE_2D, 0)
        self.framebuffer = glGenFramebuffers(1)
        glBindFramebuffer(GL_FRAMEBUFFER, self.framebuffer)
        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, GL_TEXTURE_2D, self.texture, 0)
        glDrawBuffer(GL_NONE)
        glReadBuffer(GL_NONE)
        glBindFramebuffer(GL_FRAMEBUFFER, 0)

    def light_matrix(self, toward_light):
        eye = self.center + numpy.asarray(toward_light) * self.distance
        up = (0.0, 0.0, 1.0) if abs(toward_light[1]) > 0.95 else (0.0, 1.0, 0.0)
        return orthographic(self.half_size, 1.0, self.distance * 2.0) @ look_at(eye, self.center, up)
