"""Convert the Survivor mod's dice.mesh (TTM1) to a Wavefront OBJ for Unreal import.

Usage: python convert_mesh.py <input.mesh> <output.obj> [target_size_uu]

TTM1 layout, little-endian: b"TTM1", int32 vertex count, int32 index count,
then positions (3f), normals (3f), UVs (2f) and int32 indices.

Unity is left-handed, so Z is negated and triangle winding is reversed.
The mesh is centred on its bounding box and scaled so its largest side equals
target_size_uu (default 30 Unreal units, about 30 cm).
"""
import struct
import sys
from pathlib import Path


def read_mesh(path):
    data = Path(path).read_bytes()
    if data[:4] != b"TTM1":
        raise ValueError("not a TTM1 mesh")
    nv, ni = struct.unpack_from("<ii", data, 4)
    offset = 12
    expected = offset + nv * 32 + ni * 4
    if len(data) != expected:
        raise ValueError(f"size mismatch: file {len(data)}, expected {expected}")
    if ni % 3:
        raise ValueError(f"index count {ni} is not divisible by 3")

    def take(fmt, count):
        nonlocal offset
        step = struct.calcsize(fmt)
        rows = [struct.unpack_from(fmt, data, offset + i * step) for i in range(count)]
        offset += step * count
        return rows

    positions = take("<3f", nv)
    normals = take("<3f", nv)
    uvs = take("<2f", nv)
    indices = [row[0] for row in take("<i", ni)]
    if indices and not 0 <= min(indices) <= max(indices) < nv:
        raise ValueError("index out of range")
    return positions, normals, uvs, indices


def main():
    if len(sys.argv) not in (3, 4):
        sys.exit(__doc__)
    target = float(sys.argv[3]) if len(sys.argv) == 4 else 30.0
    positions, normals, uvs, indices = read_mesh(sys.argv[1])

    lo = [min(p[a] for p in positions) for a in range(3)]
    hi = [max(p[a] for p in positions) for a in range(3)]
    size = [h - l for h, l in zip(hi, lo)]
    centre = [(h + l) / 2 for h, l in zip(hi, lo)]
    largest = max(size)
    if largest <= 0:
        sys.exit("mesh has no extent")
    scale = target / largest

    with open(sys.argv[2], "w", newline="\n") as f:
        f.write("# Lucky Dice mesh, converted by tools/convert_mesh.py\no Dice\n")
        for x, y, z in positions:
            f.write(f"v {(x - centre[0]) * scale:.6f} {(y - centre[1]) * scale:.6f} {-(z - centre[2]) * scale:.6f}\n")
        for u, v in uvs:
            f.write(f"vt {u:.6f} {v:.6f}\n")
        for x, y, z in normals:
            f.write(f"vn {x:.6f} {y:.6f} {-z:.6f}\n")
        for i in range(0, len(indices), 3):
            a, b, c = indices[i] + 1, indices[i + 2] + 1, indices[i + 1] + 1
            f.write(f"f {a}/{a}/{a} {b}/{b}/{b} {c}/{c}/{c}\n")

    print(f"verts {len(positions)}, tris {len(indices) // 3}")
    print(f"source size {size[0]:.4f} x {size[1]:.4f} x {size[2]:.4f}, scale {scale:.4f}")


if __name__ == "__main__":
    main()
