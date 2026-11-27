MANGER_CENTER = (2.3, 2.9)
STABLE_DOOR = (-2.2, 5.0)

STANDING_BODY = [(0.02, 0.02, 0.29, 0.25), (0.01, 0.45, 0.24, 0.19), (0.0, 0.9, 0.19, 0.13), (0.0, 1.2, 0.21, 0.13),
                 (0.0, 1.38, 0.17, 0.11), (0.0, 1.47, 0.065, 0.065)]
KNEELING_BODY = [(0.08, 0.02, 0.27, 0.4), (0.05, 0.3, 0.24, 0.3), (0.0, 0.6, 0.19, 0.14), (0.0, 0.88, 0.21, 0.13),
                 (0.0, 1.05, 0.17, 0.11), (0.0, 1.14, 0.065, 0.065)]
SEATED_BODY = [(0.0, 0.0, 0.24, 0.3), (0.0, 0.35, 0.2, 0.14), (0.0, 0.6, 0.2, 0.13), (0.0, 0.72, 0.16, 0.1),
               (0.0, 0.8, 0.065, 0.065)]


def cloth(name, color):
    return flat_material(name, color, 0.9)


SKIN = flat_material("skin_light", (0.72, 0.5, 0.36), 0.6)
SKIN_OLIVE = flat_material("skin_olive", (0.6, 0.42, 0.29), 0.6)
SKIN_DARK = flat_material("skin_dark", (0.33, 0.2, 0.13), 0.6)
HAIR_DARK = flat_material("hair_dark", (0.06, 0.04, 0.03), 0.8)
HAIR_BROWN = flat_material("hair_brown", (0.22, 0.14, 0.08), 0.8)
HAIR_GREY = flat_material("hair_grey", (0.6, 0.58, 0.55), 0.8)
HAIR_WHITE = flat_material("hair_white", (0.85, 0.84, 0.8), 0.8)
GOLD = flat_material("gold", (0.85, 0.62, 0.22), 0.35)
STAFF_WOOD = flat_material("staff_wood", (0.3, 0.19, 0.1), 0.8)


def robe(figure, material, profile, scale=1.0):
    points = [(0.0, y * scale, z * scale) for y, z, _, _ in profile]
    radii = [(rx * scale, ry * scale) for _, _, rx, ry in profile]
    figure.add(material, add_tube, points, radii, 14)


def neck_top(profile, scale=1.0):
    return Vector((0.0, profile[-1][0] * scale, profile[-1][1] * scale))


def head(figure, skin, center, size=0.105):
    center = Vector(center)
    figure.add(skin, add_ellipsoid, center, (size * 0.86, size * 0.92, size * 1.08))
    figure.add(skin, add_ellipsoid, center + Vector((0.0, -size * 0.92, -size * 0.12)), (size * 0.16, size * 0.2,
                                                                                         size * 0.28), 1)


def hood(figure, material, center, size=0.105, drape=0.28, width=1.0):
    center = Vector(center)
    figure.add(material, add_ellipsoid, center + Vector((0.0, size * 0.32, size * 0.18)),
               (size * 1.12 * width, size * 1.08, size * 1.14))
    figure.add(material, add_tube, [center + Vector((0.0, size * 0.45, 0.0)),
                                    center + Vector((0.0, size * 0.6, -drape * 0.5)),
                                    center + Vector((0.0, size * 0.5, -drape))],
               [(size * 1.05 * width, size * 0.9), (size * 1.5 * width, size * 1.0), (size * 1.9 * width, size * 1.1)], 12)


def headband(figure, material, center, size=0.105):
    center = Vector(center) + Vector((0.0, size * 0.18, size * 0.42))
    points = [center + Vector((math.cos(angle) * size * 1.14, math.sin(angle) * size * 1.1, 0.0))
              for angle in [step / 16 * math.tau for step in range(16)]]
    figure.add(material, add_tube, points, [size * 0.12] * 16, 6, True)


