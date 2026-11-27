import os

MANGER_FOLDER = r"D:\code\DEMOS\lib\urban\manger"


def export_scene():
    glb_path = os.path.join(MANGER_FOLDER, "manger.glb")
    blend_path = os.path.join(MANGER_FOLDER, "manger.blend")
    bpy.ops.file.pack_all()
    bpy.ops.export_scene.gltf(filepath=glb_path, export_format="GLB", use_selection=False, export_apply=True,
                              export_lights=True, export_cameras=True, export_yup=True,
                              export_image_format="AUTO")
    bpy.ops.wm.save_as_mainfile(filepath=blend_path, copy=True)
    return {path: round(os.path.getsize(path) / 1_000_000, 1) for path in (glb_path, blend_path)}


print("exported MB:", export_scene())
