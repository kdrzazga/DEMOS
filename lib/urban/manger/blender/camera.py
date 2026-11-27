def build_camera():
    collection = bpy.data.collections.get("Views") or fresh_collection("Views")
    camera = bpy.data.objects.get("painting_view")
    if not camera:
        camera = bpy.data.objects.new("painting_view", bpy.data.cameras.new("painting_view"))
        collection.objects.link(camera)
    camera.location = (-0.1, -0.3, 1.35)
    target = Vector((1.2, 6.0, 1.15))
    camera.rotation_euler = (target - camera.location).to_track_quat("-Z", "Y").to_euler()
    camera.data.lens = 22
    camera.data.clip_end = 1000.0
    scene = bpy.context.scene
    scene.camera = camera
    scene.render.resolution_x = 1920
    scene.render.resolution_y = 1080
    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
            if area.type == "VIEW_3D":
                for space in area.spaces:
                    if space.type == "VIEW_3D":
                        space.shading.type = "MATERIAL"
                        space.clip_end = 1000.0
                        space.region_3d.view_perspective = "CAMERA"


build_camera()
