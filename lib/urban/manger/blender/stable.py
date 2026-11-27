STABLE_LEFT = -4.5
STABLE_RIGHT = 4.5
STABLE_FRONT = -2.5
STABLE_BACK = 5.0
WALL_HEIGHT = 3.4
RIDGE_HEIGHT = 4.6
DOOR_LEFT = -4.3
DOOR_RIGHT = -0.2
DOOR_TOP = 3.05


def clear_default_objects():
    for name in ("Cube", "Light", "Camera"):
        obj = bpy.data.objects.get(name)
        if obj:
            bpy.data.objects.remove(obj, do_unlink=True)


def plank_wall_along_x(builder, generator, x_from, x_to, y, z_from, z_to, plank_width=0.24, thickness=0.06):
    x = x_from
    while x < x_to - 0.02:
        width = min(plank_width * generator.uniform(0.8, 1.2), x_to - x)
        gap = generator.uniform(0.0, 0.025)
        top = z_to - generator.uniform(0.0, 0.08)
        add_box(builder, (width - gap, thickness, top - z_from), (x + width / 2, y + generator.uniform(-0.015, 0.015),
                (z_from + top) / 2), (0.0, generator.uniform(-0.01, 0.01), generator.uniform(-0.015, 0.015)))
        x += width


def plank_wall_along_y(builder, generator, y_from, y_to, x, z_from, z_to, plank_width=0.24, thickness=0.06):
    y = y_from
    while y < y_to - 0.02:
        width = min(plank_width * generator.uniform(0.8, 1.2), y_to - y)
        gap = generator.uniform(0.0, 0.025)
        top = z_to - generator.uniform(0.0, 0.08)
        add_box(builder, (thickness, width - gap, top - z_from), (x + generator.uniform(-0.015, 0.015), y + width / 2,
                (z_from + top) / 2), (generator.uniform(-0.01, 0.01), 0.0, generator.uniform(-0.015, 0.015)))
        y += width


def build_walls(collection, generator):
    planks = tinted_texture_material("old_wood_floor", "stable_planks", (0.62, 0.42, 0.3))
    builder = bmesh.new()
    plank_wall_along_x(builder, generator, DOOR_RIGHT + 0.15, STABLE_RIGHT, STABLE_BACK, 0.0, WALL_HEIGHT)
    plank_wall_along_x(builder, generator, DOOR_LEFT - 0.25, DOOR_RIGHT + 0.15, STABLE_BACK, DOOR_TOP + 0.2,
                       WALL_HEIGHT)
    plank_wall_along_x(builder, generator, STABLE_LEFT, DOOR_LEFT - 0.25, STABLE_BACK, 0.0, WALL_HEIGHT)
    plank_wall_along_y(builder, generator, STABLE_FRONT, STABLE_BACK, STABLE_LEFT, 0.0, WALL_HEIGHT)
    mesh_object("stable_plank_walls", builder, collection, planks, texture_size=1.6, vertical_grain=True)


def build_door_frame(collection):
    beams = tinted_texture_material("old_wood_floor", "stable_beams", (0.55, 0.38, 0.26))
    builder = bmesh.new()
    post = 0.3
    for x in (DOOR_LEFT - post / 2, DOOR_RIGHT + post / 2):
        add_box(builder, (post, post, DOOR_TOP + 0.35), (x, STABLE_BACK - 0.05, (DOOR_TOP + 0.35) / 2))
    add_box(builder, (DOOR_RIGHT - DOOR_LEFT + 2 * post + 0.3, post, 0.3), ((DOOR_LEFT + DOOR_RIGHT) / 2,
            STABLE_BACK - 0.05, DOOR_TOP + 0.15))
    brace = 0.75
    for x, sign in ((DOOR_LEFT, 1), (DOOR_RIGHT, -1)):
        add_box(builder, (brace * 1.414, 0.22, 0.2), (x + sign * brace / 2, STABLE_BACK - 0.1, DOOR_TOP - brace / 2),
                (0.0, sign * math.radians(45), 0.0))
    for x in (STABLE_LEFT, -0.6 + 2.6, STABLE_RIGHT):
        add_box(builder, (0.28, 0.28, WALL_HEIGHT), (x, STABLE_FRONT + 0.1, WALL_HEIGHT / 2))
    add_box(builder, (STABLE_RIGHT - STABLE_LEFT, 0.26, 0.26), (0.0, STABLE_FRONT + 0.1, WALL_HEIGHT))
    add_box(builder, (STABLE_RIGHT - STABLE_LEFT, 0.26, 0.26), (0.0, STABLE_BACK - 0.05, WALL_HEIGHT))
    for y in (STABLE_FRONT + 0.1, STABLE_BACK - 0.05):
        add_box(builder, (0.26, 0.26, WALL_HEIGHT), (STABLE_LEFT, y, WALL_HEIGHT / 2))
    mesh_object("stable_beams", builder, collection, beams, texture_size=1.2)


