import math
import random

import bmesh
import bpy
from mathutils import Matrix, Vector


def fresh_collection(name):
    existing = bpy.data.collections.get(name)
    if existing:
        for obj in list(existing.all_objects):
            bpy.data.objects.remove(obj, do_unlink=True)
        bpy.data.collections.remove(existing)
    collection = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(collection)
    return collection


def flat_material(name, color, roughness=0.8, emission=None, emission_strength=1.0):
    material = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    material.use_nodes = True
    shader = material.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = (*color, 1.0)
    shader.inputs["Roughness"].default_value = roughness
    if emission:
        shader.inputs["Emission Color"].default_value = (*emission, 1.0)
        shader.inputs["Emission Strength"].default_value = emission_strength
    return material


def tinted_texture_material(source_name, name, tint):
    existing = bpy.data.materials.get(name)
    if existing:
        return existing
    material = bpy.data.materials[source_name].copy()
    material.name = name
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    shader = nodes["Principled BSDF"]
    diffuse = nodes["Image Texture"]
    multiply = nodes.new("ShaderNodeMix")
    multiply.data_type = "RGBA"
    multiply.blend_type = "MULTIPLY"
    multiply.inputs["Factor"].default_value = 1.0
    multiply.inputs["B"].default_value = (*tint, 1.0)
    links.new(diffuse.outputs["Color"], multiply.inputs["A"])
    links.new(multiply.outputs["Result"], shader.inputs["Base Color"])
    return material


def world_box_uv(obj, texture_size, vertical_grain=False):
    mesh = obj.data
    builder = bmesh.new()
    builder.from_mesh(mesh)
    uv_layer = builder.loops.layers.uv.verify()
    to_world = obj.matrix_world
    rotation = to_world.to_3x3()
    for face in builder.faces:
        normal = (rotation @ face.normal).normalized()
        axis = max(range(3), key=lambda index: abs(normal[index]))
        for loop in face.loops:
            point = to_world @ loop.vert.co
            if axis == 0:
                u, v = point.y, point.z
            elif axis == 1:
                u, v = point.x, point.z
            else:
                u, v = point.x, point.y
            if vertical_grain and axis != 2:
                u, v = v, u
            loop[uv_layer].uv = (u / texture_size, v / texture_size)
    builder.to_mesh(mesh)
    builder.free()


def mesh_object(name, builder, collection, material=None, texture_size=None, location=(0, 0, 0),
                vertical_grain=False):
    mesh = bpy.data.meshes.new(name)
    builder.to_mesh(mesh)
    builder.free()
    obj = bpy.data.objects.new(name, mesh)
    obj.location = location
    collection.objects.link(obj)
    if material:
        mesh.materials.append(material)
    if texture_size:
        bpy.context.view_layer.update()
        world_box_uv(obj, texture_size, vertical_grain)
    return obj


def add_box(builder, size, center, rotation=(0.0, 0.0, 0.0)):
    transform = Matrix.Translation(center) @ rotation_matrix(rotation) @ Matrix.Diagonal((*size, 1.0))
    bmesh.ops.create_cube(builder, size=1.0, matrix=transform)


def rotation_matrix(rotation):
    return (Matrix.Rotation(rotation[2], 4, "Z") @ Matrix.Rotation(rotation[1], 4, "Y")
            @ Matrix.Rotation(rotation[0], 4, "X"))


def add_cylinder(builder, radius, depth, center, rotation=(0.0, 0.0, 0.0), segments=8, tip_radius=None):
    transform = Matrix.Translation(center) @ rotation_matrix(rotation)
    bmesh.ops.create_cone(builder, cap_ends=True, segments=segments, radius1=radius,
                          radius2=radius if tip_radius is None else tip_radius, depth=depth, matrix=transform)


def box_object(name, size, center, collection, material, texture_size=None, rotation=(0.0, 0.0, 0.0)):
    builder = bmesh.new()
    add_box(builder, size, center, rotation)
    return mesh_object(name, builder, collection, material, texture_size)


def add_straw(builder, generator, center, radius, count, length=(0.12, 0.3), height=0.0, lift=0.25):
    for _ in range(count):
        angle = generator.uniform(0, math.tau)
        distance = radius * math.sqrt(generator.random())
        base = Vector((center[0] + math.cos(angle) * distance, center[1] + math.sin(angle) * distance,
                       center[2] + height * (1.0 - distance / max(radius, 1e-6))))
        stalk_length = generator.uniform(*length)
        heading = generator.uniform(0, math.tau)
        tilt = generator.uniform(-lift, lift)
        direction = Vector((math.cos(heading), math.sin(heading), tilt)).normalized()
        side = direction.cross(Vector((0, 0, 1)))
        if side.length < 1e-4:
            side = Vector((1, 0, 0))
        side = side.normalized() * 0.004
        tip = base + direction * stalk_length
        corners = [builder.verts.new(point) for point in (base - side, base + side, tip + side * 0.4, tip - side * 0.4)]
        builder.faces.new(corners)


