def build_ground(collection):
    ground = tinted_texture_material("dry_ground_rocks", "land_ground", (0.55, 0.6, 0.65))
    builder = bmesh.new()
    columns, rows = 90, 70
    x_from, x_to, y_from, y_to = -220.0, 160.0, 4.8, 330.0
    grid = []
    for row in range(rows + 1):
        fraction = row / rows
        y = y_from + (y_to - y_from) * fraction ** 1.8
        line = []
        for column in range(columns + 1):
            x = x_from + (x_to - x_from) * column / columns
            line.append(builder.verts.new((x, y, ground_height(x, y))))
        grid.append(line)
    for row in range(rows):
        for column in range(columns):
            builder.faces.new((grid[row][column], grid[row][column + 1], grid[row + 1][column + 1],
                               grid[row + 1][column]))
    mesh_object("land_ground", builder, collection, ground, texture_size=4.0)


def build_mountains(collection, generator):
    rock = flat_material("mountain_rock", (0.16, 0.15, 0.24), 1.0)
    builder = bmesh.new()
    columns, rows = 120, 14
    x_from, x_to = -420.0, 320.0
    peaks = [(generator.uniform(x_from, x_to), generator.uniform(25, 70), generator.uniform(30, 90)) for _ in range(16)]
    grid = []
    for row in range(rows + 1):
        depth = row / rows
        y = 170.0 + depth * 140.0
        line = []
        for column in range(columns + 1):
            x = x_from + (x_to - x_from) * column / columns
            height = 6.0
            for peak_x, peak_height, peak_width in peaks:
                height = max(height, peak_height * math.exp(-((x - peak_x) / peak_width) ** 2))
            height += generator.uniform(-2.5, 2.5)
            profile = math.sin(depth * math.pi) ** 0.6
            line.append(builder.verts.new((x, y, height * profile)))
        grid.append(line)
    for row in range(rows):
        for column in range(columns):
            builder.faces.new((grid[row][column], grid[row][column + 1], grid[row + 1][column + 1],
                               grid[row + 1][column]))
    mesh_object("land_mountains", builder, collection, rock)
    nearer = flat_material("hill_dusk", (0.1, 0.11, 0.2), 1.0)
    hills = bmesh.new()
    for index in range(9):
        x = -170.0 + index * 40.0 + generator.uniform(-10, 10)
        y = generator.uniform(110, 150)
        radius = generator.uniform(30, 55)
        bmesh.ops.create_uvsphere(hills, u_segments=24, v_segments=10, radius=1.0,
                                  matrix=Matrix.Translation((x, y, -2.0)) @ Matrix.Diagonal((radius, radius * 0.6,
                                                                                               generator.uniform(10, 22), 1.0)))
    mesh_object("land_hills", hills, collection, nearer)


def add_tree(builder_trunks, builder_leaves, generator, x, y, kind):
    base_z = ground_height(x, y)
    if kind == "palm":
        height = generator.uniform(6.0, 9.0)
        lean = generator.uniform(-0.15, 0.15)
        add_cylinder(builder_trunks, 0.22, height, (x, y, base_z + height / 2), (lean, 0.0, 0.0), 6, tip_radius=0.15)
        top = Vector((x, y - math.sin(lean) * height / 2 * 2, base_z + height))
        for frond in range(9):
            angle = frond / 9 * math.tau + generator.uniform(-0.2, 0.2)
            direction = Vector((math.cos(angle), math.sin(angle), -0.35))
            add_box(builder_leaves, (3.2, 0.55, 0.05), top + direction * 1.4,
                    (0.0, math.radians(20), angle))
    else:
        height = generator.uniform(2.0, 3.6)
        add_cylinder(builder_trunks, 0.25, height, (x, y, base_z + height / 2), segments=6, tip_radius=0.18)
        for blob in range(3):
            offset = Vector((generator.uniform(-1, 1), generator.uniform(-1, 1), generator.uniform(0, 1)))
            radius = generator.uniform(1.4, 2.3)
            bmesh.ops.create_icosphere(builder_leaves, subdivisions=2, radius=1.0,
                                       matrix=Matrix.Translation((x + offset.x, y + offset.y,
                                                                  base_z + height + offset.z)) @
                                       Matrix.Diagonal((radius, radius, radius * 0.75, 1.0)))


def build_trees(collection, generator):
    trunks = bmesh.new()
    leaves = bmesh.new()
    placed = 0
    while placed < 70:
        x = generator.uniform(-90, 30)
        y = generator.uniform(52, 95)
        if (Vector((x, y, 0)) - TOWN_CENTER).length < 16:
            continue
        add_tree(trunks, leaves, generator, x, y, "palm" if generator.random() < 0.35 else "olive")
        placed += 1
    for _ in range(14):
        x = generator.uniform(-40, 8)
        y = generator.uniform(24, 48)
        if (Vector((x, y, 0)) - TOWN_CENTER).length < 14:
            continue
        add_tree(trunks, leaves, generator, x, y, "palm" if generator.random() < 0.5 else "olive")
    mesh_object("land_tree_trunks", trunks, collection, flat_material("tree_bark", (0.12, 0.09, 0.08), 1.0))
    mesh_object("land_tree_leaves", leaves, collection, flat_material("tree_leaves", (0.06, 0.1, 0.09), 1.0))


