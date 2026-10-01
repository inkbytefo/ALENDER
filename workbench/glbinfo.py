"""
Engine-independent structural check of a .glb (pure python): what a game engine will receive.

    info = glbinfo.read("output/A/glb/A_LOD0.glb")
    info -> {bytes, nodes, meshes, primitives, materials, textures, images: [(name, w, h)],
             tris, animations, skins, node_names}
"""
import json
import os
import struct


def _png_size(data):
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return struct.unpack(">II", data[16:24])
    return None


def _jpg_size(data):
    i = 2
    while i < len(data) - 9:
        if data[i] != 0xFF:
            i += 1
            continue
        marker = data[i + 1]
        if marker in (0xC0, 0xC1, 0xC2):
            h, w = struct.unpack(">HH", data[i + 5:i + 9])
            return w, h
        i += 2 + struct.unpack(">H", data[i + 2:i + 4])[0]
    return None


def read(path):
    with open(path, "rb") as f:
        blob = f.read()
    magic, version, length = struct.unpack("<III", blob[:12])
    if magic != 0x46546C67:
        raise ValueError(f"not a GLB file: {path}")
    off, js, binchunk = 12, None, b""
    while off < length:
        clen, ctype = struct.unpack("<II", blob[off:off + 8])
        chunk = blob[off + 8:off + 8 + clen]
        if ctype == 0x4E4F534A:
            js = json.loads(chunk.decode("utf-8"))
        elif ctype == 0x004E4942:
            binchunk = chunk
        off += 8 + clen
    js = js or {}
    acc = js.get("accessors", [])
    tris = 0
    prims = 0
    for m in js.get("meshes", []):
        for p in m.get("primitives", []):
            prims += 1
            if p.get("mode", 4) != 4:
                continue
            if "indices" in p:
                tris += acc[p["indices"]]["count"] // 3
            else:
                tris += acc[p["attributes"]["POSITION"]]["count"] // 3
    images = []
    views = js.get("bufferViews", [])
    for im in js.get("images", []):
        size = None
        if "bufferView" in im:
            bv = views[im["bufferView"]]
            data = binchunk[bv.get("byteOffset", 0):bv.get("byteOffset", 0) + bv["byteLength"]]
            size = _png_size(data) or _jpg_size(data)
        images.append((im.get("name", ""), *(size or (0, 0))))
    return dict(bytes=os.path.getsize(path), nodes=len(js.get("nodes", [])), meshes=len(js.get("meshes", [])),
                primitives=prims, materials=len(js.get("materials", [])), textures=len(js.get("textures", [])),
                images=images, tris=tris, animations=len(js.get("animations", [])), skins=len(js.get("skins", [])),
                node_names=[n.get("name", "") for n in js.get("nodes", [])])
