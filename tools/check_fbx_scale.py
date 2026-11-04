"""Report the size an FBX should import at, read from the file's raw values.

Usage: python check_fbx_scale.py <file.fbx>

Size in Unreal units (cm) = vertex extent x Lcl Scaling x UnitScaleFactor.
Blender can't check this, because it undoes the same scaling when it reimports.
"""
import struct
import sys
import zlib
from pathlib import Path

ARRAYS = {b"f": "f", b"d": "d", b"i": "i", b"l": "q", b"b": "?", b"c": "B"}
SCALARS = {b"Y": "h", b"C": "?", b"I": "i", b"F": "f", b"D": "d", b"L": "q"}


def read_props(data, pos, count):
    props = []
    for _ in range(count):
        kind = data[pos:pos + 1]
        pos += 1
        if kind in SCALARS:
            fmt = "<" + SCALARS[kind]
            props.append(struct.unpack_from(fmt, data, pos)[0])
            pos += struct.calcsize(fmt)
        elif kind in ARRAYS:
            length, encoding, size = struct.unpack_from("<III", data, pos)
            pos += 12
            raw = data[pos:pos + size]
            pos += size
            if encoding == 1:
                raw = zlib.decompress(raw)
            props.append(struct.unpack(f"<{length}{ARRAYS[kind]}", raw))
        elif kind in (b"S", b"R"):
            size = struct.unpack_from("<I", data, pos)[0]
            pos += 4
            props.append(data[pos:pos + size])
            pos += size
        else:
            raise ValueError(f"unknown property type {kind!r} at {pos}")
    return props, pos


def read_nodes(data, pos, end, wide):
    head = "<QQQB" if wide else "<IIIB"
    head_size = struct.calcsize(head)
    nodes = []
    while pos < end:
        node_end, count, _, name_len = struct.unpack_from(head, data, pos)
        pos += head_size
        if node_end == 0:
            break
        name = data[pos:pos + name_len].decode()
        pos += name_len
        props, pos = read_props(data, pos, count)
        children = read_nodes(data, pos, node_end, wide) if pos < node_end else []
        nodes.append((name, props, children))
        pos = node_end
    return nodes


def walk(nodes, path=()):
    for name, props, children in nodes:
        yield path + (name,), props
        yield from walk(children, path + (name,))


def main():
    data = Path(sys.argv[1]).read_bytes()
    if not data.startswith(b"Kaydara FBX Binary"):
        sys.exit("not a binary FBX")
    version = struct.unpack_from("<I", data, 23)[0]
    nodes = read_nodes(data, 27, len(data), version >= 7500)

    unit = 1.0
    scales = []
    extents = []
    tris = 0
    for path, props in walk(nodes):
        if path[-1] == "P" and props and props[0] == b"UnitScaleFactor":
            unit = props[-1]
        elif path[-1] == "P" and props and props[0] == b"Lcl Scaling" and "Objects" in path:
            scales.append(tuple(props[-3:]))
        elif path[-1] == "Vertices" and "Geometry" in path:
            v = props[0]
            extents.append(tuple(max(v[a::3]) - min(v[a::3]) for a in range(3)))
        elif path[-1] == "PolygonVertexIndex" and "Geometry" in path:
            tris += sum(1 for i in props[0] if i < 0)

    print(f"version {version}, UnitScaleFactor {unit}, Lcl Scaling {scales or 'default (1, 1, 1)'}, polygons {tris}")
    scale = scales[0] if scales else (1.0, 1.0, 1.0)
    for e in extents:
        print("vertex extent", tuple(round(x, 4) for x in e))
        print("expected Unreal size (uu)", tuple(round(x * s * unit, 3) for x, s in zip(e, scale)))


main()