def build_stone_wall(collection, generator):
    plaster = tinted_texture_material("plastered_wall_02", "stable_plaster", (0.42, 0.28, 0.2))
    stone = tinted_texture_material("rustic_stone_wall_02", "stable_stone", (0.8, 0.62, 0.46))
    arch_from, arch_to, arch_spring = 1.4, 3.2, 1.9
    arch_center_y = (arch_from + arch_to) / 2
    arch_radius = (arch_to - arch_from) / 2
    wall = bmesh.new()
    thickness = 0.45
    x = STABLE_RIGHT + thickness / 2
    add_box(wall, (thickness, arch_from - STABLE_FRONT, WALL_HEIGHT), (x, (STABLE_FRONT + arch_from) / 2, WALL_HEIGHT / 2))
    add_box(wall, (thickness, STABLE_BACK - arch_to, WALL_HEIGHT), (x, (arch_to + STABLE_BACK) / 2, WALL_HEIGHT / 2))
    top_from = arch_spring + arch_radius
    add_box(wall, (thickness, arch_to - arch_from, WALL_HEIGHT - top_from),
            (x, arch_center_y, (top_from + WALL_HEIGHT) / 2))
    steps = 10
    for step in range(steps):
        angle = math.pi * (step + 0.5) / steps
        height = arch_spring + math.sin(angle) * arch_radius
        width = (arch_to - arch_from) / steps
        offset = math.cos(angle) * arch_radius
        filler_height = top_from - height
        if filler_height > 0.01:
            add_box(wall, (thickness, width + 0.01, filler_height),
                    (x, arch_center_y - offset, height + filler_height / 2))
    mesh_object("stable_side_wall", wall, collection, plaster, texture_size=2.0)
    ring = bmesh.new()
    blocks = 13
    for block in range(blocks):
        angle = math.pi * block / (blocks - 1)
        y = arch_center_y - math.cos(angle) * (arch_radius + 0.12)
        z = arch_spring + math.sin(angle) * (arch_radius + 0.12)
        add_box(ring, (thickness + 0.08, 0.26, 0.2 + generator.uniform(0, 0.05)), (x - 0.04, y, z),
                (angle - math.pi / 2, 0.0, 0.0))
    for side in (arch_from - 0.13, arch_to + 0.13):
        z = 0.0
        while z < arch_spring:
            height = generator.uniform(0.26, 0.38)
            add_box(ring, (thickness + 0.08, 0.28 + generator.uniform(0, 0.06), height - 0.02),
                    (x - 0.04, side, z + height / 2))
            z += height
    mesh_object("stable_arch_stones", ring, collection, stone, texture_size=0.9)
    shadow = flat_material("arch_darkness", (0.02, 0.012, 0.008), 1.0)
    box_object("stable_arch_recess", (0.05, arch_to - arch_from, arch_spring + arch_radius),
               (x + thickness / 2 + 0.03, arch_center_y, (arch_spring + arch_radius) / 2), collection, shadow)


