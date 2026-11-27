SKY_RADIUS = 450.0
GUIDING_STAR_DIRECTION = Vector((-0.42, 1.0, 0.62)).normalized()


def build_dome(collection):
    image = gradient_image("night_sky_gradient", [
        (0.0, (0.05, 0.07, 0.16)),
        (0.47, (0.09, 0.13, 0.28)),
        (0.53, (0.07, 0.1, 0.25)),
        (0.7, (0.03, 0.05, 0.16)),
        (1.0, (0.008, 0.012, 0.05)),
    ])
    material = emissive_image_material("night_sky", image)
    builder = bmesh.new()
    bmesh.ops.create_uvsphere(builder, u_segments=48, v_segments=24, radius=SKY_RADIUS)
    bmesh.ops.reverse_faces(builder, faces=builder.faces)
    uv_layer = builder.loops.layers.uv.verify()
    for face in builder.faces:
        for loop in face.loops:
            height = loop.vert.co.z / SKY_RADIUS
            loop[uv_layer].uv = (0.5, min(max(height * 0.5 + 0.5, 0.0), 1.0))
    mesh_object("sky_dome", builder, collection, material)


def build_stars(collection, generator):
    builder = bmesh.new()
    placed = 0
    while placed < 1400:
        direction = Vector((generator.gauss(0, 1), generator.gauss(0, 1), abs(generator.gauss(0, 1))))
        direction.normalize()
        if direction.z < 0.06:
            continue
        brightness = generator.random() ** 3
        size = 0.35 + brightness * 1.6
        center = direction * (SKY_RADIUS - 5.0)
        bmesh.ops.create_icosphere(builder, subdivisions=1, radius=size, matrix=Matrix.Translation(center))
        placed += 1
    star = flat_material("star", (0.0, 0.0, 0.0), 1.0, emission=(0.85, 0.9, 1.0), emission_strength=6.0)
    mesh_object("sky_stars", builder, collection, star)


def build_guiding_star(collection):
    center = GUIDING_STAR_DIRECTION * (SKY_RADIUS - 8.0)
    facing = (-GUIDING_STAR_DIRECTION).to_track_quat("Z", "Y").to_matrix().to_4x4()
    core = bmesh.new()
    bmesh.ops.create_icosphere(core, subdivisions=2, radius=3.2, matrix=Matrix.Translation(center))
    star = flat_material("guiding_star", (0.0, 0.0, 0.0), 1.0, emission=(1.0, 0.97, 0.9), emission_strength=30.0)
    mesh_object("guiding_star", core, collection, star)
    rays = bmesh.new()
    for angle, length in ((0.0, 26.0), (math.pi / 2, 18.0), (math.pi / 4, 7.0), (-math.pi / 4, 7.0)):
        transform = Matrix.Translation(center) @ facing @ Matrix.Rotation(angle, 4, "Z")
        tip = transform @ Vector((0.0, length, 0.0))
        bottom = transform @ Vector((0.0, -length, 0.0))
        left = transform @ Vector((-1.1, 0.0, 0.0))
        right = transform @ Vector((1.1, 0.0, 0.0))
        corners = [rays.verts.new(point) for point in (bottom, right, tip, left)]
        rays.faces.new(corners)
    ray = flat_material("guiding_star_rays", (0.0, 0.0, 0.0), 1.0, emission=(0.8, 0.88, 1.0), emission_strength=8.0)
    rays_object = mesh_object("guiding_star_rays", rays, collection, ray)
    rays_object.data.materials[0].use_backface_culling = False


def build_moonlight(collection):
    light_data = bpy.data.lights.new("moonlight", "SUN")
    light_data.color = (0.55, 0.65, 1.0)
    light_data.energy = 1.6
    light = bpy.data.objects.new("moonlight", light_data)
    light.rotation_euler = (math.radians(55), 0.0, math.radians(200))
    collection.objects.link(light)


def build_night_world():
    world = bpy.context.scene.world or bpy.data.worlds.new("World")
    bpy.context.scene.world = world
    world.use_nodes = True
    background = world.node_tree.nodes.get("Background")
    background.inputs["Color"].default_value = (0.01, 0.014, 0.035, 1.0)
    background.inputs["Strength"].default_value = 1.0


def build_sky():
    collection = fresh_collection("Sky")
    generator = rng(25)
    build_dome(collection)
    build_stars(collection, generator)
    build_guiding_star(collection)
    build_moonlight(collection)
    build_night_world()
    return len(collection.objects)


print("sky objects:", build_sky())