def hair(figure, material, center, size=0.105, length=0.0):
    center = Vector(center)
    figure.add(material, add_ellipsoid, center + Vector((0.0, size * 0.22, size * 0.12)), (size * 0.98, size * 0.95,
                                                                                          size * 1.08))
    if length:
        figure.add(material, add_tube, [center + Vector((0.0, size * 0.4, 0.0)), center + Vector((0.0, size * 0.45,
                                                                                                 -length))],
                   [(size * 0.95, size * 0.6), (size * 1.05, size * 0.5)], 10)


def beard(figure, material, center, size=0.105, length=0.14):
    center = Vector(center)
    chin = center + Vector((0.0, -size * 0.62, -size * 0.55))
    figure.add(material, add_tube, [chin + Vector((0.0, 0.03, 0.04)), chin + Vector((0.0, 0.0, -length * 0.5)),
                                    chin + Vector((0.0, 0.02, -length))],
               [(size * 0.75, size * 0.45), (size * 0.6, size * 0.4), (size * 0.15, size * 0.12)], 10)


def arm(figure, sleeve, skin, shoulder, elbow, wrist, width=0.07):
    shoulder, elbow, wrist = Vector(shoulder), Vector(elbow), Vector(wrist)
    figure.add(sleeve, add_tube, [shoulder, elbow, wrist], [width * 1.05, width, width * 1.15], 10)
    direction = (wrist - elbow).normalized()
    figure.add(skin, add_ellipsoid, wrist + direction * 0.06, (0.035, 0.045, 0.05), 1)


def turban(figure, material, center, size=0.105, accent=None):
    center = Vector(center)
    figure.add(material, add_ellipsoid, center + Vector((0.0, size * 0.15, size * 0.65)), (size * 1.35, size * 1.3,
                                                                                         size * 0.85))
    if accent:
        figure.add(accent, add_ellipsoid, center + Vector((0.0, -size * 1.05, size * 0.75)), (size * 0.2, size * 0.12,
                                                                                           size * 0.25), 1)


def crown(figure, center, size=0.105):
    base = Vector(center) + Vector((0.0, size * 0.1, size * 0.75))
    points = [base + Vector((math.cos(angle) * size * 0.95, math.sin(angle) * size * 0.95, 0.0))
              for angle in [step / 14 * math.tau for step in range(14)]]
    figure.add(GOLD, add_tube, points, [(size * 0.12, size * 0.25)] * 14, 6, True)
    for spike in range(7):
        angle = spike / 7 * math.tau
        figure.add(GOLD, add_cylinder, size * 0.12, size * 0.5,
                   base + Vector((math.cos(angle) * size * 0.95, math.sin(angle) * size * 0.95, size * 0.3)),
                   segments=5, tip_radius=0.0)


def belt(figure, material, height, radius_x, radius_y, y=0.0):
    points = [Vector((math.cos(angle) * radius_x, y + math.sin(angle) * radius_y, height))
              for angle in [step / 16 * math.tau for step in range(16)]]
    figure.add(material, add_tube, points, [0.025] * 16, 6, True)


def bend_upper_body(figure, pivot, angle, start=0.0):
    for vertex in figure.builder.verts:
        height = vertex.co.z - pivot
        if height <= 0.0:
            continue
        weight = min(1.0, height / 0.3)
        turn = angle * weight
        y = vertex.co.y - start
        vertex.co.y = start + y * math.cos(turn) - height * math.sin(turn)
        vertex.co.z = pivot + y * math.sin(turn) + height * math.cos(turn)