def build_roof(collection, generator):
    beams = bpy.data.materials["stable_beams"]
    thatch = tinted_texture_material("thatch_roof_angled", "stable_thatch", (0.55, 0.42, 0.3))
    builder = bmesh.new()
    depth = STABLE_BACK - STABLE_FRONT
    ridge_y = (STABLE_FRONT + STABLE_BACK) / 2
    slope = math.atan2(RIDGE_HEIGHT - WALL_HEIGHT, depth / 2)
    rafter_length = math.hypot(depth / 2, RIDGE_HEIGHT - WALL_HEIGHT) + 0.3
    x = STABLE_LEFT
    while x <= STABLE_RIGHT + 0.01:
        for sign in (1, -1):
            add_box(builder, (0.14, rafter_length, 0.18),
                    (x, ridge_y - sign * depth / 4, (WALL_HEIGHT + RIDGE_HEIGHT) / 2 + 0.1), (sign * slope, 0.0, 0.0))
        x += 0.9
    add_box(builder, (STABLE_RIGHT - STABLE_LEFT + 0.4, 0.22, 0.22), (0.0, ridge_y, RIDGE_HEIGHT + 0.15))
    for y in (STABLE_FRONT + 1.6, STABLE_BACK - 1.6):
        add_box(builder, (STABLE_RIGHT - STABLE_LEFT, 0.2, 0.2), (0.0, y, WALL_HEIGHT + 0.05),
                (0.0, 0.0, generator.uniform(-0.01, 0.01)))
    mesh_object("stable_rafters", builder, collection, beams, texture_size=1.2)
    roof = bmesh.new()
    for sign in (1, -1):
        add_box(roof, (STABLE_RIGHT - STABLE_LEFT + 0.8, rafter_length + 0.4, 0.12),
                (0.0, ridge_y - sign * depth / 4, (WALL_HEIGHT + RIDGE_HEIGHT) / 2 + 0.3), (sign * slope, 0.0, 0.0))
    mesh_object("stable_roof", roof, collection, thatch, texture_size=1.5)


def build_floor(collection, generator):
    dirt = tinted_texture_material("dirt_floor", "stable_dirt", (0.42, 0.34, 0.28))
    box_object("stable_floor", (STABLE_RIGHT - STABLE_LEFT + 0.8, STABLE_BACK - STABLE_FRONT + 0.2, 0.1),
               (0.2, (STABLE_FRONT + STABLE_BACK) / 2, -0.05), collection, dirt, texture_size=2.5)
    straw = flat_material("straw", (0.5, 0.36, 0.17), 0.9)
    builder = bmesh.new()
    for _ in range(16):
        center = (generator.uniform(STABLE_LEFT + 0.3, STABLE_RIGHT - 0.3),
                  generator.uniform(STABLE_FRONT + 0.3, STABLE_BACK - 0.3), 0.0)
        add_straw(builder, generator, center, generator.uniform(0.25, 0.7), 120, height=0.04, lift=0.12)
    add_straw(builder, generator, (2.3, 2.9, 0.0), 1.4, 900, height=0.08, lift=0.2)
    add_straw(builder, generator, (-3.6, 4.4, 0.0), 0.9, 500, length=(0.2, 0.45), height=0.35, lift=0.5)
    mesh_object("stable_floor_straw", builder, collection, straw)


def build_props(collection):
    beams = bpy.data.materials["stable_beams"]
    builder = bmesh.new()
    add_box(builder, (1.4, 0.06, 0.06), (DOOR_RIGHT + 1.0, STABLE_BACK - 0.12, 2.45), (0.0, math.radians(-25), 0.0))
    mesh_object("stable_hanging_stick", builder, collection, beams, texture_size=1.0)
    bucket = flat_material("bucket_wood", (0.32, 0.2, 0.12), 0.85)
    pail = bmesh.new()
    add_cylinder(pail, 0.16, 0.28, (DOOR_RIGHT + 0.85, STABLE_BACK - 0.25, 1.75), segments=14, tip_radius=0.19)
    mesh_object("stable_bucket", pail, collection, bucket)