def add_house(walls, windows, generator, x, y, width, depth, height, rotation):
    base = ground_height(x, y) - 0.4
    turn = Matrix.Rotation(rotation, 4, "Z")
    center = Vector((x, y, base + height / 2))
    add_box(walls, (width, depth, height), center, (0.0, 0.0, rotation))
    add_box(walls, (width + 0.3, depth + 0.3, 0.18), center + Vector((0, 0, height / 2 + 0.05)), (0.0, 0.0, rotation))
    if generator.random() < 0.4:
        add_box(walls, (width * 0.45, depth * 0.5, height * 0.45),
                center + turn @ Vector((width * 0.2, 0.0, height * 0.72)), (0.0, 0.0, rotation))
    for _ in range(generator.randint(1, 3)):
        if generator.random() < 0.55:
            local = Vector((generator.uniform(-width / 2 + 0.6, width / 2 - 0.6), -depth / 2 - 0.03,
                            generator.uniform(-height / 2 + 1.0, height / 2 - 0.6)))
            add_box(windows, (0.45, 0.06, 0.6), center + turn @ local, (0.0, 0.0, rotation))
    if generator.random() < 0.6:
        local = Vector((generator.uniform(-width / 2 + 0.8, width / 2 - 0.8), -depth / 2 - 0.03, -height / 2 + 1.0))
        add_box(windows, (0.8, 0.06, 1.6), center + turn @ local, (0.0, 0.0, rotation))


def build_town(collection, generator):
    stone = tinted_texture_material("sandstone_blocks_08", "town_stone", (0.62, 0.6, 0.68))
    walls = bmesh.new()
    windows = bmesh.new()
    houses = 0
    while houses < 34:
        offset = Vector((generator.gauss(0, 6.5), generator.gauss(0, 5.0), 0.0))
        position = TOWN_CENTER + offset
        size_falloff = 1.0 - min(offset.length / 18.0, 0.6)
        add_house(walls, windows, generator, position.x, position.y, generator.uniform(3.0, 6.0),
                  generator.uniform(3.0, 5.5), generator.uniform(2.8, 4.6) * (0.7 + size_falloff * 0.6),
                  generator.uniform(-0.3, 0.3))
        houses += 1
    add_box(walls, (3.0, 3.0, 9.0), TOWN_CENTER + Vector((2.0, 4.0, ground_height(-8, 46) + 3.5)))
    mesh_object("town_houses", walls, collection, stone, texture_size=2.5)
    light = flat_material("town_window_light", (0.2, 0.1, 0.03), 0.8, emission=(1.0, 0.62, 0.25),
                          emission_strength=12.0)
    mesh_object("town_windows_lit", windows, collection, light)
    lantern_data = bpy.data.lights.new("town_glow", "POINT")
    lantern_data.color = (1.0, 0.6, 0.3)
    lantern_data.energy = 2500.0
    lantern_data.shadow_soft_size = 4.0
    lantern = bpy.data.objects.new("town_glow", lantern_data)
    lantern.location = TOWN_CENTER + Vector((0.0, -9.0, 5.0))
    collection.objects.link(lantern)


def build_path(collection, generator):
    path = tinted_texture_material("dirt", "land_path", (0.55, 0.55, 0.6)) if bpy.data.materials.get("dirt") else \
        flat_material("land_path", (0.2, 0.2, 0.24), 1.0)
    builder = bmesh.new()
    points = [Vector((-2.2, 5.2, 0.0)), Vector((-3.5, 10.0, 0.0)), Vector((-6.0, 18.0, 0.0)),
              Vector((-8.0, 28.0, 0.0)), Vector((-9.5, 34.0, 0.0))]
    left, right = [], []
    for index, point in enumerate(points):
        following = points[min(index + 1, len(points) - 1)]
        previous = points[max(index - 1, 0)]
        direction = (following - previous).normalized()
        side = Vector((direction.y, -direction.x, 0.0)) * (1.6 - index * 0.15)
        for target, sign in ((left, -1), (right, 1)):
            edge = point + side * sign
            target.append(builder.verts.new((edge.x, edge.y, ground_height(edge.x, edge.y) + 0.03)))
    for index in range(len(points) - 1):
        builder.faces.new((left[index], right[index], right[index + 1], left[index + 1]))
    mesh_object("land_path", builder, collection, path, texture_size=3.0)


def build_bushes(collection, generator):
    bushes = bmesh.new()
    for _ in range(60):
        x = generator.uniform(-30, 12)
        y = generator.uniform(7, 40)
        if -9 < x < -0.5 and y < 22:
            continue
        radius = generator.uniform(0.3, 0.9)
        bmesh.ops.create_icosphere(bushes, subdivisions=1, radius=1.0,
                                   matrix=Matrix.Translation((x, y, ground_height(x, y) + radius * 0.3)) @
                                   Matrix.Diagonal((radius, radius, radius * 0.6, 1.0)))
    mesh_object("land_bushes", bushes, collection, flat_material("bush", (0.07, 0.11, 0.08), 1.0))
    rocks = bmesh.new()
    for _ in range(90):
        x = generator.uniform(-25, 10)
        y = generator.uniform(6, 35)
        size = generator.uniform(0.08, 0.4)
        bmesh.ops.create_icosphere(rocks, subdivisions=1, radius=size,
                                   matrix=Matrix.Translation((x, y, ground_height(x, y))))
    mesh_object("land_rocks", rocks, collection, flat_material("pebble", (0.22, 0.22, 0.26), 1.0))


def build_land():
    collection = fresh_collection("Land")
    generator = rng(33)
    build_ground(collection)
    build_path(collection, generator)
    build_bushes(collection, generator)
    build_trees(collection, generator)
    build_mountains(collection, generator)
    town = fresh_collection("Town")
    build_town(town, generator)
    return len(collection.objects) + len(town.objects)


print("land objects:", build_land())