def lamb(builder_figure, center):
    wool = flat_material("lamb_wool", (0.88, 0.85, 0.78), 1.0)
    face = flat_material("lamb_face", (0.55, 0.45, 0.38), 0.8)
    center = Vector(center)
    builder_figure.add(wool, add_ellipsoid, center, (0.2, 0.12, 0.11))
    for offset in ((-0.1, 0.0, 0.06), (0.05, 0.05, 0.07), (0.1, -0.04, 0.05), (-0.03, -0.05, 0.08)):
        builder_figure.add(wool, add_ellipsoid, center + Vector(offset), (0.07, 0.07, 0.06), 1)
    builder_figure.add(face, add_ellipsoid, center + Vector((0.22, -0.02, 0.06)), (0.07, 0.05, 0.05), 1)
    for side in (-1, 1):
        builder_figure.add(face, add_ellipsoid, center + Vector((0.2, side * 0.05, 0.1)), (0.035, 0.012, 0.02), 1)
        builder_figure.add(wool, add_tube, [center + Vector((0.12 * side, -0.04, -0.05)),
                                            center + Vector((0.14 * side, -0.07, -0.17))], [0.025, 0.02], 6)


def jar(builder_figure, center, body_material):
    center = Vector(center)
    builder_figure.add(body_material, add_ellipsoid, center, (0.09, 0.09, 0.11))
    builder_figure.add(body_material, add_cylinder, 0.04, 0.08, center + Vector((0, 0, 0.13)), segments=12,
                       tip_radius=0.05)
    builder_figure.add(GOLD, add_ellipsoid, center + Vector((0, 0, 0.19)), (0.05, 0.05, 0.03), 1)
    builder_figure.add(GOLD, add_tube, [center + Vector((math.cos(angle) * 0.092, math.sin(angle) * 0.092, 0.02))
                                        for angle in [step / 12 * math.tau for step in range(12)]], [0.012] * 12, 6,
                       True)


def build_mary(collection):
    veil = cloth("mary_veil", (0.86, 0.8, 0.7))
    dress = cloth("mary_dress", (0.62, 0.55, 0.47))
    figure = Figure("mary")
    robe(figure, dress, KNEELING_BODY)
    face = neck_top(KNEELING_BODY) + Vector((0.0, -0.02, 0.14))
    head(figure, SKIN, face, 0.1)
    hair(figure, HAIR_DARK, face, 0.1, 0.25)
    hood(figure, veil, face + Vector((0.0, 0.02, 0.0)), 0.108, 0.45, 1.1)
    for side in (-1, 1):
        arm(figure, veil, SKIN, (side * 0.2, 0.0, 1.04), (side * 0.22, -0.2, 0.86), (side * 0.13, -0.38, 0.8), 0.075)
    bend_upper_body(figure, 0.6, 0.4)
    return figure.finish(collection, (2.4, 3.62, 0.0), facing_point=(2.35, 2.7))


def build_joseph(collection):
    headcloth = cloth("joseph_headcloth", (0.78, 0.68, 0.5))
    band = cloth("joseph_band", (0.24, 0.36, 0.27))
    tunic = cloth("joseph_robe", (0.46, 0.33, 0.22))
    figure = Figure("joseph")
    robe(figure, tunic, STANDING_BODY)
    face = neck_top(STANDING_BODY) + Vector((0.0, -0.02, 0.14))
    head(figure, SKIN, face)
    beard(figure, HAIR_BROWN, face, 0.105, 0.12)
    hood(figure, headcloth, face, 0.108, 0.42, 1.05)
    headband(figure, band, face, 0.108)
    for side in (-1, 1):
        arm(figure, headcloth if side > 0 else tunic, SKIN, (side * 0.2, 0.0, 1.37), (side * 0.25, -0.18, 1.12),
            (side * 0.17, -0.42, 0.97))
    bend_upper_body(figure, 0.95, 0.28)
    return figure.finish(collection, (3.35, 3.35, 0.0), facing_point=MANGER_CENTER)


