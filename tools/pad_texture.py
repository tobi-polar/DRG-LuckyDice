"""Extend texture colours into transparent gaps and make the result opaque. Run with Blender:

blender --background --factory-startup --python pad_texture.py -- <input.png> <output.png> [pixels]

Without padding, the gaps between UV islands can bleed in as dark seams once
Unreal generates mipmaps.
"""
import sys

import bpy
import numpy as np


def main():
    args = sys.argv[sys.argv.index("--") + 1:]
    src, dst = args[0], args[1]
    passes = int(args[2]) if len(args) > 2 else 16

    img = bpy.data.images.load(src)
    img.colorspace_settings.name = "Non-Color"
    w, h = img.size
    px = np.empty(w * h * 4, dtype=np.float32)
    img.pixels.foreach_get(px)
    px = px.reshape(h, w, 4)
    rgb = px[..., :3].copy()
    filled = px[..., 3] > 0.5
    start = filled.mean()

    for _ in range(passes):
        total = np.zeros_like(rgb)
        count = np.zeros((h, w), dtype=np.float32)
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)):
            total += np.roll(rgb * filled[..., None], (dy, dx), axis=(0, 1))
            count += np.roll(filled, (dy, dx), axis=(0, 1))
        grow = ~filled & (count > 0)
        rgb[grow] = total[grow] / count[grow][..., None]
        filled = filled | grow

    # Whatever the padding didn't reach gets the average colour of the texture.
    rgb[~filled] = rgb[filled].mean(axis=0)

    out = np.dstack((rgb, np.ones((h, w), dtype=np.float32)))
    img.pixels.foreach_set(out.ravel())
    img.filepath_raw = dst
    img.file_format = "PNG"
    img.save()
    print(f"RESULT {dst}: {w}x{h}, opaque coverage {start:.1%} -> padded {filled.mean():.1%}")


main()
