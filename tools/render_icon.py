"""Render a transparent dice icon. Run with Blender:

blender --background --factory-startup --python render_icon.py -- <dice.fbx> <texture.png> <output.png> [size]
"""
import sys

import bpy
from mathutils import Vector


def main():
    args = sys.argv[sys.argv.index("--") + 1:]
    fbx, tex, out = args[0], args[1], args[2]
    size = int(args[3]) if len(args) > 3 else 256

    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=fbx)
    scene = bpy.context.scene
    obj = next(o for o in scene.objects if o.type == "MESH")

    mat = bpy.data.materials.new("icon")
    mat.use_nodes = True
    node = mat.node_tree.nodes.new("ShaderNodeTexImage")
    node.image = bpy.data.images.load(tex)
    mat.node_tree.links.new(node.outputs["Color"], mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"])
    obj.data.materials.clear()
    obj.data.materials.append(mat)

    corners = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
    centre = sum(corners, Vector()) / 8
    span = max((a - centre).length for a in corners) * 2

    scene.render.engine = "BLENDER_WORKBENCH"
    scene.display.shading.light = "STUDIO"
    scene.display.shading.color_type = "TEXTURE"
    scene.render.film_transparent = True
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.resolution_x = scene.render.resolution_y = size
    scene.render.filepath = out

    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
    scene.collection.objects.link(cam)
    scene.camera = cam
    cam.data.type = "ORTHO"
    cam.data.ortho_scale = span * 1.02
    cam.data.clip_start = span / 100
    cam.data.clip_end = span * 100
    cam.location = centre + Vector((1, -1, 0.8)).normalized() * span * 3
    cam.rotation_euler = (centre - cam.location).to_track_quat("-Z", "Y").to_euler()
    bpy.ops.render.render(write_still=True)
    print("RESULT rendered", out)


main()