def build_old_shepherd(collection):
    mantle = cloth("old_shepherd_mantle", (0.42, 0.33, 0.29))
    figure = Figure("old_shepherd")
    robe(figure, mantle, STANDING_BODY)
    face = neck_top(STANDING_BODY) + Vector((0.0, -0.02, 0.14))
    head(figure, SKIN_OLIVE, face)
    beard(figure, HAIR_WHITE, face, 0.105, 0.3)
    hood(figure, mantle, face, 0.11, 0.5, 1.1)
    arm(figure, mantle, SKIN_OLIVE, (0.2, 0.0, 1.37), (0.3, -0.14, 1.12), (0.27, -0.2, 1.3))
    arm(figure, mantle, SKIN_OLIVE, (-0.2, 0.0, 1.37), (-0.06, -0.24, 1.15), (0.2, -0.22, 1.22))
    figure.add(STAFF_WOOD, add_cylinder, 0.022, 2.0, (0.27, -0.24, 1.0), segments=8)
    curve = [Vector((0.27 - 0.1 + math.cos(angle) * 0.1, -0.24, 2.0 + math.sin(angle) * 0.1))
             for angle in [step / 8 * math.pi for step in range(9)]]
    figure.add(STAFF_WOOD, add_tube, curve, [0.02] * len(curve), 6)
    bend_upper_body(figure, 1.0, 0.12)
    return figure.finish(collection, (1.5, 4.2, 0.0), facing_point=MANGER_CENTER)


def build_shawl_woman(collection):
    shawl = cloth("woman_shawl", (0.86, 0.55, 0.17))
    band = cloth("woman_band", (0.1, 0.5, 0.55))
    dress = cloth("woman_dress", (0.4, 0.26, 0.17))
    figure = Figure("shawl_woman")
    robe(figure, dress, STANDING_BODY)
    face = neck_top(STANDING_BODY) + Vector((0.0, -0.02, 0.14))
    head(figure, SKIN_OLIVE, face, 0.1)
    hood(figure, shawl, face, 0.112, 0.6, 1.3)
    headband(figure, band, face + Vector((0.0, 0.0, 0.02)), 0.112)
    arm(figure, shawl, SKIN_OLIVE, (0.2, 0.0, 1.37), (0.22, -0.25, 1.15), (0.08, -0.48, 1.02))
    arm(figure, shawl, SKIN_OLIVE, (-0.2, 0.0, 1.37), (-0.24, -0.22, 1.1), (-0.15, -0.45, 0.98))
    bend_upper_body(figure, 0.95, 0.38)
    return figure.finish(collection, (2.8, 4.3, 0.0), facing_point=(2.4, 3.3))


def build_lamb_bearer(collection):
    hooded = cloth("lamb_bearer_hood", (0.8, 0.75, 0.64))
    tunic = cloth("lamb_bearer_tunic", (0.58, 0.55, 0.5))
    figure = Figure("lamb_bearer")
    robe(figure, tunic, STANDING_BODY, 0.95)
    face = neck_top(STANDING_BODY, 0.95) + Vector((0.0, -0.02, 0.13))
    head(figure, SKIN, face, 0.1)
    hood(figure, hooded, face, 0.106, 0.4, 1.1)
    lamb(figure, (0.0, -0.26, 1.08))
    for side in (-1, 1):
        arm(figure, hooded, SKIN, (side * 0.19, 0.0, 1.3), (side * 0.23, -0.17, 1.0), (side * -0.02, -0.3, 1.0))
    bend_upper_body(figure, 0.9, 0.1)
    return figure.finish(collection, (0.85, 3.8, 0.0), facing_point=MANGER_CENTER)


