"""Prepare the source dice FBX for Unreal. Run with Blender:

blender --background --factory-startup --python prepare_dice.py -- <input.fbx> <output.fbx> [target_tris] [size_m] [preview_prefix] [texture.png]

Removes empty meshes, welds split vertices, reduces the triangle count,
centres the pivot, scales the largest side to size_m and exports an FBX with
applied transforms. UVs are kept, so the source textures still fit.
"""
import sys

import bmesh
import bpy
from mathutils import Vector


def tris(mesh):
    return sum(len(p.vertices) - 2 for p in mesh.polygons)


def bounds(mesh):
    lo = Vector(tuple(min(v.co[a] for v in mesh.vertices) for a in range(3)))
    hi = Vector(tuple(max(v.co[a] for v in mesh.vertices) for a in range(3)))
    return lo, hi


def render_previews(scene, obj, tex, prefix):
    mat = bpy.data.materials.new("preview")
    mat.use_nodes = True
    node = mat.node_tree.nodes.new("ShaderNodeTexImage")
    node.image = bpy.data.images.load(tex)
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    mat.node_tree.links.new(node.outputs["Color"], bsdf.inputs["Base Color"])
    saved = list(obj.data.materials)
    obj.data.materials.clear()
    obj.data.materials.append(mat)

    scene.render.engine = "BLENDER_WORKBENCH"
    scene.display.shading.light = "STUDIO"
    scene.display.shading.color_type = "TEXTURE"
    scene.render.resolution_x = scene.render.resolution_y = 600
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
    scene.collection.objects.link(cam)
    scene.camera = cam
    lo, hi = bounds(obj.data)
    span = max(hi - lo)
    cam.data.clip_start = span / 100
    cam.data.clip_end = span * 100
    for name, d in (("a", (1, -1, 0.8)), ("b", (-1, 1, -0.8))):
        cam.location = Vector(d).normalized() * span * 2.2
        cam.rotation_euler = (-cam.location).to_track_quat("-Z", "Y").to_euler()
        scene.render.filepath = f"{prefix}_{name}.png"
        bpy.ops.render.render(write_still=True)

    bpy.data.objects.remove(cam)
    obj.data.materials.clear()
    for m in saved:
        obj.data.materials.append(m)


def main():
    args = sys.argv[sys.argv.index("--") + 1:]
    src, dst = args[0], args[1]
    target = int(args[2]) if len(args) > 2 else 10000
    size_m = float(args[3]) if len(args) > 3 else 0.3
    prefix = args[4] if len(args) > 4 else None
    tex = args[5] if len(args) > 5 else None

    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=src)
    scene = bpy.context.scene

    for o in list(scene.objects):
        if o.type != "MESH" or not o.data.vertices:
            bpy.data.objects.remove(o)
    objs = list(scene.objects)
    if len(objs) != 1:
        sys.exit(f"expected one mesh, found {len(objs)}")
    obj = objs[0]
    obj.name = obj.data.name = "SM_Dice"
    me = obj.data
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    print(f"RESULT before: verts {len(me.vertices)}, tris {tris(me)}")

    lo, hi = bounds(me)
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=max(hi - lo) * 1e-5)
    bm.to_mesh(me)
    bm.free()
    print(f"RESULT welded: verts {len(me.vertices)}, tris {tris(me)}")

    if tris(me) > target:
        mod = obj.modifiers.new("reduce", "DECIMATE")
        mod.decimate_type = "COLLAPSE"
        mod.ratio = target / tris(me)
        bpy.ops.object.modifier_apply(modifier=mod.name)
    print(f"RESULT reduced: verts {len(me.vertices)}, tris {tris(me)}")

    lo, hi = bounds(me)
    centre = (lo + hi) / 2
    factor = size_m / max(hi - lo)
    for v in me.vertices:
        v.co = (v.co - centre) * factor
    me.update()

    lo, hi = bounds(me)
    print("RESULT size m", tuple(round(a, 4) for a in hi - lo), "centre", tuple(round(a, 5) for a in (lo + hi) / 2))
    print(f"RESULT materials {[m.name for m in me.materials]}, uv_layers {[u.name for u in me.uv_layers]}")

    if prefix and tex:
        render_previews(scene, obj, tex, prefix)

    bpy.ops.export_scene.fbx(
        filepath=dst,
        use_selection=True,
        object_types={"MESH"},
        apply_scale_options="FBX_SCALE_ALL",
        mesh_smooth_type="FACE",
        use_mesh_modifiers=True,
        add_leaf_bones=False,
        bake_anim=False,
        path_mode="STRIP",
    )

    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=dst)
    back = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    print(f"RESULT reimport: objects {len(back)}, tris {tris(back[0].data)}, dimensions {tuple(round(a, 4) for a in back[0].dimensions)}, scale {tuple(round(a, 4) for a in back[0].scale)}")


main()