def build_manger(collection, generator):
    wood = tinted_texture_material("old_wood_floor", "manger_wood", (0.5, 0.34, 0.22))
    center_x, center_y, rim = 2.3, 2.9, 0.78
    length, width = 1.5, 0.75
    builder = bmesh.new()
    for x in (center_x - length / 2 + 0.1, center_x + length / 2 - 0.1):
        for y in (center_y - width / 2 + 0.05, center_y + width / 2 - 0.05):
            add_box(builder, (0.09, 0.09, rim + 0.05), (x, y, (rim + 0.05) / 2),
                    (math.copysign(0.12, y - center_y), 0.0, 0.0))
    side_angle = math.radians(28)
    for sign in (1, -1):
        add_box(builder, (length, 0.045, 0.42), (center_x, center_y + sign * (width / 2 - 0.08), rim - 0.17),
                (sign * side_angle, 0.0, 0.0))
        add_box(builder, (length + 0.1, 0.07, 0.07), (center_x, center_y + sign * width / 2, rim + 0.02))
    for x in (center_x - length / 2, center_x + length / 2):
        add_box(builder, (0.05, width, 0.4), (x, center_y, rim - 0.18))
    add_box(builder, (length, 0.18, 0.04), (center_x, center_y, rim - 0.38))
    mesh_object("manger_trough", builder, collection, wood, texture_size=0.8)
    hay_material = tinted_texture_material("thatch_roof_angled", "manger_hay", (1.0, 0.82, 0.55))
    hay = bmesh.new()
    soft_mound(hay, (center_x, center_y, rim - 0.12), length / 2, width / 2 + 0.05, 0.16, 16, generator)
    mesh_object("manger_hay", hay, collection, hay_material, texture_size=0.5)
    straw = bpy.data.materials["straw"]
    stalks = bmesh.new()
    add_straw(stalks, generator, (center_x, center_y, rim - 0.02), 0.75, 900, length=(0.1, 0.28), height=0.08, lift=0.6)
    mesh_object("manger_straw", stalks, collection, straw)


def build_candle(collection):
    wax = flat_material("candle_wax", (0.92, 0.86, 0.7), 0.5)
    flame = flat_material("candle_flame", (1.0, 0.7, 0.3), 0.5, emission=(1.0, 0.62, 0.22), emission_strength=25.0)
    clay = flat_material("candle_clay", (0.42, 0.24, 0.14), 0.9)
    holder = bmesh.new()
    add_cylinder(holder, 0.07, 0.03, (1.62, 2.55, 0.81), segments=16, tip_radius=0.05)
    mesh_object("candle_dish", holder, collection, clay)
    body = bmesh.new()
    add_cylinder(body, 0.018, 0.09, (1.62, 2.55, 0.87), segments=10)
    mesh_object("candle_body", body, collection, wax)
    tip = bmesh.new()
    add_cylinder(tip, 0.012, 0.045, (1.62, 2.55, 0.94), segments=8, tip_radius=0.0)
    mesh_object("candle_flame", tip, collection, flame)
    light_data = bpy.data.lights.new("candle_light", "POINT")
    light_data.color = (1.0, 0.62, 0.28)
    light_data.energy = 110.0
    light_data.shadow_soft_size = 0.05
    light = bpy.data.objects.new("candle_light", light_data)
    light.location = (1.62, 2.5, 1.02)
    collection.objects.link(light)
    glow_data = bpy.data.lights.new("manger_glow", "POINT")
    glow_data.color = (1.0, 0.75, 0.4)
    glow_data.energy = 35.0
    glow_data.shadow_soft_size = 0.6
    glow = bpy.data.objects.new("manger_glow", glow_data)
    glow.location = (2.3, 2.9, 1.15)
    collection.objects.link(glow)
    fill_data = bpy.data.lights.new("stable_fill", "AREA")
    fill_data.color = (1.0, 0.6, 0.35)
    fill_data.energy = 45.0
    fill_data.size = 3.0
    fill = bpy.data.objects.new("stable_fill", fill_data)
    fill.location = (2.5, 0.0, 3.0)
    fill.rotation_euler = (math.radians(40), 0.0, 0.0)
    collection.objects.link(fill)


def build_stable():
    clear_default_objects()
    generator = rng(1224)
    collection = fresh_collection("Stable")
    build_walls(collection, generator)
    build_door_frame(collection)
    build_stone_wall(collection, generator)
    build_roof(collection, generator)
    build_floor(collection, generator)
    build_props(collection)
    build_manger(collection, generator)
    build_candle(collection)
    return len(collection.objects)


print("stable objects:", build_stable())