def build_kneeling_shepherd(collection):
    cloak = cloth("kneeling_cloak", (0.5, 0.2, 0.14))
    fur = flat_material("sheepskin", (0.33, 0.24, 0.16), 1.0)
    figure = Figure("kneeling_shepherd")
    robe(figure, cloak, KNEELING_BODY)
    figure.add(fur, add_ellipsoid, (0.0, 0.03, 0.98), (0.3, 0.22, 0.16))
    figure.add(fur, add_ellipsoid, (0.0, 0.12, 0.7), (0.26, 0.16, 0.3))
    face = neck_top(KNEELING_BODY) + Vector((0.0, -0.02, 0.14))
    head(figure, SKIN_OLIVE, face)
    hair(figure, HAIR_BROWN, face, 0.108, 0.2)
    beard(figure, HAIR_BROWN, face, 0.105, 0.2)
    for side in (-1, 1):
        arm(figure, cloak, SKIN_OLIVE, (side * 0.2, 0.0, 1.04), (side * 0.17, -0.2, 0.86), (side * 0.03, -0.3, 0.98))
    bend_upper_body(figure, 0.6, 0.3)
    return figure.finish(collection, (0.3, 2.45, 0.0), facing_point=MANGER_CENTER)


def build_crouching_shepherd(collection):
    headcloth = cloth("crouching_headcloth", (0.6, 0.5, 0.38))
    band = cloth("crouching_band", (0.3, 0.2, 0.14))
    tunic = cloth("crouching_tunic", (0.38, 0.32, 0.27))
    figure = Figure("crouching_shepherd")
    robe(figure, tunic, KNEELING_BODY)
    face = neck_top(KNEELING_BODY) + Vector((0.0, -0.02, 0.14))
    head(figure, SKIN_OLIVE, face)
    beard(figure, HAIR_GREY, face, 0.105, 0.14)
    hood(figure, headcloth, face, 0.108, 0.42, 1.1)
    headband(figure, band, face, 0.108)
    arm(figure, headcloth, SKIN_OLIVE, (0.2, 0.0, 1.04), (0.22, -0.32, 0.98), (0.12, -0.6, 0.98))
    arm(figure, tunic, SKIN_OLIVE, (-0.2, 0.0, 1.04), (-0.24, -0.18, 0.8), (-0.2, -0.28, 0.6))
    bend_upper_body(figure, 0.5, 0.7)
    return figure.finish(collection, (1.15, 1.95, 0.0), facing_point=(1.75, 2.6))


def build_child(collection):
    tunic = cloth("child_tunic", (0.42, 0.3, 0.2))
    figure = Figure("child")
    robe(figure, tunic, STANDING_BODY, 0.62)
    face = neck_top(STANDING_BODY, 0.62) + Vector((0.0, -0.02, 0.11))
    head(figure, SKIN, face, 0.095)
    hair(figure, HAIR_BROWN, face, 0.1)
    for side in (-1, 1):
        arm(figure, tunic, SKIN, (side * 0.13, 0.0, 0.85), (side * 0.15, -0.15, 0.72), (side * 0.1, -0.3, 0.8), 0.045)
    return figure.finish(collection, (1.85, 1.85, 0.0), facing_point=MANGER_CENTER)


def build_baby(collection):
    swaddle = cloth("baby_swaddle", (0.93, 0.9, 0.84))
    figure = Figure("baby_jesus")
    figure.add(swaddle, add_ellipsoid, (0.0, 0.0, 0.0), (0.21, 0.1, 0.075))
    figure.add(swaddle, add_ellipsoid, (0.17, 0.0, 0.02), (0.08, 0.095, 0.08))
    head(figure, SKIN, (0.24, 0.0, 0.04), 0.068)
    hair(figure, HAIR_BROWN, (0.25, 0.0, 0.045), 0.066)
    obj = figure.finish(collection, (2.25, 2.9, 0.8), yaw=math.radians(-10))
    obj.rotation_euler = (0.0, math.radians(-12), math.radians(-10))
    return obj