def soft_mound(builder, center, radius_x, radius_y, height, rows, generator, roughness=0.15):
    grid = []
    for row in range(rows + 1):
        line = []
        for column in range(rows + 1):
            u = column / rows * 2 - 1
            v = row / rows * 2 - 1
            falloff = max(0.0, 1.0 - (u * u + v * v))
            bump = 1.0 + generator.uniform(-roughness, roughness)
            line.append(builder.verts.new((center[0] + u * radius_x, center[1] + v * radius_y,
                                           center[2] + height * math.sqrt(falloff) * bump)))
        grid.append(line)
    for row in range(rows):
        for column in range(rows):
            builder.faces.new((grid[row][column], grid[row][column + 1], grid[row + 1][column + 1], grid[row + 1][column]))


def gradient_image(name, stops, height=256):
    image = bpy.data.images.get(name) or bpy.data.images.new(name, width=4, height=height)
    pixels = []
    for row in range(height):
        position = row / (height - 1)
        for index in range(len(stops) - 1):
            start, end = stops[index], stops[index + 1]
            if start[0] <= position <= end[0]:
                blend = (position - start[0]) / max(end[0] - start[0], 1e-6)
                color = [start[1][channel] + (end[1][channel] - start[1][channel]) * blend for channel in range(3)]
                break
        else:
            color = list(stops[-1][1])
        pixels.extend((color + [1.0]) * 4)
    image.pixels = pixels
    image.pack()
    return image


def emissive_image_material(name, image):
    material = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    shader = nodes["Principled BSDF"]
    shader.inputs["Base Color"].default_value = (0, 0, 0, 1)
    shader.inputs["Emission Strength"].default_value = 1.0
    texture = nodes.get("Gradient") or nodes.new("ShaderNodeTexImage")
    texture.name = "Gradient"
    texture.image = image
    texture.extension = "EXTEND"
    links.new(texture.outputs["Color"], shader.inputs["Emission Color"])
    return material


def add_tube(builder, points, radii, segments=10, closed=False, cap=True):
    points = [Vector(point) for point in points]
    rings = []
    count = len(points)
    for index, point in enumerate(points):
        if closed:
            tangent = points[(index + 1) % count] - points[index - 1]
        else:
            tangent = points[min(index + 1, count - 1)] - points[max(index - 1, 0)]
        tangent.normalize()
        reference = Vector((0, 0, 1)) if abs(tangent.z) < 0.9 else Vector((0, 1, 0))
        side = tangent.cross(reference).normalized()
        up = side.cross(tangent).normalized()
        radius = radii[index]
        radius_x, radius_y = (radius, radius) if isinstance(radius, (int, float)) else radius
        ring = []
        for step in range(segments):
            angle = step / segments * math.tau
            ring.append(builder.verts.new(point + side * math.cos(angle) * radius_x + up * math.sin(angle) * radius_y))
        rings.append(ring)
    pairs = range(count if closed else count - 1)
    for index in pairs:
        current, following = rings[index], rings[(index + 1) % count]
        for step in range(segments):
            builder.faces.new((current[step], current[(step + 1) % segments], following[(step + 1) % segments],
                               following[step]))
    if cap and not closed:
        builder.faces.new(list(reversed(rings[0])))
        builder.faces.new(rings[-1])


def add_ellipsoid(builder, center, size, subdivisions=2):
    bmesh.ops.create_icosphere(builder, subdivisions=subdivisions, radius=1.0,
                               matrix=Matrix.Translation(center) @ Matrix.Diagonal((*size, 1.0)))


class Figure:

    def __init__(self, name):
        self.name = name
        self.builder = bmesh.new()
        self.materials = []

    def add(self, material, shape, *arguments, **options):
        before = len(self.builder.faces)
        shape(self.builder, *arguments, **options)
        if material not in self.materials:
            self.materials.append(material)
        slot = self.materials.index(material)
        self.builder.faces.ensure_lookup_table()
        for index in range(before, len(self.builder.faces)):
            self.builder.faces[index].material_index = slot

    def finish(self, collection, location, facing_point=None, yaw=0.0, smooth_levels=1):
        if facing_point is not None:
            yaw = math.atan2(facing_point[0] - location[0], -(facing_point[1] - location[1]))
        mesh = bpy.data.meshes.new(self.name)
        self.builder.to_mesh(mesh)
        self.builder.free()
        for material in self.materials:
            mesh.materials.append(material)
        for polygon in mesh.polygons:
            polygon.use_smooth = True
        obj = bpy.data.objects.new(self.name, mesh)
        obj.location = location
        obj.rotation_euler = (0.0, 0.0, yaw)
        collection.objects.link(obj)
        if smooth_levels:
            modifier = obj.modifiers.new("smooth", "SUBSURF")
            modifier.levels = smooth_levels
            modifier.render_levels = smooth_levels
        return obj


TOWN_CENTER = Vector((-10.0, 42.0, 0.0))


def ground_height(x, y):
    distance = max(0.0, y - 8.0)
    rolling = math.sin(x * 0.045) * math.cos(y * 0.037) * 1.6 + math.sin(x * 0.11 + y * 0.07) * 0.6
    town_hill = 3.2 * math.exp(-((x - TOWN_CENTER.x) ** 2 + (y - TOWN_CENTER.y) ** 2) / 260.0)
    return rolling * min(distance / 30.0, 1.0) + town_hill


def rng(seed):
    return random.Random(seed)