def build_red_king(collection):
    robe_red = cloth("red_king_robe", (0.5, 0.06, 0.1))
    cloak = cloth("red_king_cloak", (0.62, 0.16, 0.22))
    turban_cloth = cloth("red_king_turban", (0.75, 0.2, 0.2))
    vessel = flat_material("king_vessel", (0.05, 0.07, 0.12), 0.25)
    figure = Figure("king_with_gift")
    robe(figure, robe_red, STANDING_BODY, 1.03)
    figure.add(cloak, add_tube, [(0.0, 0.08, 1.45), (0.0, 0.12, 0.8), (0.0, 0.14, 0.05)],
               [(0.24, 0.16), (0.3, 0.18), (0.36, 0.2)], 14)
    belt(figure, GOLD, 0.95, 0.2, 0.14)
    face = neck_top(STANDING_BODY, 1.03) + Vector((0.0, -0.02, 0.14))
    head(figure, SKIN_OLIVE, face)
    beard(figure, HAIR_GREY, face, 0.105, 0.22)
    turban(figure, turban_cloth, face, 0.11, GOLD)
    jar(figure, (0.0, -0.3, 1.12), vessel)
    for side in (-1, 1):
        arm(figure, cloak, SKIN_OLIVE, (side * 0.21, 0.0, 1.4), (side * 0.25, -0.16, 1.12), (side * 0.1, -0.28, 1.1))
    return figure.finish(collection, (-5.6, 9.5, ground_height(-5.6, 9.5)), facing_point=STABLE_DOOR)


def build_blue_king(collection):
    robe_blue = cloth("blue_king_robe", (0.13, 0.18, 0.42))
    sash = cloth("blue_king_sash", (0.55, 0.45, 0.2))
    figure = Figure("king_leading_camel")
    robe(figure, robe_blue, STANDING_BODY)
    belt(figure, sash, 0.95, 0.2, 0.14)
    face = neck_top(STANDING_BODY) + Vector((0.0, -0.02, 0.14))
    head(figure, SKIN_DARK, face)
    beard(figure, HAIR_DARK, face, 0.105, 0.1)
    crown(figure, face, 0.11)
    arm(figure, robe_blue, SKIN_DARK, (0.2, 0.0, 1.37), (0.3, -0.2, 1.15), (0.42, -0.35, 1.2))
    arm(figure, robe_blue, SKIN_DARK, (-0.2, 0.0, 1.37), (-0.22, -0.05, 1.05), (-0.2, -0.12, 0.8))
    return figure.finish(collection, (-5.0, 13.6, ground_height(-5.0, 13.6)), facing_point=STABLE_DOOR)


def build_riding_king():
    robe_purple = cloth("riding_king_robe", (0.32, 0.14, 0.3))
    turban_cloth = cloth("riding_king_turban", (0.85, 0.82, 0.74))
    figure = Figure("king_on_camel")
    robe(figure, robe_purple, SEATED_BODY)
    for side in (-1, 1):
        figure.add(robe_purple, add_tube, [(side * 0.12, -0.12, 0.08), (side * 0.32, -0.2, -0.2),
                                           (side * 0.32, -0.15, -0.6)], [0.09, 0.08, 0.07], 8)
    face = neck_top(SEATED_BODY) + Vector((0.0, -0.02, 0.14))
    head(figure, SKIN_OLIVE, face)
    beard(figure, HAIR_BROWN, face, 0.105, 0.16)
    turban(figure, turban_cloth, face, 0.11, GOLD)
    for side in (-1, 1):
        arm(figure, robe_purple, SKIN_OLIVE, (side * 0.2, 0.0, 0.7), (side * 0.22, -0.18, 0.45),
            (side * 0.08, -0.3, 0.4))
    return figure


def build_camel(name, collection, location, facing_point, standing, coat, blanket, rider=None):
    figure = Figure(name)
    hoof = flat_material("camel_hoof", (0.2, 0.15, 0.12), 0.9)
    if standing:
        body_z, leg_top = 1.45, 1.25
    else:
        body_z, leg_top = 0.55, 0.4
    figure.add(coat, add_ellipsoid, (0.0, 0.0, body_z), (0.36, 0.82, 0.4))
    figure.add(coat, add_ellipsoid, (0.0, 0.08, body_z + 0.36), (0.3, 0.42, 0.32))
    neck = [(0.0, -0.7, body_z + 0.05), (0.0, -1.0, body_z + 0.15), (0.0, -1.18, body_z + 0.5),
            (0.0, -1.22, body_z + 0.72)]
    figure.add(coat, add_tube, neck, [0.2, 0.15, 0.12, 0.1], 10)
    head_center = Vector((0.0, -1.38, body_z + 0.74))
    figure.add(coat, add_ellipsoid, head_center, (0.1, 0.24, 0.11))
    for side in (-1, 1):
        figure.add(coat, add_ellipsoid, head_center + Vector((side * 0.07, 0.15, 0.1)), (0.025, 0.02, 0.05), 1)
        figure.add(hoof, add_ellipsoid, head_center + Vector((side * 0.085, -0.06, 0.04)), (0.012, 0.012, 0.012), 1)
    figure.add(coat, add_tube, [(0.0, 0.8, body_z + 0.1), (0.0, 0.92, body_z - 0.25), (0.0, 0.93, body_z - 0.5)],
               [0.04, 0.03, 0.02], 6)
    for side in (-1, 1):
        for front in (-1, 1):
            x = side * 0.2
            y = front * -0.52
            if standing:
                points = [(x, y, leg_top), (x, y + 0.05, 0.8), (x, y - 0.03 * front, 0.45), (x, y, 0.06)]
                figure.add(coat, add_tube, points, [0.13, 0.07, 0.065, 0.055], 8)
                figure.add(hoof, add_ellipsoid, (x, y - 0.03, 0.04), (0.08, 0.11, 0.04), 1)
            else:
                points = [(x * 1.4, y, 0.35), (x * 1.6, y - 0.35, 0.1), (x * 1.5, y + 0.1, 0.08)]
                figure.add(coat, add_tube, points, [0.12, 0.08, 0.06], 8)
    figure.add(blanket, add_ellipsoid, (0.0, 0.08, body_z + 0.42), (0.34, 0.46, 0.22))
    figure.add(GOLD, add_tube, [Vector((math.cos(angle) * 0.35, 0.08 + math.sin(angle) * 0.47, body_z + 0.38))
                                for angle in [step / 16 * math.tau for step in range(16)]], [0.02] * 16, 6, True)
    ground = ground_height(*location)
    obj = figure.finish(collection, (location[0], location[1], ground), facing_point=facing_point)
    if rider:
        rider.finish(collection, (location[0], location[1], ground + body_z + 0.52), facing_point=facing_point)
    return obj


def build_figures():
    nativity = fresh_collection("Nativity")
    build_baby(nativity)
    build_mary(nativity)
    build_joseph(nativity)
    build_old_shepherd(nativity)
    build_shawl_woman(nativity)
    build_lamb_bearer(nativity)
    build_kneeling_shepherd(nativity)
    build_crouching_shepherd(nativity)
    build_child(nativity)
    kings = fresh_collection("Kings")
    tan = flat_material("camel_tan", (0.62, 0.5, 0.36), 0.95)
    pale = flat_material("camel_pale", (0.82, 0.77, 0.66), 0.95)
    red_blanket = cloth("camel_blanket_red", (0.55, 0.12, 0.12))
    blue_blanket = cloth("camel_blanket_blue", (0.18, 0.22, 0.45))
    green_blanket = cloth("camel_blanket_green", (0.2, 0.35, 0.25))
    build_red_king(kings)
    build_blue_king(kings)
    build_camel("camel_with_rider", kings, (-3.9, 14.8), (-1.5, 6.0), True, pale, red_blanket,
                build_riding_king())
    build_camel("camel_resting_left", kings, (-8.0, 11.5), (-2.0, 12.5), False, tan, blue_blanket)
    build_camel("camel_resting_right", kings, (-2.4, 16.6), (-7.0, 16.0), False, pale, green_blanket)
    return len(nativity.objects) + len(kings.objects)


print("figures:", build_figures())
